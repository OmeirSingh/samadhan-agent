"""SQLite persistence via SQLAlchemy.

The deck specifies PostgreSQL for production. SQLite is used here for a
zero-config prototype that runs anywhere — the SQLAlchemy models are
Postgres-compatible, so swapping the URL is the only change needed to
move to Postgres.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samadhan.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Hosted Postgres providers (Render, Neon, Supabase, Heroku) hand out URLs that
# start with "postgres://". SQLAlchemy + the modern psycopg 3 driver need the
# "postgresql+psycopg://" scheme, so normalise it here.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
