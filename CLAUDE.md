# Calls Summary

Phone call recording transcription & summarization app with auto-upload.

## Architecture

Hybrid: local agent (watchdog) auto-uploads recordings to S3, cloud backend processes everything.

```
Local Agent (watchdog) -> S3 -> FastAPI -> Celery Workers -> Deepgram/Claude/SendGrid
                                            |
                                      Streamlit UI
```

## Tech Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0 async, Pydantic v2
- **Frontend**: Streamlit (multi-page)
- **Database**: PostgreSQL 17 (conda, data at `C:/Users/zivre/pgdata`)
- **Queue**: Celery + Redis (`C:\tools\redis\redis-server.exe`)
- **Storage**: AWS S3
- **APIs**: Deepgram (transcription), Claude Haiku 4.5 (summarization), SendGrid (email), Twilio (WhatsApp)

## Commands

```bash
# Start infrastructure
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
```

## Project Structure

```
src/
├── app.py                    # Streamlit entry point
├── pages/                    # Streamlit pages (upload, calls, summary, settings)
├── api/
│   ├── main.py               # FastAPI app
│   └── routes/               # calls, summaries, webhooks, health
├── models/                   # SQLAlchemy models (call, transcription, summary, notification, settings)
├── schemas/                  # Pydantic request/response schemas
├── repositories/             # Data access layer (base CRUD + per-entity)
├── services/                 # Business logic
│   ├── call_service.py       # Pipeline orchestration
│   ├── storage_service.py    # S3 operations
│   ├── transcription_service.py  # Deepgram
│   ├── summarization_service.py  # Claude API
│   ├── email_service.py      # SendGrid
│   └── whatsapp_service.py   # Twilio (Phase 2)
├── tasks/                    # Celery async tasks (transcription -> summarization -> notification)
├── config/                   # Settings (Pydantic from .env), logging
└── utils/                    # Validators, formatters, audio utils
agent/                        # Local file watcher + S3 uploader
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

PostgreSQL with tables: `calls`, `transcriptions`, `summaries`, `notifications`, `user_settings`.
Migrations via Alembic. DB URL: `postgresql+asyncpg://postgres@localhost:5432/calls_summery`

## Environment

Conda environment `calls_summery` (Python 3.11). All API keys in `.env` file (never commit).
