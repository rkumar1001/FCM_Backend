"""Pydantic models for the Retell AI webhook and internal order representation."""

from pydantic import BaseModel, Field
from typing import Any


# ---------------------------------------------------------------------------
# Retell webhook incoming payload (actual structure from RetellAI)
# ---------------------------------------------------------------------------
class RetellCallInfo(BaseModel):
    call_id: str
    from_number: str = ""
    to_number: str = ""
    call_status: str = ""
    # Accept any other fields Retell sends without breaking validation
    model_config = {"extra": "allow"}


class RetellArgs(BaseModel):
    phone_number: str = ""
    customer_name: str
    pickup_time: str = ""
    order_items_json: str | list = "[]"
    order_summary: str = ""
    # Accept any extra args
    model_config = {"extra": "allow"}


class RetellWebhookPayload(BaseModel):
    call: RetellCallInfo
    name: str = ""
    args: RetellArgs


# ---------------------------------------------------------------------------
# Parsed order item
# ---------------------------------------------------------------------------
class OrderItem(BaseModel):
    quantity: int = 1
    name: str
    spice_level: int | None = None
    original_name: str = ""
    matched: bool = True
    confidence: float = 1.0
    modifiers: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Normalized internal order object
# ---------------------------------------------------------------------------
class NormalizedOrder(BaseModel):
    job_id: str
    confirmation_number: str = ""
    order_date: str
    customer_name: str
    phone_number: str
    ready_time: str
    order_items_raw: str
    subtotal: str
    tax: str
    total: str
    status: str
    restaurant_name: str
    restaurant_phone: str
    restaurant_address: str
    order_type: str
    items: list[OrderItem]


# ---------------------------------------------------------------------------
# Legacy n8n endpoint model (kept for backward compatibility)
# ---------------------------------------------------------------------------
class LegacySendOrderRequest(BaseModel):
    secret: str
    deviceToken: str = Field(..., min_length=1)
    orderData: Any = {}
