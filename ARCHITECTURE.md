# Architecture

## Package Diagram

![Package Diagram](./documentation/diagrams/5-package-diagram.png)

The system follows Clean Architecture: domain logic is isolated from web framework, database, and scraping adapters. The FastAPI app wires them together at the infra layer.

## Database ERD

![Database ERD](./documentation/diagrams/10-database-erd.png)

SQLite with three core tables: `cars`, `fipe_references`, and `opportunities`. The opportunities view joins listing price against the FIPE reference to compute the delta.

## Class Diagram

![Class Diagram](./documentation/diagrams/9-class-diagram.png)
