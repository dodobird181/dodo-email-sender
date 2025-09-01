import json
import subprocess
from dataclasses import dataclass


@dataclass
class Config:
    """
    Python representation of the config file.
    """

    class InvalidConfig(Exception):
        """The config contains some invalid formatting or data."""

        ...

    logdir: str
    max_email_payload_bytes: int
    api_secret: str
    sender: str


def load_config(config_path="config.yaml") -> Config:
    try:
        result = subprocess.run(["yq", "-e", "-o=json", ".", config_path], capture_output=True)
        data = json.loads(result.stdout)["config"]
        return Config(
            logdir=data["logs"]["dir"],
            max_email_payload_bytes=data["security"]["max_email_payload_bytes"],
            api_secret=data["security"]["api_secret"],
            sender=data["email"]["sender"],
        )
    except (KeyError, ValueError) as e:
        raise Config.InvalidConfig from e
