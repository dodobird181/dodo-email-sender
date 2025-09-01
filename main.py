import hashlib
import hmac
import time
from typing import Any, Dict

import flask

from config import load_config
from email_sender import EmailSender
from logger import logger_from_config
from utils import request_to_sanitized_json

app = flask.Flask(__name__)
email_sender = EmailSender()
config = load_config()
logger = logger_from_config(config)


# Custom error handler for all HTTP exceptions.
@app.errorhandler(Exception)
def handle_exception(e):
    """
    Transform all exceptions from 'flask.abort' to JSON error responses.
    """
    # If it's an HTTPException, use its code; otherwise 500
    code = getattr(e, "code", 500)
    return flask.jsonify(error=str(e), code=code), code


def _abort_if_payload_too_large() -> None:
    """
    Abort request if the content is too large.
    """
    max_bytes = config.max_email_payload_bytes
    content_length = flask.request.content_length if flask.request.content_length else 0
    if content_length > max_bytes:
        logger.warning(
            "Rejected request with payload = {} KB > {} KB: {}.".format(
                content_length / 1000,
                max_bytes / 1000,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(413, description="Payload too large.")


def _abort_if_invalid_signature() -> None:
    """
    Abort if the request is missing auth headers, it's timestamp is too old, or it has an invalid signature.
    """
    signature = flask.request.headers.get("X-Signature")
    timestamp = flask.request.headers.get("X-Timestamp")
    body = flask.request.get_data(as_text=True)

    if not signature or not timestamp:
        logger.warning(
            "Rejected request because it was missing 'X-Signature': '{}', or 'X-Timestamp': '{}'. Request: {}".format(
                signature,
                timestamp,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Missing auth header(s). Make sure you're sending 'X-Signature' and 'X-Timestamp'.")

    # Check timestamp is from the last 5 minutes
    if abs(time.time() - int(timestamp)) > 300:
        logger.warning(
            "Rejected request with timestamp '{}' because it's too old. Request: {}.".format(
                timestamp,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Too old.")

    # Compute the expected request signature and compare
    message = timestamp + body
    secret_bytes = config.api_secret.encode("utf-8")
    expected_sig = hmac.new(secret_bytes, message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        logger.warning(
            "Rejected request with invalid signature. Request: {}.".format(
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(403, "Invalid Signature.")


def _require_arg(argname: str, data: Dict[str, Any]) -> None:
    if argname not in data:
        logger.warning(
            "Rejected request with missing argument '{}'. Request: {}.".format(
                argname,
                request_to_sanitized_json(flask.request),
            )
        )
        flask.abort(400, f"Missing required argument '{argname}'.")


@app.route("/", methods=["GET"])
def index():
    return flask.Response("Dodo Email Sender v1.0.", status=200)


@app.route("/send", methods=["POST"])
def send():

    _abort_if_payload_too_large()
    _abort_if_invalid_signature()

    data = flask.request.get_json()
    _require_arg("recipients", data)
    _require_arg("subject", data)
    _require_arg("body", data)

    try:
        email_sender.send(
            sender=config.sender,
            recipients=data["recipients"],
            subject=data["subject"],
            body=data["body"],
        )
        return flask.jsonify({"message": "Email sent!"}), 200

    except EmailSender.SendError as e:
        log = logger.error if e.status_code >= 500 else logger.warning
        log("Failed to send email.", exc_info=e)
        flask.abort(e.status_code, e.message)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
