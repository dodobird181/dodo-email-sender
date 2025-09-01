from typing import List

import boto3
from botocore.exceptions import ClientError


class EmailSender:

    class SendError(Exception):

        def __init__(self, status_code: int, message: str):
            self.status_code = status_code
            self.message = message
            super().__init__(
                {
                    "status_code": self.status_code,
                    "message": message,
                }
            )

    class AWSClientError(SendError):
        """
        There was an error sending an email.
        """

        ...

    class UnexpectedError(SendError):
        """
        Something unexpected happened while trying to send an email!
        """

        ...

    def __init__(self):
        self._ses = boto3.client("ses", region_name="us-east-1")

    def send(self, sender: str, recipients: List[str], subject: str, body: str) -> str:
        try:
            response = self._ses.send_email(
                Source=sender,
                Destination={"ToAddresses": recipients},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {
                        "Text": {"Data": body},
                        # "Html": {"Data": "<h1>Hello from SES</h1><p>This is a test.</p>"},
                    },
                },
            )
            return str(response["MessageId"])
        except ClientError as e:
            if "email address is not verified" in repr(e).lower():
                # Lower error severity for known bad requests from the client
                raise EmailSender.AWSClientError(400, message=repr(e)) from e
            raise EmailSender.AWSClientError(500, message=repr(e)) from e
        except Exception as e:
            raise EmailSender.UnexpectedError(500, message=repr(e)) from e
