# TaskBoards Backend - Database Setup

This backend uses SQLAlchemy with Alembic migrations. To allow the app to start without a database, the DB engine is initialized lazily. Until you set the DATABASE_URL environment variable, all DB-backed endpoints will return HTTP 503, while health endpoints continue to work.

Follow these steps when you're ready to configure the database.

## 1. Environment Variables

Copy `.env.example` to `.env` and fill the placeholders. At minimum, set:

- DATABASE_URL: SQLAlchemy URL (e.g., `postgresql+psycopg://user:pass@localhost:5432/taskboards`)
- SECRET_KEY: a strong secret for JWT signing
- ACCESS_TOKEN_EXPIRE_MINUTES: e.g., 60
- CORS_ALLOW_ORIGINS: comma-separated list (e.g., `http://localhost:3000`)
- WEBSOCKET_ORIGINS: optional; origins allowed for websockets

The app reads environment variables via `os.environ`. Ensure your process manager or shell exports them.

## 2. Database Options

Below are common options for local development.

### Option A: Homebrew Postgres (macOS)

1. Install Postgres:
   brew install postgresql
   brew services start postgresql

2. Create DB and user:
   createdb taskboards
   createuser taskboards_user --pwprompt
   # set a password when prompted

3. Grant privileges:
   psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE taskboards TO taskboards_user;"

4. Set DATABASE_URL:
   export DATABASE_URL="postgresql+psycopg://taskboards_user:<password>@localhost:5432/taskboards"

5. Verify connection:
   psql "$DATABASE_URL" -c '\conninfo'

### Option B: Docker Postgres

1. Start Postgres container:
   docker run --name taskboards-postgres -e POSTGRES_USER=taskboards_user -e POSTGRES_PASSWORD=taskboards_pass -e POSTGRES_DB=taskboards -p 5432:5432 -d postgres:16

2. Set DATABASE_URL:
   export DATABASE_URL="postgresql+psycopg://taskboards_user:taskboards_pass@localhost:5432/taskboards"

## 3. Run Alembic Migrations

Alembic is configured in `alembic.ini` and `alembic/env.py`. It will use `DATABASE_URL` if provided.

- Upgrade to latest:
  cd taskboards_backend
  alembic upgrade head

- Generate a new migration after model changes:
  alembic revision --autogenerate -m "describe changes"
  alembic upgrade head

If you need to override the URL explicitly:
  DATABASE_URL="..." alembic upgrade head

## 4. Start the Backend

Ensure environment variables are set and start the FastAPI app (example with uvicorn):

  uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Health endpoint:
  GET / -> {"message": "Healthy"}

Status endpoint:
  GET /status -> {"dbConfigured": true|false}

When `dbConfigured` is false, DB-backed endpoints will return 503 with message:
  "Database not configured. Set DATABASE_URL. See .env.example"

## 5. Troubleshooting

- 503 on DB routes: Check that `DATABASE_URL` is exported and reachable, then restart the app.
- Alembic URL: Ensure `DATABASE_URL` is set or specify `-x` options/override `sqlalchemy.url` in `alembic.ini` if needed.
- Psycopg binary: This project uses `psycopg[binary]`. If you need the C extension, install `psycopg[c]` instead and update requirements accordingly.
