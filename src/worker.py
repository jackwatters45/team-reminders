# src/worker.py
import logging
from typing import Dict, Any  # For typing ctx

from arq import create_pool
from arq.connections import RedisSettings

from src.settings import settings  # Absolute import
from src.logging_config import setup_logging  # Absolute import
# from src import crud, models # Absolute import (when needed)
# from src.database import SessionLocal # Absolute import (when needed)
# from src.main import send_message # Absolute import (when needed)

# --- Setup Logging ---
setup_logging()  # Call the setup function once on import

logger = logging.getLogger(__name__)

# --- Placeholder Task Functions ---


# Add type hint for arq context dictionary
async def send_single_reminder_task(ctx: Dict[str, Any], recipient_id: int):
    """Sends a reminder to a single recipient (identified by DB ID)."""
    logger.info(
        f"Running task: send_single_reminder_task for recipient_id={recipient_id}"
    )
    # redis = ctx["redis"]
    # db = SessionLocal() # Create a new session for this task
    try:
        # 1. Get recipient details from DB using recipient_id
        # recipient = crud.get_recipient(db, recipient_id)
        # if not recipient or not recipient.send_flag:
        #     logger.warning(f"Recipient {recipient_id} not found or flag disabled, skipping.")
        #     return

        # 2. Call the actual sending logic (e.g., Twilio)
        # send_message(phone_number=recipient.phone_number, name=recipient.name)
        logger.info(f"Placeholder: Sent reminder to recipient {recipient_id}")
        # Optionally update DB status for this recipient

    except Exception as e:
        logger.error(f"Error in send_single_reminder_task for {recipient_id}: {e}")
        # Add retry logic or specific error handling if needed
    finally:
        # db.close() # Ensure session is closed
        pass


async def send_all_reminders_task(ctx: Dict[str, Any]):
    """Gets all applicable recipients and enqueues individual tasks."""
    logger.info("Running task: send_all_reminders_task")
    # db = SessionLocal()
    try:
        # 1. Query DB for all recipients where send_flag is True
        # recipients_to_send = crud.get_active_recipients(db)
        recipients_to_send = [1, 2, 3]  # Placeholder IDs
        logger.info(f"Found {len(recipients_to_send)} recipients to send reminders to.")

        # 2. Enqueue a separate job for each recipient
        redis = ctx["redis"]  # Get redis pool from context
        for recipient_id in recipients_to_send:
            # Type checkers might not know about enqueue_job on the redis object
            await redis.enqueue_job("send_single_reminder_task", recipient_id)  # type: ignore[attr-defined]
            logger.debug(
                f"Enqueued send_single_reminder_task for recipient_id={recipient_id}"
            )

    except Exception as e:
        logger.error(f"Error in send_all_reminders_task: {e}")
    finally:
        # db.close()
        pass


async def startup(ctx: Dict[str, Any]):
    logger.info("Worker starting up...")
    # Can initialize resources here if needed, e.g., DB connection pool
    # ctx['db_pool'] = await create_db_pool()


async def shutdown(ctx: Dict[str, Any]):
    logger.info("Worker shutting down...")
    # Clean up resources
    # await close_db_pool(ctx['db_pool'])


# --- Worker Settings ---
# Defines the functions the worker can run and Redis connection
class WorkerSettings:
    functions = [send_single_reminder_task, send_all_reminders_task]
    on_startup = startup
    on_shutdown = shutdown
    # Pass the string representation of the DSN
    redis_settings = RedisSettings.from_dsn(str(settings.REDIS_URL))
    # max_jobs = 10 # Control concurrency
    # job_timeout = 60 # Timeout for a single job


# --- Function to get an arq redis pool (for enqueueing from API) ---
# Note: Ensure this pool is managed correctly (e.g., created once per app instance)
# In FastAPI, you might create this on startup and store it in app.state

_arq_redis_pool = None


async def get_arq_pool():
    global _arq_redis_pool
    if _arq_redis_pool is None:
        _arq_redis_pool = await create_pool(WorkerSettings.redis_settings)
    return _arq_redis_pool


async def close_arq_pool():
    global _arq_redis_pool
    if _arq_redis_pool:
        await _arq_redis_pool.close()
        _arq_redis_pool = None
