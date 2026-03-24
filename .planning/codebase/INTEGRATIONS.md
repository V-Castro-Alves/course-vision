# External Integrations

**Analysis Date:** 2024-07-29

## APIs & External Services

**Messaging Platform:**
- Telegram Bot API - Used for all bot interactions (sending/receiving messages, handling commands, callbacks).
  - SDK/Client: `python-telegram-bot`
  - Auth: `TELEGRAM_TOKEN` (environment variable)

**Artificial Intelligence:**
- Google Gemini API - Used for AI model interactions, potentially for text generation or analysis.
  - SDK/Client: `google-genai`
  - Auth: `GEMINI_API_KEY` (environment variable)

## Data Storage

**Databases:**
- SQLite (local file-based)
  - Connection: `DATABASE_PATH` (environment variable, defaults to `database.db`)
  - Client: Not explicitly defined (likely uses Python's built-in `sqlite3` module or an ORM that abstracts it)

**File Storage:**
- Local filesystem only - For `database.db` and other local files.

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- Custom / Telegram's user IDs
  - Implementation: `TELEGRAM_TOKEN` for bot authentication, `AUTHORIZED_USER_ID` and `ALLOWED_TELEGRAM_IDS` for controlling access to bot functionalities.

## Monitoring & Observability

**Error Tracking:**
- None detected (basic logging with `logging` module is present).

**Logs:**
- Standard Python `logging` module outputting to console (configured via `basicConfig` in `core/config.py`).

## CI/CD & Deployment

**Hosting:**
- Not explicitly defined, likely self-hosted or containerized.

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- `TELEGRAM_TOKEN`: Telegram Bot API token.
- `AUTHORIZED_USER_ID`: ID of the main authorized user.
- `ALLOWED_TELEGRAM_IDS`: Comma-separated list of additional authorized user IDs.
- `GEMINI_API_KEY`: API key for Google Gemini.
- `DATABASE_PATH`: Path to the SQLite database file.
- `GEMINI_MODEL`: Specific Gemini model to use (e.g., `gemini-2.5-flash`).
- `TIMEZONE`: Timezone for scheduled tasks (e.g., `America/Sao_Paulo`).

**Secrets location:**
- `.env` file (for local development/deployment).

## Webhooks & Callbacks

**Incoming:**
- Telegram Bot API webhooks/polling handled by `python-telegram-bot`.

**Outgoing:**
- None detected explicitly, but `httpx` and `requests` could be used for arbitrary external calls.

---

*Integration audit: 2024-07-29*
