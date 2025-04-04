# src/database.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.settings import settings  # Absolute import
from src.logging_config import setup_logging  # Absolute import

# --- Setup Logging ---
setup_logging()  # Call the setup function once on import

logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine
# For SQLite, connect_args is needed to support multi-threaded access (like FastAPI might use)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Only needed for SQLite
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
Base = declarative_base()


# Dependency for FastAPI to get a DB session
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Function to create database tables (optional, useful for initial setup)
# In a real app, you'd likely use Alembic for migrations
def create_db_tables():
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


# Example usage (e.g., in a startup script or main)
# if __name__ == "__main__":
#     create_db_tables()
