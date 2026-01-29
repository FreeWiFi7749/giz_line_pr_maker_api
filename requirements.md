# PR Maker API Requirements

## Overview
FastAPI backend for managing LINE Flex Message PR bubbles for giz_line_bot digest delivery.

## Data Model

### PRBubble Table
- id: UUID (primary key)
- title: VARCHAR(40) - max 40 characters
- description: VARCHAR(100) - max 100 characters
- image_url: VARCHAR(500)
- link_url: VARCHAR(500)
- tag_type: ENUM('gizmart', 'custom')
- tag_text: VARCHAR(50)
- tag_color: VARCHAR(7) - HEX color
- start_date: TIMESTAMP
- end_date: TIMESTAMP
- priority: INTEGER (nullable)
- status: ENUM('draft', 'active', 'inactive')
- utm_campaign: VARCHAR(100) (nullable)
- view_count: INTEGER (default 0)
- click_count: INTEGER (default 0)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

## API Endpoints

### Management (Cloudflare Access auth)
- GET /api/pr - List PRs with pagination and status filter
- GET /api/pr/{id} - Get PR details
- POST /api/pr - Create PR
- PUT /api/pr/{id} - Update PR
- DELETE /api/pr/{id} - Delete PR
- POST /api/pr/{id}/duplicate - Duplicate PR
- GET /api/pr/{id}/stats - Get PR statistics

### giz_line_bot Integration (API Key auth)
- GET /api/pr/active - Get currently active PRs
- POST /api/pr/{id}/track - Record view/click

### Image Upload
- POST /api/upload/image - Upload image to Cloudflare R2

## Authentication
- Management endpoints: Cloudflare Access (JWT validation)
- Bot integration: X-API-Key header

## Environment Variables
- DATABASE_URL: PostgreSQL connection string
- R2_ACCOUNT_ID: Cloudflare R2 account ID
- R2_ACCESS_KEY_ID: R2 access key
- R2_SECRET_ACCESS_KEY: R2 secret key
- R2_BUCKET_NAME: R2 bucket name
- R2_PUBLIC_URL: R2 public URL
- API_KEY: giz_line_bot API key
- SECRET_KEY: Application secret
- ALLOWED_ORIGINS: CORS allowed origins
