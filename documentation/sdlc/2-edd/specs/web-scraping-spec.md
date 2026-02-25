# Feature Implementation Spec: Web Scraping

## Overview
Technical specification for implementing the web scraping feature that extracts vehicle listings from OLX and WebMotors marketplaces.

## Design Reference
- **BDD Spec**: [../../1-design/web-scraping/2-web-scraping-bdd-spec.feature](../../1-design/web-scraping/2-web-scraping-bdd-spec.feature)
- **Use Case**: [../../1-design/web-scraping/6-web-scraping-usecase-specification.md](../../1-design/web-scraping/6-web-scraping-usecase-specification.md)

## Architecture Layer Breakdown

### Domain Layer
**Location**: `src/domain/entities/`

**Entities**:
```python
# src/domain/entities/listing.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Listing:
    brand: str
    model: str
    year: int
    price: float
    mileage: int | None
    condition: str  # "excellent" | "good" | "fair" | "poor"
    url: str
    marketplace: str  # "olx" | "webmotors"
    scraped_at: datetime
```

```python
# src/domain/entities/scrape_log.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScrapeLog:
    marketplace: str
    status: str  # "running" | "completed" | "failed"
    listings_found: int
    listings_saved: int
    errors: list[str]
    started_at: datetime
    completed_at: datetime | None
```

**Ports (Interfaces)**:
```python
# src/domain/ports/scraper.py
from typing import Protocol
from src.domain.entities import Listing

class IScraper(Protocol):
    """Interface for marketplace scrapers."""

    def scrape(self) -> list[Listing]:
        """Scrape marketplace and return listings."""
        ...

# src/domain/ports/listing_repository.py
from typing import Protocol
from src.domain.entities import Listing

class IListingRepository(Protocol):
    def save(self, listing: Listing) -> None: ...
    def find_by_url(self, url: str) -> Listing | None: ...
    def count_by_marketplace(self, marketplace: str) -> int: ...
```

### Application Layer (Use Cases)
**Location**: `src/application/`

```python
# src/application/scrape_listings.py
from src.domain.entities import Listing, ScrapeLog
from src.domain.ports import IScraper, IListingRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ScrapeListingsUseCase:
    """Use case for scraping marketplace listings."""

    def __init__(
        self,
        scraper: IScraper,
        repository: IListingRepository
    ):
        self._scraper = scraper
        self._repository = repository

    def execute(self, marketplace: str) -> ScrapeLog:
        """Execute scraping for given marketplace."""
        started_at = datetime.utcnow()

        try:
            # Scrape listings
            listings = self._scraper.scrape()

            # Deduplicate and save
            saved_count = 0
            for listing in listings:
                existing = self._repository.find_by_url(listing.url)
                if not existing:
                    self._repository.save(listing)
                    saved_count += 1

            # Log success
            return ScrapeLog(
                marketplace=marketplace,
                status="completed",
                listings_found=len(listings),
                listings_saved=saved_count,
                errors=[],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Scraping failed for {marketplace}: {e}")
            return ScrapeLog(
                marketplace=marketplace,
                status="failed",
                listings_found=0,
                listings_saved=0,
                errors=[str(e)],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
```

### Adapters Layer (Integration)
**Location**: `src/adapters/`

**Scrapers**:
```python
# src/adapters/scrapers/olx_scraper.py
from src.domain.entities import Listing
from src.domain.ports import IScraper
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from datetime import datetime
import time
import random

class OLXScraper(IScraper):
    """OLX marketplace scraper."""

    BASE_URL = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios/estado-rj/regiao-de-rio-de-janeiro"

    def scrape(self) -> list[Listing]:
        """Scrape OLX marketplace."""
        ua = UserAgent()
        headers = {"User-Agent": ua.random}

        # Add delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))

        response = requests.get(self.BASE_URL, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        listings = []

        for item in soup.select("li[data-id]"):
            try:
                listing = self._parse_listing_item(item)
                listings.append(listing)
            except Exception as e:
                # Log parsing error but continue
                logger.warning(f"Failed to parse OLX listing: {e}")
                continue

        return listings

    def _parse_listing_item(self, item) -> Listing:
        """Parse individual listing element."""
        # Extract fields (marketplace-specific)
        title = item.select_one("h2").text.strip()
        price_text = item.select_one(".price").text.strip()
        url = item.select_one("a")["href"]

        # Parse price (format: "R$ 30.000")
        price = float(price_text.replace("R$", "").replace(".", "").replace(",", ".").strip())

        # Parse title for brand, model, year
        # Example: "Volkswagen Gol 2020"
        parts = title.split()
        brand = parts[0]
        model = " ".join(parts[1:-1])
        year = int(parts[-1])

        return Listing(
            brand=brand,
            model=model,
            year=year,
            price=price,
            mileage=None,  # Extract if available
            condition="good",  # Default
            url=url,
            marketplace="olx",
            scraped_at=datetime.utcnow()
        )
```

