# email_server.py
import os
import smtplib
from email.mime.text import MIMEText

import flask
import itsdangerous as danger
from decouple import config

app = flask.Flask(__name__)

SECRET_TOKEN = config("DODO_EMAIL_SENDER_SECRET", cast=str)
SMTP_HOST = config("SMTP_HOST", cast=str)
SMTP_PORT = config("SMTP_PORT", cast=int)
EMAIL_ADDRESS = config("EMAIL_ADDRESS", cast=str)
EMAIL_PASSWORD = config("EMAIL_PASSWORD", cast=str)
MAX_EMAIL_REQUEST_BYTES = config("MAX_EMAIL_REQUEST_BYTES", cast=int)


@app.route("/", methods=["GET"])
def index():
    return flask.Response("Dodo Email Sender v1.0.", status=200)


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    # TODO: Check connection to Protonmail Bridge and return 200 OK.
    return flask.Response("OK", status=200)


@app.route("/send_email", methods=["POST"])
def send():

    if (length := flask.request.content_length) and length > MAX_EMAIL_REQUEST_BYTES:
        # reject bigger than 64KB for memory safety
        flask.abort(413, description="Payload too large.")

    data = flask.request.get_data()
    signer = danger.TimestampSigner(SECRET_TOKEN)

    try:
        # make sure signature is valid
        signer.unsign(flask.request.get_data(), max_age=60)
    except danger.BadSignature:
        flask.abort(403, description="Not allowed.")

    data = flask.request.get_json()
    try:
        # parse required fields
        subject = data["subject"]
        body = data["body"]
        to_email = data["to_email"]
    except KeyError:
        flask.abort(
            400, description="Required fields are 'subject', 'body', and 'to_email'."
        )

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "your@protonmail.com"
        msg["To"] = to_email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
        return flask.jsonify({"status": "sent"})
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
