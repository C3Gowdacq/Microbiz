"""
backend/app/migrate.py

Safe schema migration script for MicroBizAI.
Adds new columns to existing tables WITHOUT dropping data.
Creates all new tables defined in models.py.

Run once after Phase 1 model changes:
    python -m backend.app.migrate

Uses SQLite PRAGMA table_info to detect existing columns before altering.
"""

import sqlite3
import os
import sys

# Ensure the project root is in path for model imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import engine, Base

# Import all models so Base.metadata is populated
from backend.app import models  # noqa: F401


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Return True if `column` already exists in `table`."""
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    """Return True if `table` exists in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def run_migration():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "microbizai.db"))
    print(f"[migrate] Target database: {db_path}")

    # Step 1: Create all new tables (safe — only creates missing ones)
    print("[migrate] Creating any missing tables via SQLAlchemy create_all...")
    Base.metadata.create_all(bind=engine)
    print("[migrate] Table creation complete.")

    # Step 2: Add missing columns to existing tables via raw SQLite ALTER TABLE
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ── business_settings: new operational threshold columns (Phase 1) ──────
    new_settings_cols = [
        ("safety_stock_days",             "INTEGER DEFAULT 3"),
        ("review_period_days",            "INTEGER DEFAULT 7"),
        ("khata_overdue_days",            "INTEGER DEFAULT 30"),
        ("expense_anomaly_threshold_pct", "REAL DEFAULT 30.0"),
        ("high_risk_multiplier",          "REAL DEFAULT 1.0"),
        ("medium_risk_multiplier",        "REAL DEFAULT 1.5"),
        ("autonomous_mode",               "INTEGER DEFAULT 0"),  # SQLite stores bool as int
    ]
    for col_name, col_def in new_settings_cols:
        if not column_exists(cursor, "business_settings", col_name):
            print(f"[migrate] Adding column business_settings.{col_name} ...")
            cursor.execute(f"ALTER TABLE business_settings ADD COLUMN {col_name} {col_def}")
            print(f"[migrate]   + Added {col_name}")
        else:
            print(f"[migrate]   . {col_name} already exists, skipping.")

    # __ recommendations: new entity context columns (Phase 1) ________________
    new_rec_cols = [
        ("module",            "TEXT"),
        ("entity_type",       "TEXT"),
        ("entity_id",         "TEXT"),
        ("purchase_order_id", "INTEGER"),
    ]
    for col_name, col_def in new_rec_cols:
        if not column_exists(cursor, "recommendations", col_name):
            print(f"[migrate] Adding column recommendations.{col_name} ...")
            cursor.execute(f"ALTER TABLE recommendations ADD COLUMN {col_name} {col_def}")
            print(f"[migrate]   + Added {col_name}")
        else:
            print(f"[migrate]   . recommendations.{col_name} already exists, skipping.")

    # __ products: inventory_events relationship (no new columns needed) _______
    # The relationship is handled by the new inventory_events table FK

    conn.commit()
    conn.close()

    print("\n[migrate] Migration complete. All tables and columns are up to date.")
    print("[migrate] Existing data has been preserved.")


if __name__ == "__main__":
    run_migration()
