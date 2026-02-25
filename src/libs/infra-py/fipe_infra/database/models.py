"""
SQLAlchemy Database Models

Defines the database schema for FIPE Hunter.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ListingModel(Base):
    """Database model for vehicle listings."""

    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    mileage = Column(Integer, nullable=True)
    condition = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    marketplace = Column(String, nullable=False)
    scraped_at = Column(DateTime, nullable=False)


class OpportunityModel(Base):
    """Database model for qualified opportunities."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String, unique=True, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    listing_price = Column(Float, nullable=False)
    fipe_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    score_value = Column(Integer, nullable=False)
    marketplace = Column(String, nullable=False)
    listing_url = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    mileage = Column(Integer, nullable=True)
    status = Column(String, nullable=False)  # active, suspicious, sold, expired
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class PriceCacheModel(Base):
    """Database model for FIPE price cache."""

    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String, unique=True, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    price_value = Column(Float, nullable=False)
    version = Column(String, nullable=False)
    fipe_table_date = Column(String, nullable=False)
    cached_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class SessionModel(Base):
    """Database model for anonymous user sessions."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)


class FavoriteModel(Base):
    """Database model for favorited opportunities."""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    opportunity_id = Column(String, nullable=False)  # maps to OpportunityModel.listing_id
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('session_id', 'opportunity_id'),)


class SearchCacheModel(Base):
    """Database model for search result cache (OLX + WebMotors scrape results)."""

    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String, unique=True, nullable=False, index=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    results_json = Column(Text, nullable=False)  # JSON-serialized list of result dicts
    cached_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class AlertModel(Base):
    """Database model for alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String, unique=True, nullable=False)
    opportunity_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # telegram, email
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, sent, failed, delivered
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)


class RateLimitEventModel(Base):
    """Database model for external API rate-limit events."""

    __tablename__ = "rate_limit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String, nullable=False, index=True)   # "fipe"|"olx"|"webmotors"
    endpoint = Column(String, nullable=True)
    status_code = Column(Integer, nullable=False, default=429)
    retry_attempt = Column(Integer, nullable=False, default=0)
    occurred_at = Column(DateTime, nullable=False, index=True)


class ApiHitModel(Base):
    """Tracks every outbound call to a 3rd-party API (FIPE, OLX, WebMotors)."""

    __tablename__ = "api_hits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String, nullable=False, index=True)  # "fipe" | "olx" | "webmotors"
    called_at = Column(DateTime, nullable=False, index=True)


class CatalogCacheModel(Base):
    """Database model for FIPE MMY catalog cache with adaptive TTL."""

    __tablename__ = "catalog_cache"

    key = Column(String, primary_key=True)   # "brands", "models:59", "years:59:4530"
    data_json = Column(Text, nullable=False)  # serialized API response
    last_count = Column(Integer, nullable=False)   # item count of last response
    stable_streak = Column(Integer, nullable=False, default=0)
    current_ttl_seconds = Column(Integer, nullable=False)
    cached_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
