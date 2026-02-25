-- FIPE Hunter Database Schema
-- SQLite

-- === CORE ENTITIES ===

CREATE TABLE IF NOT EXISTS vehicles (
  id TEXT PRIMARY KEY,
  brand VARCHAR(100) NOT NULL,
  model VARCHAR(100) NOT NULL,
  year INTEGER NOT NULL,
  version VARCHAR(100),
  transmission VARCHAR(50),
  fuel_type VARCHAR(50),
  fipe_key VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT valid_year CHECK (year >= 1950 AND year <= CAST(strftime('%Y', 'now') AS INTEGER))
);

CREATE INDEX idx_vehicles_brand_model_year ON vehicles(brand, model, year);
CREATE INDEX idx_vehicles_fipe_key ON vehicles(fipe_key);

-- Listings from marketplaces
CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY,
  vehicle_id TEXT NOT NULL,
  marketplace VARCHAR(50) NOT NULL,
  listing_price DECIMAL(12, 2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'BRL',
  mileage INTEGER,
  condition VARCHAR(50) NOT NULL,
  url TEXT NOT NULL UNIQUE,
  description TEXT,
  seller_name VARCHAR(100),
  seller_rating DECIMAL(3, 2),
  is_duplicate BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
  CONSTRAINT valid_price CHECK (listing_price > 0),
  CONSTRAINT valid_mileage CHECK (mileage >= 0),
  CONSTRAINT valid_condition CHECK (condition IN ('excellent', 'good', 'fair', 'poor'))
);

CREATE INDEX idx_listings_marketplace ON listings(marketplace);
CREATE INDEX idx_listings_vehicle_id ON listings(vehicle_id);
CREATE INDEX idx_listings_created_at ON listings(created_at);
CREATE INDEX idx_listings_is_duplicate ON listings(is_duplicate);

-- Qualified opportunities
CREATE TABLE IF NOT EXISTS opportunities (
  id TEXT PRIMARY KEY,
  listing_id TEXT NOT NULL,
  fipe_price DECIMAL(12, 2) NOT NULL,
  discount_pct DECIMAL(5, 2) NOT NULL,
  discount_amount DECIMAL(12, 2) NOT NULL,
  score INTEGER NOT NULL,
  status VARCHAR(50) DEFAULT 'new',
  source VARCHAR(50) DEFAULT 'bulk_scrape',
  carwizard_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
  CONSTRAINT valid_score CHECK (score >= 0 AND score <= 100),
  CONSTRAINT valid_discount_pct CHECK (discount_pct >= -100 AND discount_pct <= 100),
  CONSTRAINT valid_source CHECK (source IN ('bulk_scrape', 'on_demand_search'))
);

CREATE INDEX idx_opportunities_score ON opportunities(score);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_source ON opportunities(source);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at);
CREATE INDEX idx_opportunities_carwizard_id ON opportunities(carwizard_id);

-- === ALERTS & NOTIFICATIONS ===

CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY,
  opportunity_id TEXT NOT NULL,
  channel VARCHAR(50) NOT NULL,
  recipient VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  message TEXT,
  sent_at TIMESTAMP,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  CONSTRAINT valid_channel CHECK (channel IN ('telegram', 'sheets', 'carwizard')),
  CONSTRAINT valid_alert_status CHECK (status IN ('pending', 'sent', 'failed', 'retry'))
);

CREATE INDEX idx_alerts_opportunity_id ON alerts(opportunity_id);
CREATE INDEX idx_alerts_channel ON alerts(channel);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- Alert delivery history
CREATE TABLE IF NOT EXISTS alert_history (
  id TEXT PRIMARY KEY,
  opportunity_id TEXT NOT NULL,
  alert_id TEXT,
  channel VARCHAR(50) NOT NULL,
  status VARCHAR(50) NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE SET NULL
);

CREATE INDEX idx_alert_history_opportunity_id ON alert_history(opportunity_id);
CREATE INDEX idx_alert_history_timestamp ON alert_history(timestamp);

