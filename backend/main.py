"""Phase 5 PC Builder API — first milestone: read the existing component catalogue."""

import json
import logging

import mysql.connector
from fastapi import FastAPI, HTTPException, Query

from backend.database import get_db_connection

logger = logging.getLogger(__name__)
app = FastAPI(title="PC Builder API", version="0.1.0")


@app.get("/")
def home():
    return {"message": "PC Builder backend is running"}


@app.get("/health/db")
def database_health():
    """Confirm MySQL connectivity and report the existing component count."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM component")
        component_count = cursor.fetchone()[0]
        return {"database": "connected", "component_count": component_count}
    except mysql.connector.Error:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database connection failed")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.get("/components")
def list_components(
    category: str | None = None,
    manufacturer: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
):
    """Retrieve real MySQL records; allow basic filters from the Balsamiq designs."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot exceed max_price")

    conditions = []
    parameters = []
    if category:
        conditions.append("category = %s")
        parameters.append(category)
    if manufacturer:
        conditions.append("manufacturer = %s")
        parameters.append(manufacturer)
    if min_price is not None:
        conditions.append("price >= %s")
        parameters.append(min_price)
    if max_price is not None:
        conditions.append("price <= %s")
        parameters.append(max_price)

    query = (
        "SELECT component_id, category, manufacturer, model, price, "
        "release_date, specifications FROM component"
    )
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY category, price, model"

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, tuple(parameters))
        components = cursor.fetchall()
        for component in components:
            component["price"] = (float(component["price"])if component["price"] is not None else None)
            specs = component["specifications"]
            if isinstance(specs, str):
                component["specifications"] = json.loads(specs)
        return {"count": len(components), "components": components}
    except mysql.connector.Error:
        logger.exception("Could not retrieve components from MySQL")
        raise HTTPException(status_code=503, detail="Database query failed")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
