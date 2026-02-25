# Project Overview: FIPE Hunter

## Description

FIPE Hunter is an automated vehicle opportunity finder that scrapes listings from Brazilian marketplaces (OLX, WebMotors) and identifies vehicles with significant discounts (20-50%) compared to FIPE reference prices. The system scores opportunities by profit potential and delivers real-time alerts via Telegram while logging results to Google Sheets.

## Tech Stack

- **Backend:** Python 3.9+, FastAPI
- **Database:** SQLite
- **External APIs:** FIPE (reference prices), Telegram Bot API, Google Sheets API
- **Web Scraping:** BeautifulSoup4, requests
- **Data Processing:** pandas

## Key Constraints

- Target market: Rio de Janeiro, Brazil
- FIPE pricing is the source of truth for vehicle valuations
- System must handle anti-bot measures (user-agent rotation, rate limiting)
- Real-time alerting via Telegram Bot
- Google Sheets integration for persistent logging
- CarWizard system integration for advanced vehicle analysis
