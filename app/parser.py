"""Utility to parse order items from RetellAI's formats."""

import json
import re
from app.models import OrderItem

# Matches an optional leading integer quantity followed by the item name.
_QTY_RE = re.compile(r"^(\d+)\s+(.+)$")


def parse_order_items_json(raw_json: str | list) -> list[OrderItem]:
    """
    Parse order items from either a JSON-encoded string or a list of dicts.
    """
    if isinstance(raw_json, list):
        items_list = raw_json
    else:
        try:
            items_list = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            return []

    items: list[OrderItem] = []
    for entry in items_list:
        if not isinstance(entry, dict):
            continue
        name = entry.get("item_name") or entry.get("name", "Unknown item")
        qty = int(entry.get("quantity", 1))
        spice = entry.get("spice_level")
        spice_level = int(spice) if spice is not None else None

        # Capture every other key as a modifier (e.g. modifications, special_instructions)
        _skip = {"item_name", "name", "quantity", "spice_level"}
        mods = {k: v for k, v in entry.items() if k not in _skip and v}

        items.append(OrderItem(quantity=qty, name=name, spice_level=spice_level, modifiers=mods))

    return items


def parse_order_items_text(raw: str) -> list[OrderItem]:
    """
    Fallback parser for pipe/comma/semicolon-delimited strings like:
      "2 chicken biryani | 1 garlic naan | 1 mango lassi"
      "1 Lamb Sherry Korma, spice level 1; 1 Gulab Jamun"
    """
    segments = re.split(r"\s*[|,;]\s*", raw.strip())
    items: list[OrderItem] = []

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        match = _QTY_RE.match(segment)
        if match:
            qty = int(match.group(1))
            name = match.group(2).strip()
        else:
            qty = 1
            name = segment

        items.append(OrderItem(quantity=qty, name=name))

    return items
