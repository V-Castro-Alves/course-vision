# Architecture

**Analysis Date:** 2026-03-24

## Pattern Overview

**Overall:** Telegram Bot with Modular Design

**Key Characteristics:**
- **Event-Driven:** Responds to user commands and messages via Telegram API.
- **Handler-Based:** Logic is organized into specific handler functions for different bot commands/message types.
- **Separation of Concerns:** Distinct modules for configuration, database, internationalization, and handler logic.

## Layers

**Entry Layer:**
- Purpose: Initializes the Telegram bot application, registers handlers, and starts the polling mechanism.
- Location: `core/main.py`
- Contains: Application setup, handler registrations.
- Depends on: `telegram.ext` library, `core/config.py`, `core/database.py`, `core/i18n.py`, `core/handlers.py`.
- Used by: Directly executed as the application's starting point.

**Handlers Layer:**
- Purpose: Contains the business logic for specific Telegram commands and message types. These functions are called by the Telegram bot framework when a matching event occurs.
- Location: `core/handlers.py`
- Contains: Functions like `start`, `set_language`, `upload_command`, `photo_upload`, etc.
- Depends on: `telegram.ext` (for context and update objects), `core/database.py`, `core/i18n.py`, `core/parsing.py`, potentially external APIs.
- Used by: `core/main.py` (for registration).

**Configuration Layer:**
- Purpose: Manages application settings, primarily environment variables.
- Location: `core/config.py`
- Contains: Variables like `TELEGRAM_TOKEN`.
- Depends on: `python-dotenv`.
- Used by: `core/main.py` and other modules requiring configuration.

**Database Layer:**
- Purpose: Handles database initialization and interactions (e.g., storing user data, scheduling information).
- Location: `core/database.py`
- Contains: `init_db()` function, likely database models/schemas.
- Depends on: Database client library (not explicitly seen, but implied by `init_db`).
- Used by: `core/main.py`, `core/handlers.py`.

**Internationalization (i18n) Layer:**
- Purpose: Provides multi-language support for bot responses.
- Location: `core/i18n.py`, `core/responses.json`
- Contains: Functions to load and retrieve localized messages.
- Depends on: `core/responses.json`.
- Used by: `core/main.py` (initialization), `core/handlers.py`.

**Utility/Parsing Layer:**
- Purpose: Contains helper functions for parsing complex messages or performing utility operations.
- Location: `core/parsing.py`
- Contains: Functions for specific data extraction or processing.
- Depends on: Standard Python libraries, possibly `pytesseract` for OCR.
- Used by: `core/handlers.py`.

## Data Flow

**Telegram Bot Interaction:**

1. **User sends message/command:** Telegram servers receive user input.
2. **Telegram API sends update:** The `python-telegram-bot` library (running in `core/main.py`) receives updates via polling.
3. **Dispatcher identifies handler:** The `ApplicationBuilder` dispatches the update to the appropriate handler function registered in `core/main.py` (e.g., `start`, `photo_upload`).
4. **Handler logic executes:** The function in `core/handlers.py` performs its task, which may involve:
    - Reading/writing to the database via `core/database.py`.
    - Fetching configuration from `core/config.py`.
    - Retrieving localized responses from `core/i18n.py`.
    - Processing data using `core/parsing.py` or external APIs (e.g., Google GenAI).
5. **Bot sends response:** The handler constructs and sends a response back to the user via the Telegram API.

**State Management:**
- Application state is managed implicitly through the Telegram bot's context objects and explicitly through database interactions (e.g., `core/database.py` for persistent user data or schedules).

## Key Abstractions

**Telegram Bot API Wrapper (`python-telegram-bot`):**
- Purpose: Provides a high-level interface to the Telegram Bot API.
- Examples: `ApplicationBuilder`, `CommandHandler`, `MessageHandler`, `CallbackQueryHandler`.
- Pattern: Object-oriented wrapper over a remote API.

**Custom Handler Functions:**
- Purpose: Encapsulate specific bot behaviors for different user inputs.
- Examples: `core/handlers.py` functions like `start`, `upload_command`, `attendance_callback`.
- Pattern: Callback functions that receive `Update` and `Context` objects.

## Entry Points

**Application Entry:**
- Location: `main.py` (delegates to `core/main.py`)
- Triggers: Execution of the Python script (e.g., `python main.py`).
- Responsibilities: Bootstrap the entire application, initialize core components, and start the bot's polling loop.

## Error Handling

**Strategy:** Not explicitly defined as a global strategy, but individual handlers in `core/handlers.py` would typically contain `try-except` blocks for specific error scenarios. The `python-telegram-bot` library also provides error handling mechanisms.

**Patterns:**
- Per-handler error management.
- Implicit error handling by the `python-telegram-bot` framework for API issues.

## Cross-Cutting Concerns

**Logging:**
- Approach: Not explicitly configured in the provided snippets. Standard Python `print()` statements are used in `core/main.py` ("Bot iniciado."). The `python-telegram-bot` library likely uses its own logging. A dedicated logging setup is not evident.

**Validation:**
- Approach: Pydantic is listed in `requirements.txt`, suggesting data validation is performed, likely for incoming data models or configuration. Specific usage not observed in `core/main.py`.
- Files: `requirements.txt` (implies usage), likely in models or parsing logic not directly shown.

**Authentication:**
- Approach: Handled by Telegram's token-based authentication for the bot itself (`TELEGRAM_TOKEN` in `core/config.py`). User authentication within the bot is likely session-based or through user IDs provided by Telegram.

---

*Architecture analysis: 2026-03-24*
