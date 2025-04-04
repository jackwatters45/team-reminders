# src/api.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from arq.connections import ArqRedis  # Import the ArqRedis type
from arq.jobs import Job  # Import Job type

# Use absolute imports
# from src import crud, models, schemas # Placeholder imports (will create later when files exist)
from src.database import (
    get_db,
)  # Only import get_db, Base, engine if needed directly here

# from src.settings import settings # settings usually not needed directly in api.py
from src.logging_config import setup_logging
from src.worker import get_arq_pool, close_arq_pool  # Import arq pool functions

# --- Setup Logging ---
setup_logging()  # Call the setup function once on import

logger = logging.getLogger(__name__)


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions on startup
    logger.info("Starting up API...")
    # Initialize arq pool on startup
    app.state.arq_pool = await get_arq_pool()
    logger.info("Arq Redis pool initialized.")

    # Optional: Create DB tables (better handled by migrations)
    # from src.database import create_db_tables
    # create_db_tables()

    yield  # API is ready to serve requests

    # Actions on shutdown
    logger.info("Shutting down API...")
    # Close arq pool on shutdown
    await close_arq_pool()
    app.state.arq_pool = None  # Clear state
    logger.info("Arq Redis pool closed.")
    logger.info("API shutdown complete.")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Team Reminder API",
    description="API for managing team reminders, schedule, and settings.",
    version="0.1.0",
    lifespan=lifespan,  # Use the new lifespan context manager
)


# --- API Endpoints (Placeholders) ---
@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the Team Reminder API"}


# Example placeholder using DB session
@app.get("/items/{item_id}")  # Example route
async def read_item(item_id: int, db: Session = Depends(get_db)):
    logger.info(
        f"Reading item {item_id} (placeholder). DB Session active: {db.is_active}"
    )
    # Replace with actual DB query using crud functions
    # from src import crud # Import crud here when needed
    # item = crud.get_item(db, item_id=item_id)
    # if item is None:
    #     raise HTTPException(status_code=404, detail="Item not found")
    return {
        "item_id": item_id,
        "description": "Placeholder item",
        "db_session_active": db.is_active,
    }


# Placeholder for triggering a task using arq pool from app state
@app.post("/send/trigger")
async def trigger_send(arq_pool: ArqRedis = Depends(lambda: app.state.arq_pool)):
    if not arq_pool:
        logger.error("Arq pool not available.")
        raise HTTPException(status_code=500, detail="Task queue not available")

    logger.info("Manual send triggered. Enqueuing task...")
    # Enqueue the main task
    job: Job | None = await arq_pool.enqueue_job("send_all_reminders_task")

    if job:
        logger.info(f"Enqueued job: {job.job_id}")
        return {"message": "Send process triggered", "job_id": job.job_id}
    else:
        logger.error("Failed to enqueue job.")
        raise HTTPException(status_code=500, detail="Failed to enqueue background task")


# Add more placeholder endpoints for settings, recipients, schedule as needed
# e.g., @app.get("/recipients/"), @app.post("/recipients/"), etc.
