"""Read saved/estimated component prices from MySQL (no external API)."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from backend.database import get_db_connection

router = APIRouter(tags=["Component prices"])


def _parse_json(value):
    if not value:
        return {}
    return json.loads(value) if isinstance(value, str) else value


@router.get("/components/{component_id}/price")
def read_component_price(component_id: int):
    """Public, read-only price information from the existing component table."""
    db = get_db_connection()
    cur = None
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT component_id, manufacturer, model, price, specifications "
            "FROM component WHERE component_id=%s", (component_id,)
        )
        item = cur.fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Component not found")

        specs = _parse_json(item["specifications"])
        metadata = specs.get("price_metadata") or {}
        return {
            "component_id": item["component_id"],
            "manufacturer": item["manufacturer"],
            "model": item["model"],
            "price_aud": float(item["price"]) if item["price"] is not None else None,
            "price_type": metadata.get("type") or "existing_database_price",
            "last_checked_at": metadata.get("checked_at"),
            "source_url": metadata.get("source_url"),
            "seller": metadata.get("seller"),
            "condition": metadata.get("condition"),
            "disclaimer": "Estimated prices are for educational demonstration and may not reflect current retailer prices.",
        }
    finally:
        if cur is not None:
            cur.close()
        db.close()
