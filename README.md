# Dodo Email Sender
A simple email sender API that integrates with Amazon SES. This app listens for incoming requests at `/send` and sends emails if they contain a valid signature and the required parameters: `{sender, recipients, subject, body}`.

## Installation
Before installing, please make sure you have Python >= 3.10, and [Poetry](https://python-poetry.org/docs/#installing-with-pipx) installed.
1. Download and install the [AWS CLI tool](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
2. Run `aws configure` and enter your Access Key ID and Access Key Secret.
3. Run `poetry install` to create a new python virtual environment and install the required python dependencies.
3. **That's it!** The app can now be run in development mode using `poetry run python main.py`. Once the app has started, you can send test emails by editing and running `test_send_valid_sig.sh`.
