# Calls Summary

Phone call recording transcription & summarization SaaS with Electron desktop app.

## Architecture

```
Phone (recording) -> S3 -> Celery Workers -> Deepgram/Claude -> PostgreSQL
                                |
                           FastAPI API (:8001)
                          /              \
                   Electron Desktop    Streamlit UI (:8501)
                   (React+TypeScript)
```

## Tech Stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0 async, Pydantic v2
- **Desktop**: Electron + React + TypeScript + Vite + Tailwind CSS (in `desktop/`)
- **Legacy Frontend**: Streamlit (multi-page)
- **Database**: PostgreSQL 17 (conda local: `C:/Users/zivre/pgdata`, Docker in production)
- **Queue**: Celery + Redis
- **Storage**: AWS S3
- **APIs**: Deepgram Nova-3 (transcription), Claude Haiku 4.5 (summarization + chat), SendGrid (email), Twilio (WhatsApp)
- **Deployment**: Docker Compose on EC2, GitHub Actions CI/CD

## Commands

```bash
# CRITICAL: Load .env vars first (empty ANTHROPIC_API_KEY env var overrides .env)
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Start infrastructure (local dev)
conda run -n calls_summery pg_ctl -D "C:/Users/zivre/pgdata" start
C:\tools\redis\redis-server.exe

# Run backend services (each in separate terminal)
conda run -n calls_summery celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
conda run -n calls_summery uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# Run desktop app
cd desktop && npm run dev

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
├── api/
│   ├── main.py               # FastAPI app
│   └── routes/               # auth, calls, summaries, contacts, actions, chat, settings, notifications, webhooks, api-keys, health
├── models/                   # SQLAlchemy models (user, call, transcription, summary, notification, settings, api_key, contact)
├── schemas/                  # Pydantic request/response schemas
├── repositories/             # Data access layer (base CRUD + per-entity)
├── services/                 # Business logic
│   ├── auth_service.py       # JWT + API key auth
│   ├── call_service.py       # Pipeline orchestration
│   ├── storage_service.py    # S3 operations
│   ├── transcription_service.py  # Deepgram Nova-3
│   ├── summarization_service.py  # Claude API (structured output)
│   ├── contact_service.py    # Contact management + phone matching
│   ├── action_service.py     # Deep link generation (calendar, email, WhatsApp)
│   ├── email_service.py      # SendGrid
│   └── whatsapp_service.py   # Twilio
├── tasks/                    # Celery tasks: transcription -> summarization -> notification
├── config/                   # Settings (Pydantic from .env), logging
└── utils/                    # Validators, formatters, audio utils
desktop/                      # Electron + React + TypeScript desktop app
├── electron/                 # Main process: window, tray, IPC, watcher, uploader
├── src/                      # React app: screens, components, stores, API client
agent/                        # Legacy Python file watcher + S3 uploader
deploy/                       # EC2 setup script
.github/workflows/            # CI (tests) + CD (deploy to EC2)
```

## Key Patterns

- **Immutability**: All service results use `@dataclass(frozen=True)`. Never mutate existing objects.
- **Repository pattern**: Data access behind `BaseRepository` with generic CRUD.
- **Celery task chaining**: `transcribe -> summarize -> notify` (sync tasks, sync DB sessions).
- **Multi-language**: Deepgram auto-detects language, Claude summarizes in user-chosen language (auto/he/en).
- **Electron security**: API keys in main process only, IPC channel whitelist in preload, CSP headers.
- **JWT auto-refresh**: Axios interceptor with single-flight token refresh pattern.

## Pipeline Flow

1. Audio uploaded (manual via desktop/Streamlit, or auto via watcher) -> stored in S3
2. Celery task: S3 presigned URL -> Deepgram transcription (with speaker diarization)
3. Celery task: transcription text + speakers -> Claude API summarization
   - Produces: summary, key_points, action_items, structured_actions, participants_details, topics, sentiment
4. Celery task: summary -> email (SendGrid) / WhatsApp (Twilio) notification
5. Status tracked in DB: `uploaded -> transcribing -> transcribed -> summarizing -> completed`
6. Auto-links calls to contacts via phone numbers extracted from participant details

## Database

PostgreSQL with tables: `users`, `calls`, `transcriptions`, `summaries`, `notifications`, `user_settings`, `api_keys`, `contacts`.
Migrations via Alembic. DB URL: `postgresql+asyncpg://postgres@localhost:5432/calls_summery`

## Important Pitfalls

- **Empty env vars override .env**: pydantic-settings prioritizes env vars. An empty `ANTHROPIC_API_KEY=""` in the shell overrides the real key from `.env`. Always `export $(grep -v '^#' .env | grep -v '^$' | xargs)` before starting services.
- **Celery does NOT hot-reload**: Must restart worker after code changes.
- **Celery retries can corrupt state**: `max_retries=3` with `raise self.retry()` can cause duplicate key errors if task partially succeeds.
- **Worktree .env**: Git worktrees don't share `.env`. Copy from main repo.

## Git Workflow

- Work on `dev` branch (or feature branches off dev)
- Merge to `main` only when ready for production
- GitHub: `Ziv1972/calls_summery`

## Deployment

- **EC2**: Docker Compose (PostgreSQL, Redis, API, Worker, Streamlit)
- **CI**: GitHub Actions runs tests on push to dev/main
- **CD**: GitHub Actions auto-deploys to EC2 on push to main
- **Access**: API docs at `:8001/docs`, Streamlit at `:8501`

## Environment

- Conda environment `calls_summery` (Python 3.11)
- Node.js v24.13.1 (PATH: `C:\Program Files\nodejs`)
- All API keys in `.env` file (never commit)

## Phase Status

- **Phase 1** (Complete): Backend AI - structured actions, contacts, search/filtering, deep links. 242 tests, 90% coverage.
- **Phase 2** (Complete): Electron desktop app - auth, dashboard, calls, chat, contacts, upload, auto-upload, system tray, settings.
- **Phase 3** (Next): Connect phone - full pipeline from call recording to summarization. Options: React Native mobile app OR Android call recorder folder monitoring.
- **Phase 4**: Speaker identification, topic clustering, direct integrations (Google Calendar, Gmail).
- **Phase 5**: Production hardening (rate limiting, monitoring, API versioning).