**Controller**:
```python
# src/adapters/controllers/scrape_controller.py
from fastapi import APIRouter, HTTPException
from src.application.scrape_listings import ScrapeListingsUseCase

router = APIRouter(prefix="/api/v1/scrape", tags=["scraping"])

@router.post("/olx")
def scrape_olx(use_case: ScrapeListingsUseCase):
    """Trigger OLX marketplace scrape."""
    result = use_case.execute("olx")

    if result.status == "failed":
        raise HTTPException(status_code=500, detail=result.errors)

    return {
        "marketplace": result.marketplace,
        "listings_found": result.listings_found,
        "listings_saved": result.listings_saved,
        "duration_seconds": (result.completed_at - result.started_at).total_seconds()
    }

@router.post("/webmotors")
def scrape_webmotors(use_case: ScrapeListingsUseCase):
    """Trigger WebMotors marketplace scrape."""
    result = use_case.execute("webmotors")

    if result.status == "failed":
        raise HTTPException(status_code=500, detail=result.errors)

    return {
        "marketplace": result.marketplace,
        "listings_found": result.listings_found,
        "listings_saved": result.listings_saved,
        "duration_seconds": (result.completed_at - result.started_at).total_seconds()
    }
```

### Infrastructure Layer
**Location**: `src/infrastructure/`

**Repository Implementation**:
```python
# src/infrastructure/repositories/listing_repository.py
from src.domain.entities import Listing
from src.domain.ports import IListingRepository
from src.infrastructure.database.models import ListingModel
from sqlalchemy.orm import Session

class SQLAlchemyListingRepository(IListingRepository):
    """SQLAlchemy implementation of listing repository."""

    def __init__(self, session: Session):
        self._session = session

    def save(self, listing: Listing) -> None:
        model = ListingModel(
            brand=listing.brand,
            model=listing.model,
            year=listing.year,
            price=listing.price,
            mileage=listing.mileage,
            condition=listing.condition,
            url=listing.url,
            marketplace=listing.marketplace,
            scraped_at=listing.scraped_at
        )
        self._session.add(model)
        self._session.commit()

    def find_by_url(self, url: str) -> Listing | None:
        model = self._session.query(ListingModel).filter_by(url=url).first()
        if not model:
            return None

        return Listing(
            brand=model.brand,
            model=model.model,
            year=model.year,
            price=model.price,
            mileage=model.mileage,
            condition=model.condition,
            url=model.url,
            marketplace=model.marketplace,
            scraped_at=model.scraped_at
        )

    def count_by_marketplace(self, marketplace: str) -> int:
        return self._session.query(ListingModel).filter_by(marketplace=marketplace).count()
```

**Database Model**:
```python
# src/infrastructure/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ListingModel(Base):
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
```

## API Endpoints

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| POST | /api/v1/scrape/olx | Trigger OLX scrape | ScrapeLog summary |
| POST | /api/v1/scrape/webmotors | Trigger WebMotors scrape | ScrapeLog summary |
| GET | /api/v1/scrape/status | Get scrape status | Current scrape state |

## Testing Strategy

### Unit Tests
**Location**: `tests/unit/application/test_scrape_listings.py`

```python
from unittest.mock import Mock
from src.application.scrape_listings import ScrapeListingsUseCase

def test_scrape_listings_saves_new_listings():
    # Arrange
    mock_scraper = Mock()
    mock_scraper.scrape.return_value = [sample_listing]

    mock_repo = Mock()
    mock_repo.find_by_url.return_value = None  # Not a duplicate

    use_case = ScrapeListingsUseCase(mock_scraper, mock_repo)

    # Act
    result = use_case.execute("olx")

    # Assert
    assert result.status == "completed"
    assert result.listings_saved == 1
    mock_repo.save.assert_called_once()
```

### Integration Tests
**Location**: `tests/integration/test_olx_scraper.py`

```python
import responses
from src.adapters.scrapers.olx_scraper import OLXScraper

@responses.activate
def test_olx_scraper_parses_listings():
    # Arrange
    responses.add(
        responses.GET,
        OLXScraper.BASE_URL,
        body=open("tests/fixtures/olx_response.html").read(),
        status=200
    )

    scraper = OLXScraper()

    # Act
    listings = scraper.scrape()

    # Assert
    assert len(listings) > 0
    assert listings[0].marketplace == "olx"
```

## Error Handling

| Error | Handling |
|-------|----------|
| HTTP 5xx | Retry 3 times with exponential backoff |
| HTTP 429 | Increase delay, retry after 60s |
| Parsing error | Log, skip listing, continue |
| Network timeout | Retry 3 times, then fail gracefully |

## Performance Requirements
- Scrape 50 listings in < 2 minutes
- Parse each listing in < 100ms
- Handle rate limiting without data loss

## Related Documentation
- [Architecture](../architecture.md) - System design
- [ADR-0004: BeautifulSoup Scraping](../adr/0004-beautifulsoup-scraping.md)
- [Use Case Specification](../../1-design/web-scraping/6-web-scraping-usecase-specification.md)
