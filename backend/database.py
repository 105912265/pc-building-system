"""MySQL connection settings. Store credentials in the repository-root .env file."""

import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Open a new connection to the existing Phase 3 MySQL database."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3307")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "lazar$123"),
        database=os.getenv("DB_NAME", "pc_building_system"),
        connection_timeout=5,
    )
