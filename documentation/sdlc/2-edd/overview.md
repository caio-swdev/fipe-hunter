# EDD: FIPE Hunter

## Purpose
Technical foundation for implementing FIPE Hunter - an automated vehicle opportunity finder that identifies underpriced vehicles in Brazilian marketplaces by comparing listing prices against official FIPE reference valuations.

## Project Context
- **Tech Stack:** Python 3.9+, FastAPI, SQLite
- **Architecture:** Clean Architecture (domain-driven design)
- **Target:** Rio de Janeiro vehicle marketplaces (OLX, WebMotors)

## Documents

### Core Documentation
- [Architecture](architecture.md) - C4 diagrams (L1-L3) and system design
- [Folder Structure](folder-structure.md) - Project layout and module organization
- [Tech Stack](tech-stack.md) - Frameworks, libraries, and versions
- [Testing Strategy](testing-strategy.md) - Test approach and coverage targets
- [CI/CD](ci-cd.md) - Pipeline design and deployment strategy
- [Coding Conventions](conventions.md) - Python coding standards and patterns

### Architecture Decision Records
- [ADR Index](adr/README.md) - Project-level technical decisions

### Feature Implementation Specs
- [Web Scraping](specs/web-scraping-spec.md) - Marketplace listing extraction
- [FIPE Lookup](specs/fipe-lookup-spec.md) - Reference price integration
- [Price Comparison](specs/price-comparison-spec.md) - Discount calculation
- [Opportunity Scoring](specs/opportunity-scoring-spec.md) - Profit ranking algorithm
- [Sheets Integration](specs/sheets-integration-spec.md) - Google Sheets logging
- [Telegram Alerts](specs/telegram-alerts-spec.md) - Real-time notifications
- [CarWizard Integration](specs/carwizard-integration-spec.md) - System integration

## Getting Started

1. Read [Architecture](architecture.md) for system context
2. Review [Tech Stack](tech-stack.md) for technologies used
3. Check [Folder Structure](folder-structure.md) for code organization
4. Review relevant [Feature Specs](specs/) for implementation details

## Related Documentation
- **Design Phase:** [../1-design/](../1-design/) - Functional specifications and BDD scenarios
- **Enterprise Architecture:** [../../ea/](../../ea/) - Organization-wide patterns and standards
