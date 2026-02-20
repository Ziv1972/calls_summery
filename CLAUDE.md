# Calls Summary

Phone call recording transcription & summarization app with auto-upload.

## Architecture

Hybrid: local agent (watchdog) auto-uploads recordings to S3, cloud backend processes everything.
Deployed on AWS EC2 via Docker Compose with CI/CD auto-deploy on push to main.

```
User/Agent -> FastAPI -> Celery Workers -> Deepgram/Claude/SendGrid
                |              |
           Streamlit UI    PostgreSQL + Redis
                |
            AWS S3 (audio storage)
```

## Tech Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0 async, Pydantic v2
- **Frontend**: Streamlit (multi-page)
- **Database**: PostgreSQL 17 (conda local: `C:/Users/zivre/pgdata`, Docker in production)
- **Queue**: Celery + Redis
- **Storage**: AWS S3
- **APIs**: Deepgram (transcription), Claude Haiku 4.5 (summarization), SendGrid (email), Twilio (WhatsApp)
- **Deployment**: Docker Compose on EC2, GitHub Actions CI/CD

## Commands

```bash
# Start infrastructure (local dev)
conda run -n calls_summery pg_ctl -D "C:/Users/zivre/pgdata" start
C:\tools\redis\redis-server.exe

# Run services (each in separate terminal)
conda run -n calls_summery celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
conda run -n calls_summery uvicorn src.api.main:app --reload
conda run -n calls_summery streamlit run src/app.py

# Or use scripts
start.bat    # Start PostgreSQL + Redis
stop.bat     # Stop all

# Tests
conda run -n calls_summery python -m pytest tests/unit -v
conda run -n calls_summery python -m pytest tests/unit --cov=src --cov-report=term

# Database migrations
conda run -n calls_summery alembic upgrade head
conda run -n calls_summery alembic revision --autogenerate -m "description"

# Deploy to EC2 (auto on push to main)
git checkout main && git merge dev && git push
```

## Project Structure

```
src/
├── app.py                    # Streamlit entry point
├── pages/                    # Streamlit pages (auth, upload, calls, summary, settings, notifications, api keys)
├── api/
│   ├── main.py               # FastAPI app
│   └── routes/               # auth, calls, summaries, settings, notifications, webhooks, api-keys, health
├── models/                   # SQLAlchemy models (user, call, transcription, summary, notification, settings, api_key)
├── schemas/                  # Pydantic request/response schemas
├── repositories/             # Data access layer (base CRUD + per-entity)
├── services/                 # Business logic
│   ├── auth_service.py       # JWT + API key auth
│   ├── call_service.py       # Pipeline orchestration
│   ├── storage_service.py    # S3 operations
│   ├── transcription_service.py  # Deepgram
│   ├── summarization_service.py  # Claude API
│   ├── email_service.py      # SendGrid
│   └── whatsapp_service.py   # Twilio
├── tasks/                    # Celery async tasks (transcription -> summarization -> notification)
├── config/                   # Settings (Pydantic from .env), logging
└── utils/                    # Validators, formatters, audio utils
agent/                        # Local file watcher + S3 uploader
deploy/                       # EC2 setup script
.github/workflows/            # CI (tests) + CD (deploy to EC2)
```

## Key Patterns

- **Immutability**: All service results use `@dataclass(frozen=True)`. Never mutate existing objects.
- **Repository pattern**: Data access behind `BaseRepository` with generic CRUD.
- **Celery task chaining**: `transcribe -> summarize -> notify` (sync tasks, sync DB sessions).
- **Multi-language**: Deepgram auto-detects language, Claude summarizes in user-chosen language (auto/he/en).

## Pipeline Flow

1. Audio uploaded (manual via Streamlit or auto via agent) -> stored in S3
2. Celery task: S3 presigned URL -> Deepgram transcription (polling)
3. Celery task: transcription text -> Claude API summarization
4. Celery task: summary -> email (SendGrid) / WhatsApp (Twilio)
5. Status tracked in DB: `uploaded -> transcribing -> transcribed -> summarizing -> completed`

## Database

PostgreSQL with tables: `users`, `calls`, `transcriptions`, `summaries`, `notifications`, `user_settings`, `api_keys`.
Migrations via Alembic. DB URL: `postgresql+asyncpg://postgres@localhost:5432/calls_summery`

## Deployment

- **EC2**: Docker Compose (PostgreSQL, Redis, API, Worker, Streamlit)
- **CI**: GitHub Actions runs tests on push to dev/main
- **CD**: GitHub Actions auto-deploys to EC2 on push to main
- **Access**: UI at `:8501`, API docs at `:8001/docs`

## Environment

Conda environment `calls_summery` (Python 3.11). All API keys in `.env` file (never commit).
