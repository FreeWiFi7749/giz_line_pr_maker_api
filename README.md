# PR Maker API

FastAPI backend for managing LINE Flex Message PR bubbles for giz_line_bot digest delivery.

## Features

- CRUD operations for PR bubbles
- Image upload to Cloudflare R2
- Active PR retrieval for giz_line_bot integration
- View/click tracking for analytics
- Cloudflare Access authentication for management
- API key authentication for bot integration

## Tech Stack

- FastAPI
- PostgreSQL (async with asyncpg)
- SQLAlchemy 2.0
- Pydantic v2
- Cloudflare R2 (S3-compatible storage)
- Poetry for dependency management

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

## API Endpoints

### Management (Cloudflare Access auth)
- `GET /api/pr` - List PRs with pagination and status filter
- `GET /api/pr/{id}` - Get PR details
- `POST /api/pr` - Create PR
- `PUT /api/pr/{id}` - Update PR
- `DELETE /api/pr/{id}` - Delete PR
- `POST /api/pr/{id}/duplicate` - Duplicate PR
- `GET /api/pr/{id}/stats` - Get PR statistics
- `POST /api/upload/image` - Upload image to R2

### giz_line_bot Integration (API Key auth)
- `GET /api/pr/active` - Get currently active PRs
- `POST /api/pr/{id}/track` - Record view/click

### Health
- `GET /api/health` - Health check
- `GET /api/readiness` - Readiness check

## Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | Application secret |
| R2_ACCOUNT_ID | Cloudflare R2 account ID |
| R2_ACCESS_KEY_ID | R2 access key |
| R2_SECRET_ACCESS_KEY | R2 secret key |
| R2_BUCKET_NAME | R2 bucket name |
| R2_PUBLIC_URL | R2 public URL |
| API_KEY | API key for bot integration |
| ALLOWED_ORIGINS | CORS allowed origins |
| CF_ACCESS_TEAM_DOMAIN | Cloudflare Access team domain |
| CF_ACCESS_AUDIENCE | Cloudflare Access audience tag |

## Deployment

Deploy to Railway with the following configuration:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```
