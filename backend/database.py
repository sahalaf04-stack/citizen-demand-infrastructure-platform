"""
SQLite for local dev. Swap SQLALCHEMY_DATABASE_URL for a Postgres+PostGIS
connection string in production (e.g. postgresql://user:pass@host/db) -
the rest of the code doesn't need to change for the MVP fields we use here.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./citizen_platform.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
