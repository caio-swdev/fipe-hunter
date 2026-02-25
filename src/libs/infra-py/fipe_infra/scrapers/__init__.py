"""
Scrapers Package

Marketplace scraper implementations.
"""
try:
    from fipe_infra.scrapers.curl_olx_scraper import CurlOLXScraper
except ImportError:
    pass

try:
    from fipe_infra.scrapers.webmotors_scraper import WebMotorsScraper
except ImportError:
    pass

__all__ = ["CurlOLXScraper", "WebMotorsScraper"]
