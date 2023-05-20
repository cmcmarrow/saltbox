from typing import Dict

SALT_PYTHON_VERSION: Dict[str, str] = {"3006": "3.9",
                                       "3005": "3.9",
                                       "3004": "3.9",
                                       "3003": "3.8",
                                       "3002": "3.7",
                                       "3001": "3.7",
                                       "2019": "3.6"}


def get_salt_python_version(salt: str) -> str:
    salt = salt.split(".")[0]
    return SALT_PYTHON_VERSION.get(salt, "3.9")
