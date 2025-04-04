# Team Reminders - Implementation Plan

This document outlines the steps for building the Team Reminders application.

## Implementation Steps

1. **Project Setup:**
   - Initialize the project structure (e.g., using `cookiecutter` or manually).
   - Set up the main FastAPI application (`main.py`).
   - Configure database connection (e.g., in `database.py` or `config.py`).
   - Define dependencies in `requirements.txt` or `pyproject.toml`.

2. **Database Modeling (`models.py`):**
   - Define SQLAlchemy models for:
     - `User`: Stores user information (id, email, hashed password, name, team
       memberships).
     - `Team`: Stores team information (id, name, members).
     - `Reminder`: Stores reminder details (id, message, due_datetime,
       created_by_user_id, team_id, is_recurring, cron_schedule - optional).
   - Establish relationships:
     - Many-to-Many between `User` and `Team`.
     - One-to-Many between `Team` and `Reminder`.
     - One-to-Many between `User` (creator) and `Reminder`.

3. **API Schemas (`schemas.py`):**
   - Create Pydantic schemas for request bodies and response models
     corresponding to the database models.
   - Include schemas for creation, update, and retrieval (e.g., `UserCreate`,
     `UserUpdate`, `UserInDB`, `ReminderCreate`, etc.).
   - Define schemas for authentication (`Token`, `TokenData`).

4. **CRUD Operations (`crud.py`):**
   - Implement functions for Create, Read, Update, Delete operations for each
     model.
   - These functions will take a database session and Pydantic schemas as
     input/output.
   - Example: `create_user(db: Session, user: schemas.UserCreate)`,
     `get_reminders_by_team(db: Session, team_id: int)`.

5. **API Endpoints (`routers/`):**
   - Create FastAPI `APIRouter` instances for each resource (`users.py`,
     `teams.py`, `reminders.py`).
   - Define path operations (e.g., `@router.post("/")`,
     `@router.get("/{item_id}")`) that use the `crud` functions.
   - Inject dependencies like the database session (`Depends(get_db)`).
   - Include an authentication router (`auth.py`).
   - Mount routers in the main FastAPI app (`main.py`).

6. **Authentication (`auth.py`, `dependencies.py`):**
   - Implement user registration and login endpoints.
   - Use password hashing (e.g., `passlib`).
   - Integrate JWT (JSON Web Tokens) for token-based authentication.
   - Create dependency functions (e.g., `get_current_user`) to protect endpoints
     and retrieve the authenticated user. Consider using FastAPI Users library
     for simplification.

7. **Arq Integration for Background Tasks (`tasks.py`, `worker.py`):**
   - **Setup:**
     - Configure `arq` settings (Redis connection details) potentially in
       `config.py`.
     - Define `arq` task functions in `tasks.py` (e.g.,
       `schedule_reminder_check`, `send_reminder_notification`).
     - Create a `worker.py` script or use the `arq` CLI to run the worker
       process.
   - **Reminder Scheduling:**
     - When a reminder is created or updated via the API, enqueue an `arq` job.
     - For non-recurring reminders: Enqueue a job (`send_reminder_notification`)
       scheduled for the `due_datetime`.
     - For recurring reminders: Enqueue a recurring job
       (`schedule_reminder_check`?) or manage scheduling logic within a periodic
       task.
   - **Reminder Dispatching (Alternative for non-scheduled jobs):**
     - Create a recurring `arq` task (e.g., `check_due_reminders`, running every
       minute via `cron` setting in `arq`).
     - This task queries the database (`crud.get_due_reminders`) for reminders
       due within the next minute (or interval).
     - For each due reminder, enqueue a `send_reminder_notification` task.
   - **Notification Sending:**
     - The `send_reminder_notification` task will contain the logic to:
       - Fetch full reminder and team details.
       - Format the notification message.
       - Send the notification via the chosen channel (e.g., Email, Slack API -
         implementation TBD).
       - Update the reminder status if necessary (e.g., mark as sent).
   - **Why Arq?**
     - **Asynchronous Execution:** Prevents blocking API requests for tasks like
       sending notifications or complex scheduling checks. The API can return a
       response immediately.
     - **Reliability:** `arq` handles retries and ensures tasks are executed
       even if the worker restarts (thanks to Redis persistence).
     - **Scalability:** You can run multiple worker processes to handle higher
       loads.
     - **Scheduling:** Built-in support for cron-like recurring tasks and
       delayed job execution.
     - **Documentation:** Find detailed `arq` documentation here:
       [https://arq-docs.helpmanual.io/](https://arq-docs.helpmanual.io/)

8. **Testing (`tests/`):**
   - Write unit tests for `crud` functions, utility functions, and potentially
     `arq` task logic (can be tested without a full worker).
   - Write integration tests using FastAPI's `TestClient` to test API endpoints,
     including authentication and interactions with the database (using a test
     database).

9. **Containerization (Optional):**
   - Create a `Dockerfile` to define the application image, including
     dependencies, application code, and how to run the API server (e.g.,
     `uvicorn`) and the `arq` worker.
   - Consider a `docker-compose.yml` file to orchestrate the application,
     database (e.g., PostgreSQL), and Redis containers for local development and
     testing.

10. **Deployment (Optional):**
    - Choose a deployment strategy (e.g., Serverless, PaaS like Heroku/Render,
      Kubernetes, VMs).
    - Configure environment variables for production settings (database URL,
      secrets, Redis URL).
    - Set up CI/CD pipelines for automated testing and deployment.

## Architecture Notes

- **Technology Stack:** FastAPI, SQLAlchemy (with Alembic for migrations),
  Pydantic, Arq, PostgreSQL, Redis.
- **Structure:** Modular structure separating concerns (routers, crud, models,
  schemas, tasks).
- **Asynchronicity:** Leverage FastAPI's async capabilities for I/O-bound
  operations and `arq` for background task processing.
- **Database:** PostgreSQL is chosen for its robustness and features suitable
  for relational data.
- **Task Queue:** Redis + Arq provide a reliable and efficient mechanism for
  handling background jobs and scheduled tasks like sending reminders.