-- === CACHING & PERFORMANCE ===

CREATE TABLE IF NOT EXISTS price_cache (
  id TEXT PRIMARY KEY,
  vehicle_key VARCHAR(255) UNIQUE NOT NULL,
  fipe_price DECIMAL(12, 2) NOT NULL,
  cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_price_cache_expires_at ON price_cache(expires_at);

-- === LOGGING & MONITORING ===

CREATE TABLE IF NOT EXISTS scrape_logs (
  id TEXT PRIMARY KEY,
  marketplace VARCHAR(50) NOT NULL,
  start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  end_time TIMESTAMP,
  listings_found INTEGER DEFAULT 0,
  listings_saved INTEGER DEFAULT 0,
  error_message TEXT,
  status VARCHAR(50) DEFAULT 'running',
  duration_seconds INTEGER
);

CREATE INDEX idx_scrape_logs_marketplace ON scrape_logs(marketplace);
CREATE INDEX idx_scrape_logs_start_time ON scrape_logs(start_time);
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status);

-- Opportunity action log
CREATE TABLE IF NOT EXISTS opportunity_logs (
  id TEXT PRIMARY KEY,
  listing_id TEXT NOT NULL,
  action VARCHAR(100) NOT NULL,
  details TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
);

CREATE INDEX idx_opportunity_logs_listing_id ON opportunity_logs(listing_id);
CREATE INDEX idx_opportunity_logs_timestamp ON opportunity_logs(timestamp);

-- === VIEWS (For Analytics) ===

CREATE VIEW IF NOT EXISTS v_top_opportunities AS
SELECT
  o.id,
  v.brand,
  v.model,
  v.year,
  l.listing_price,
  o.fipe_price,
  o.discount_pct,
  o.score,
  l.marketplace,
  o.source,
  l.url,
  o.created_at
FROM opportunities o
JOIN listings l ON o.listing_id = l.id
JOIN vehicles v ON l.vehicle_id = v.id
WHERE o.status = 'new'
ORDER BY o.score DESC
LIMIT 50;

