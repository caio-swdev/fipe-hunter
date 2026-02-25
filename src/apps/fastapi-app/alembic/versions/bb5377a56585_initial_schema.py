"""initial_schema

Revision ID: bb5377a56585
Revises:
Create Date: 2026-02-22 18:43:18.759247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb5377a56585'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('marketplace', sa.String(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
    )
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('listing_id', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('listing_price', sa.Float(), nullable=False),
        sa.Column('fipe_price', sa.Float(), nullable=False),
        sa.Column('discount_percentage', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('score_value', sa.Integer(), nullable=False),
        sa.Column('marketplace', sa.String(), nullable=False),
        sa.Column('listing_url', sa.String(), nullable=False),
        sa.Column('condition', sa.String(), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('listing_id'),
    )
    op.create_table(
        'price_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('price_value', sa.Float(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('fipe_table_date', sa.String(), nullable=False),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
    )
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('ix_sessions_session_id', 'sessions', ['session_id'])
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('opportunity_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'opportunity_id'),
    )
    op.create_index('ix_favorites_session_id', 'favorites', ['session_id'])
    op.create_table(
        'search_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('results_json', sa.Text(), nullable=False),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
    )
    op.create_index('ix_search_cache_cache_key', 'search_cache', ['cache_key'])
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.String(), nullable=False),
        sa.Column('opportunity_id', sa.String(), nullable=False),
        sa.Column('recipient_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_id'),
    )
    op.create_table(
        'rate_limit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('retry_attempt', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rate_limit_events_service', 'rate_limit_events', ['service'])
    op.create_index('ix_rate_limit_events_occurred_at', 'rate_limit_events', ['occurred_at'])
    op.create_table(
        'api_hits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('called_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_hits_service', 'api_hits', ['service'])
    op.create_index('ix_api_hits_called_at', 'api_hits', ['called_at'])
    op.create_table(
        'catalog_cache',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('data_json', sa.Text(), nullable=False),
        sa.Column('last_count', sa.Integer(), nullable=False),
        sa.Column('stable_streak', sa.Integer(), nullable=False),
        sa.Column('current_ttl_seconds', sa.Integer(), nullable=False),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    op.drop_table('catalog_cache')
    op.drop_index('ix_api_hits_called_at', 'api_hits')
    op.drop_index('ix_api_hits_service', 'api_hits')
    op.drop_table('api_hits')
    op.drop_index('ix_rate_limit_events_occurred_at', 'rate_limit_events')
    op.drop_index('ix_rate_limit_events_service', 'rate_limit_events')
    op.drop_table('rate_limit_events')
    op.drop_table('alerts')
    op.drop_index('ix_search_cache_cache_key', 'search_cache')
    op.drop_table('search_cache')
    op.drop_index('ix_favorites_session_id', 'favorites')
    op.drop_table('favorites')
    op.drop_index('ix_sessions_session_id', 'sessions')
    op.drop_table('sessions')
    op.drop_table('price_cache')
    op.drop_table('opportunities')
    op.drop_table('listings')
