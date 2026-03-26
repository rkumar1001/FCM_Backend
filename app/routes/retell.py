"""Retell AI webhook route — receives order data and dispatches FCM push."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models import RetellWebhookPayload
from app.services import build_normalized_order, dispatch_order_notification
from app.database import save_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/retell", tags=["retell"])


@router.post("/order")
async def retell_order_webhook(payload: RetellWebhookPayload, request: Request):
    client = request.client.host if request.client else "unknown"
    logger.info(
        "Incoming Retell webhook from %s (call_id=%s, tool=%s)",
        client, payload.call.call_id, payload.name,
    )

    # --- Normalize ----------------------------------------------------------
    order = build_normalized_order(payload)
    logger.info(
        "Normalized order built — confirmation=%s, job_id=%s, items=%d",
        order.confirmation_number, order.job_id, len(order.items),
    )

    # --- Persist to DB ------------------------------------------------------
    save_order(order)

    # --- Send FCM -----------------------------------------------------------
    try:
        message_id = dispatch_order_notification(order)
        logger.info(
            "FCM push sent — confirmation=%s, messageId=%s",
            order.confirmation_number, message_id,
        )
        return {
            "status": "sent",
            "confirmation_number": order.confirmation_number,
            "job_id": order.job_id,
        }

    except Exception as exc:
        logger.exception("FCM push failed for job_id=%s: %s", order.job_id, exc)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "job_id": order.job_id, "error": str(exc)},
        )
