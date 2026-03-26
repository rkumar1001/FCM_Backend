"""Centralised configuration — loads from environment / .env."""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
PORT: int = int(os.getenv("PORT", "8000"))

# ---------------------------------------------------------------------------
# FCM target device
# ---------------------------------------------------------------------------
DEVICE_TOKEN: str = os.getenv("DEVICE_TOKEN", "")

# ---------------------------------------------------------------------------
# Restaurant constants (override via .env if needed)
# ---------------------------------------------------------------------------
RESTAURANT_NAME: str = os.getenv("RESTAURANT_NAME", "The Masala Twist")
RESTAURANT_PHONE: str = os.getenv("RESTAURANT_PHONE", "805-832-4945")
RESTAURANT_ADDRESS: str = os.getenv(
    "RESTAURANT_ADDRESS",
    "2810 South Harbor Blvd, Suite B1, Oxnard, CA",
)
ORDER_TYPE: str = os.getenv("ORDER_TYPE", "Pickup")
