import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import json
import os
import logging

logger = logging.getLogger(__name__)

_app = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK once.

    Supports two modes:
    1. FIREBASE_CREDENTIALS_JSON env var (for containers / ECS)
    2. Local JSON file (for local development)
    """
    global _app
    if _app is not None:
        return

    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
        logger.info("Firebase credentials loaded from environment variable.")
    else:
        key_path = Path(__file__).resolve().parent.parent / "printing-test-61b1b-firebase-adminsdk-fbsvc-cd1a2f3bdf.json"
        if not key_path.exists():
            raise FileNotFoundError(
                f"Firebase service account key not found at {key_path}. "
                "Set FIREBASE_CREDENTIALS_JSON env var or place the key file in the project root."
            )
        cred = credentials.Certificate(str(key_path))
        logger.info("Firebase credentials loaded from local file.")

    _app = firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully.")


def send_push_notification(device_token: str, order_data: dict) -> str:
    """Send a data-only FCM message to the given device token."""
    message = messaging.Message(
        token=device_token,
        data={
            "order_json": json.dumps(order_data),
        },
    )

    response = messaging.send(message)
    logger.info("FCM message sent successfully. Message ID: %s", response)
    return response