CREATE VIEW IF NOT EXISTS v_alert_summary AS
SELECT
  DATE(a.created_at) as date,
  a.channel,
  COUNT(*) as total_alerts,
  SUM(CASE WHEN a.status = 'sent' THEN 1 ELSE 0 END) as sent,
  SUM(CASE WHEN a.status = 'failed' THEN 1 ELSE 0 END) as failed,
  SUM(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending
FROM alerts a
GROUP BY DATE(a.created_at), a.channel;

CREATE VIEW IF NOT EXISTS v_marketplace_stats AS
SELECT
  l.marketplace,
  COUNT(DISTINCT l.id) as total_listings,
  COUNT(DISTINCT o.id) as total_opportunities,
  AVG(o.discount_pct) as avg_discount_pct,
  AVG(o.score) as avg_score,
  MAX(o.created_at) as last_update
FROM listings l
LEFT JOIN opportunities o ON l.id = o.listing_id
GROUP BY l.marketplace;

CREATE VIEW IF NOT EXISTS v_price_trends AS
SELECT
  DATE(o.created_at) as date,
  AVG(o.discount_pct) as avg_discount_pct,
  AVG(o.score) as avg_score,
  COUNT(DISTINCT o.id) as opportunities_count,
  COUNT(DISTINCT l.id) as listings_count
FROM opportunities o
JOIN listings l ON o.listing_id = l.id
WHERE o.created_at >= datetime('now', '-30 days')
GROUP BY DATE(o.created_at)
ORDER BY date DESC;

CREATE VIEW IF NOT EXISTS v_discount_distribution AS
SELECT
  CASE
    WHEN o.discount_pct >= 0 AND o.discount_pct < 10 THEN '0-10%'
    WHEN o.discount_pct >= 10 AND o.discount_pct < 20 THEN '10-20%'
    WHEN o.discount_pct >= 20 AND o.discount_pct < 30 THEN '20-30%'
    WHEN o.discount_pct >= 30 AND o.discount_pct < 40 THEN '30-40%'
    WHEN o.discount_pct >= 40 AND o.discount_pct < 50 THEN '40-50%'
    WHEN o.discount_pct >= 50 THEN '50%+'
  END as discount_bucket,
  COUNT(DISTINCT o.id) as opportunity_count
FROM opportunities o
WHERE o.created_at >= datetime('now', '-30 days')
GROUP BY discount_bucket
ORDER BY discount_bucket;

CREATE VIEW IF NOT EXISTS v_brand_analysis AS
SELECT
  v.brand,
  COUNT(DISTINCT o.id) as opportunities_count,
  AVG(o.score) as avg_score,
  AVG(o.discount_pct) as avg_discount_pct,
  MAX(o.created_at) as last_update
FROM opportunities o
JOIN listings l ON o.listing_id = l.id
JOIN vehicles v ON l.vehicle_id = v.id
WHERE o.created_at >= datetime('now', '-30 days')
GROUP BY v.brand
ORDER BY opportunities_count DESC
LIMIT 10;

CREATE VIEW IF NOT EXISTS v_dashboard_summary AS
SELECT
  (SELECT COUNT(*) FROM opportunities WHERE status = 'new') as total_found,
  (SELECT COUNT(*) FROM opportunities WHERE DATE(created_at) = DATE('now')) as new_today,
  (SELECT COUNT(*) FROM opportunities WHERE DATE(created_at) = DATE('now') AND source = 'bulk_scrape') as bulk_scrape_today,
  (SELECT COUNT(*) FROM opportunities WHERE DATE(created_at) = DATE('now') AND source = 'on_demand_search') as on_demand_today,
  (SELECT COUNT(*) FROM opportunities WHERE score > 75 AND status = 'new') as high_score_count,
  (SELECT MAX(score) FROM opportunities) as top_score,
  (SELECT COUNT(*) FROM scrape_logs WHERE DATE(start_time) = DATE('now')) as scrapes_today,
  (SELECT COUNT(*) FROM alerts WHERE status = 'pending') as pending_alerts;

-- === CONFIGURATION TABLE ===

CREATE TABLE IF NOT EXISTS system_config (
  id TEXT PRIMARY KEY DEFAULT 'singleton',
  scraping_frequency VARCHAR(50) DEFAULT 'hourly',
  scraping_start_time VARCHAR(5) DEFAULT '08:00',
  scraping_days_of_week VARCHAR(100) DEFAULT '0,1,2,3,4,5,6',
  olx_enabled BOOLEAN DEFAULT TRUE,
  webmotors_enabled BOOLEAN DEFAULT TRUE,
  telegram_alert_threshold INTEGER DEFAULT 75,
  carwizard_sync_threshold INTEGER DEFAULT 80,
  sheets_logging_enabled BOOLEAN DEFAULT TRUE,
  discount_min_pct DECIMAL(5, 2) DEFAULT 20.00,
  discount_max_pct DECIMAL(5, 2) DEFAULT 50.00,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (id = 'singleton')
);

CREATE TRIGGER IF NOT EXISTS trg_system_config_update
AFTER UPDATE ON system_config
BEGIN
  UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE id = 'singleton';
END;

-- === CONSTRAINTS & TRIGGERS ===

CREATE TRIGGER IF NOT EXISTS trg_listings_update
AFTER UPDATE ON listings
BEGIN
  UPDATE listings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_opportunities_update
AFTER UPDATE ON opportunities
BEGIN
  UPDATE opportunities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_alerts_update
AFTER UPDATE ON alerts
BEGIN
  UPDATE alerts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Clean up expired cache entries (called via scheduled job)
CREATE TRIGGER IF NOT EXISTS trg_price_cache_cleanup
AFTER INSERT ON price_cache
WHEN (SELECT COUNT(*) FROM price_cache WHERE expires_at < CURRENT_TIMESTAMP) > 100
BEGIN
  DELETE FROM price_cache WHERE expires_at < CURRENT_TIMESTAMP LIMIT 100;
END;
