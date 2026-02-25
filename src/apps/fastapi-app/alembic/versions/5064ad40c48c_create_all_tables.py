"""create_all_tables

Revision ID: 5064ad40c48c
Revises: bb5377a56585
Create Date: 2026-02-23 14:30:00.000000

Neon DB had the empty initial migration (bb5377a56585) applied, so all
tables were never created. This migration creates every table with
IF NOT EXISTS so it is idempotent and safe to run on any state.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '5064ad40c48c'
down_revision: Union[str, Sequence[str], None] = 'bb5377a56585'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            price FLOAT NOT NULL,
            mileage INTEGER,
            condition VARCHAR NOT NULL,
            url VARCHAR NOT NULL UNIQUE,
            marketplace VARCHAR NOT NULL,
            scraped_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id SERIAL PRIMARY KEY,
            listing_id VARCHAR NOT NULL UNIQUE,
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            listing_price FLOAT NOT NULL,
            fipe_price FLOAT NOT NULL,
            discount_percentage FLOAT NOT NULL,
            discount_amount FLOAT NOT NULL,
            score_value INTEGER NOT NULL,
            marketplace VARCHAR NOT NULL,
            listing_url VARCHAR NOT NULL,
            condition VARCHAR NOT NULL,
            mileage INTEGER,
            status VARCHAR NOT NULL,
            image_url VARCHAR,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS price_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR NOT NULL UNIQUE,
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            price_value FLOAT NOT NULL,
            version VARCHAR NOT NULL,
            fipe_table_date VARCHAR NOT NULL,
            cached_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            session_id VARCHAR NOT NULL UNIQUE,
            ip_address VARCHAR,
            created_at TIMESTAMP,
            last_seen_at TIMESTAMP
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_sessions_session_id ON sessions (session_id)"
    ))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            session_id VARCHAR NOT NULL,
            opportunity_id VARCHAR NOT NULL,
            created_at TIMESTAMP,
            UNIQUE (session_id, opportunity_id)
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_favorites_session_id ON favorites (session_id)"
    ))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS search_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR NOT NULL UNIQUE,
            brand VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            year INTEGER,
            results_json TEXT NOT NULL,
            cached_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_search_cache_cache_key ON search_cache (cache_key)"
    ))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            alert_id VARCHAR NOT NULL UNIQUE,
            opportunity_id VARCHAR NOT NULL,
            recipient_id VARCHAR NOT NULL,
            channel VARCHAR NOT NULL,
            message VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            sent_at TIMESTAMP,
            delivered_at TIMESTAMP,
            error_message VARCHAR,
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS rate_limit_events (
            id SERIAL PRIMARY KEY,
            service VARCHAR NOT NULL,
            endpoint VARCHAR,
            status_code INTEGER NOT NULL DEFAULT 429,
            retry_attempt INTEGER NOT NULL DEFAULT 0,
            occurred_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_rate_limit_events_service ON rate_limit_events (service)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_rate_limit_events_occurred_at ON rate_limit_events (occurred_at)"
    ))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS api_hits (
            id SERIAL PRIMARY KEY,
            service VARCHAR NOT NULL,
            called_at TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_api_hits_service ON api_hits (service)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_api_hits_called_at ON api_hits (called_at)"
    ))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS catalog_cache (
            key VARCHAR PRIMARY KEY,
            data_json TEXT NOT NULL,
            last_count INTEGER NOT NULL,
            stable_streak INTEGER NOT NULL DEFAULT 0,
            current_ttl_seconds INTEGER NOT NULL,
            cached_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    for tbl in ['catalog_cache', 'api_hits', 'rate_limit_events', 'alerts',
                'search_cache', 'favorites', 'sessions', 'price_cache',
                'opportunities', 'listings']:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {tbl}"))
