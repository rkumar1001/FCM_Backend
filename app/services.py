"""Order service — normalizes webhook payloads and dispatches FCM notifications."""

import json
import logging
import random
import string
from datetime import datetime, timezone

from app.models import RetellWebhookPayload, NormalizedOrder, OrderItem
from app.parser import parse_order_items_json, parse_order_items_text
from app.menu import match_menu_item
from app.config import (
    RESTAURANT_NAME,
    RESTAURANT_PHONE,
    RESTAURANT_ADDRESS,
    ORDER_TYPE,
    DEVICE_TOKEN,
)
from app.firebase_config import send_push_notification

logger = logging.getLogger(__name__)


def _validate_items_against_menu(items: list[OrderItem]) -> list[OrderItem]:
    """
    Validate each item against the restaurant menu.
    - If exact/fuzzy match found → replace name with canonical menu name.
    - If no match → keep original name, set matched=False and mark as needs review.
    """
    validated: list[OrderItem] = []

    for item in items:
        matched_name, confidence = match_menu_item(item.name)

        if matched_name:
            logger.info(
                "Menu match: '%s' → '%s' (confidence=%.2f)",
                item.name, matched_name, confidence,
            )
            validated.append(item.model_copy(update={
                "original_name": item.name,
                "name": matched_name,
                "matched": True,
                "confidence": round(confidence, 2),
            }))
        else:
            logger.warning(
                "No menu match for '%s' (best=%.2f) — marked as NEEDS REVIEW",
                item.name, confidence,
            )
            validated.append(item.model_copy(update={
                "original_name": item.name,
                "name": f"[NEEDS REVIEW] {item.name}",
                "matched": False,
                "confidence": round(confidence, 2),
            }))

    return validated


def _generate_confirmation_number() -> str:
    """Generate a short human-friendly confirmation number like MT-4829."""
    digits = "".join(random.choices(string.digits, k=4))
    return f"MT-{digits}"


def build_normalized_order(payload: RetellWebhookPayload) -> NormalizedOrder:
    """Convert a raw Retell webhook payload into a normalized internal order."""
    args = payload.args
    call = payload.call
    confirmation_number = _generate_confirmation_number()

    # Parse items — prefer structured JSON, fall back to text summary
    items = parse_order_items_json(args.order_items_json)
    if not items and args.order_summary:
        items = parse_order_items_text(args.order_summary)
    logger.info("Parsed %d item(s) from order data.", len(items))

    # Validate items against the restaurant menu
    items = _validate_items_against_menu(items)
    unmatched = [i for i in items if not i.matched]
    if unmatched:
        logger.warning(
            "%d item(s) not found on menu: %s",
            len(unmatched),
            [i.original_name for i in unmatched],
        )

    # Use order_summary as the raw representation for readability
    raw_text = args.order_summary or (
        json.dumps(args.order_items_json) if isinstance(args.order_items_json, list) else args.order_items_json
    )

    return NormalizedOrder(
        job_id=call.call_id,
        confirmation_number=confirmation_number,
        order_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        customer_name=args.customer_name,
        phone_number=args.phone_number or call.from_number,
        ready_time=args.pickup_time,
        order_items_raw=raw_text,
        subtotal="0.00",
        tax="0.00",
        total="0.00",
        status="confirmed",
        restaurant_name=RESTAURANT_NAME,
        restaurant_phone=RESTAURANT_PHONE,
        restaurant_address=RESTAURANT_ADDRESS,
        order_type=ORDER_TYPE,
        items=items,
    )


def dispatch_order_notification(order: NormalizedOrder) -> str:
    """Send the normalized order as a data-only FCM push. Returns the message ID."""
    if not DEVICE_TOKEN:
        raise RuntimeError(
            "DEVICE_TOKEN is not configured in .env — cannot send push notification."
        )

    message_id = send_push_notification(
        device_token=DEVICE_TOKEN,
        order_data=order.model_dump(),
    )
    return message_id
