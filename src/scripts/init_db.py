#!/usr/bin/env python3
"""
Initialize FIPE Hunter Database

Creates all necessary tables in the SQLite database.
"""
import sys
from pathlib import Path


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "libs" / "infra-py"))

from sqlalchemy import create_engine
from fipe_infra.database.models import Base


DB_PATH = project_root / "fipe_hunter.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

def init_database():
    """Create all tables in the database."""
    print(f"Initializing database at: {DB_PATH}")


    engine = create_engine(DATABASE_URL, echo=True)


    Base.metadata.create_all(engine)

    print("\n✅ Database initialized successfully!")
    print(f"Tables created: {', '.join(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    init_database()
