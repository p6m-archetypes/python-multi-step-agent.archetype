import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CHAINLIT_AUTH_SECRET = os.environ.get("CHAINLIT_AUTH_SECRET")


def create_jwt(identifier: str, metadata: dict) -> str:
    """
    Create a JSON Web Token (JWT) with the given identifier and metadata.

    Args:
        identifier (str): The unique identifier to include in the token.
        metadata (dict): Additional metadata to include in the token.

    Returns:
        str: The encoded JWT as a string.
    """
    to_encode = {
        "identifier": identifier,
        "metadata": metadata,
        "exp": datetime.utcnow() + timedelta(minutes=60 * 24 * 15),  # 15 days
    }

    encoded_jwt = jwt.encode(to_encode, CHAINLIT_AUTH_SECRET, algorithm="HS256")
    return encoded_jwt


# This is required to make the copilot example work
# This is required to make the copilot example work
# This is required to make the copilot example work

access_token = create_jwt("user-1", {"name": "John Doe"})
print(access_token)
