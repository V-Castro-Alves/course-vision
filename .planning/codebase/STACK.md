# Technology Stack

**Analysis Date:** 2024-07-29

## Languages

**Primary:**
- Python 3.9+ - Core application logic, bot handling, API interactions.

## Runtime

**Environment:**
- Python 3.9+

**Package Manager:**
- pip - Used for dependency management.
- Lockfile: `requirements.txt` (lists direct dependencies)

## Frameworks

**Core:**
- python-telegram-bot 22.7 - Framework for building the Telegram bot.
- APScheduler 3.11.2 - Used for scheduling tasks.
- Pydantic 2.12.5 - Data validation and settings management.

**Testing:**
- Not detected

**Build/Dev:**
- python-dotenv 1.2.2 - For loading environment variables from `.env` files.

## Key Dependencies

**Critical:**
- google-genai 1.68.0 - Interacting with Google's Gemini AI models for content generation/analysis.
- httpx 0.28.1 - Asynchronous HTTP client for making web requests.
- requests 2.32.5 - Synchronous HTTP client.

**Infrastructure:**
- cffi 2.0.0, cryptography 46.0.5, pycparser 3.0 - Cryptographic operations, likely dependencies of other packages.

## Configuration

**Environment:**
- Configured via environment variables loaded from `.env` files using `python-dotenv`.
- Access via `os.getenv()`.

**Build:**
- `requirements.txt` specifies Python package dependencies.

## Platform Requirements

**Development:**
- Python 3.9+ interpreter.
- `pip` for package installation.

**Production:**
- Linux-based environment (common for Python applications).

---

*Stack analysis: 2024-07-29*
