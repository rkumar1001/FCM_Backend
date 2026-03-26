import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_app = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK once using local service account key."""
    global _app
    if _app is not None:
        return

    key_path = Path(__file__).resolve().parent.parent / "printing-test-61b1b-firebase-adminsdk-fbsvc-cd1a2f3bdf.json"
    if not key_path.exists():
        raise FileNotFoundError(
            f"Firebase service account key not found at {key_path}. "
            "Place your serviceAccountKey.json in the project root."
        )

    cred = credentials.Certificate(str(key_path))
    _app = firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully.")


def send_push_notification(device_token: str, order_data: dict) -> str:
    """
    Send a data-only FCM message to the given device token.

    Returns the message ID on success, raises on failure.
    """
    import json

    message = messaging.Message(
        token=device_token,
        data={
            "order_json": json.dumps(order_data),
        },
    )

    response = messaging.send(message)
    logger.info("FCM message sent successfully. Message ID: %s", response)
    return response
