# Gemini Instructions for CourseVision

This project uses the `google-genai` SDK and Structured Outputs to parse class schedules from images.

## Security Mandates

- **Environment Variables:** NEVER read the content of the `.env` file or directly access environment variables. Assume they are properly configured in the execution environment.

## Core Mandates

- **SDK:** Always use the `google-genai` SDK (`from google import genai`).
- **Structured Output:** Use Pydantic models for Gemini responses to ensure reliability. The `ClassRow` model now focuses on extracting `class_code`, `class_name`, `professor`, and `classroom`. Day and date information is assigned deterministically after extraction.
- **Fallbacks:** Maintain the `generate_with_model_fallback` logic to handle quota issues by switching between available models (e.g., Gemini 2.5 Flash, 2.0 Flash). The list of candidates is managed in `core/config.py`.
- **Validation:** Always normalize extracted strings (strip whitespace, capitalize days) before saving to the database.
- **Resilience & Resource Management:**
    - **Resource Safety:** ALWAYS use `contextlib.closing` with database connections to guarantee they are closed, preventing locks and resource leaks.
    - **Isolation:** Background jobs MUST implement internal `try...except...finally` blocks. Errors in jobs should never propagate to the main application.
    - **Global Error Handling:** Maintain a global error handler to capture and report uncaught exceptions to the `AUTHORIZED_USER_ID`.
- **Documentation Updates:** When a new feature is successfully implemented, ALWAYS update the `README.md` (and any other relevant documentation) to reflect the new functionality.
- **Bilingual Consistency:** When updating user-facing documentation (e.g., `README.md`), ensure all language versions (English and Portuguese) are updated consistently.

## Environment Variables

The project uses a `.env` file to configure sensitive information and customizable settings.

-   `TELEGRAM_TOKEN`: **Required.** Your Telegram Bot API token, obtained from BotFather.
-   `AUTHORIZED_USER_ID`: **Required.** The numeric user ID of the Telegram user authorized to use all commands.
-   `ALLOWED_TELEGRAM_IDS`: **Optional.** A comma-separated list of additional Telegram user IDs allowed to use the bot.
-   `GEMINI_API_KEY`: **Required.** Your Google Gemini API key.
-   `DATABASE_PATH`: **Optional.** Path to the SQLite database file (default: `database.db`).
-   `GEMINI_MODEL`: **Optional.** Specifies a preferred Gemini model for extraction (e.g., `gemini-2.0-flash`).
-   `TIMEZONE`: **Optional.** The timezone for date calculations (default: `UTC`).
-   `RESPONSES_PATH`: **Optional.** Path to the `responses.json` file.


## Technical Details

- **Database:** SQLite3.
    -   **Path Management:** `DATABASE_PATH` must be absolute (handled in `core/config.py`) to ensure consistency between the main application and background threads/jobs.
    -   Table `classes` includes `day_index` (0-6, where 0 is Monday), `class_date` (YYYY-MM-DD), `start_time`, and `end_time`.
    -   Table `attendance` tracks class presence (`attended`, `skipped`).
    -   When a schedule image is uploaded, existing classes for the *current week* (Monday to Friday) are deleted, and new classes are added.
    -   Date assignment is deterministic: classes are assigned sequentially from Monday to Friday (2 per day logic).
- **Time Format:** Time extraction is NOT performed by Gemini; it is assigned deterministically (1st class: 19:00-20:30, 2nd class: 20:50-22:30).
- **I18n:** Multi-language support (English and Portuguese) is managed via `core/responses.json` and the `t()` function.

## Bot Commands

-   `/start` / `/help`: Displays the welcome message and available commands.
-   `/setlang pt-br|en`: Changes the user's language preference.
-   `/upload`: Explains how to send a schedule image for parsing.
-   `/schedule`: Displays all classes for the current week (Monday to Friday).
-   `/today`: Displays classes scheduled for the current day.
-   **Automatic Detection:** Sending a photo or image document directly (without a command) triggers a confirmation prompt to process the schedule.

## Development Lifecycle

- **Research:** If extraction fails, check the `prompt` in `core/handlers.py` and the `ClassRow` model in `core/parsing.py`.
- **Testing Workflow:** ALWAYS run tests using the Docker Compose setup defined in `docker-compose.ci.yml`, as in the CI. Local checks should match the CI environment.
  - Ensure all CI checks (Ruff, pip-audit, Bandit) pass before finalizing changes.
- **Test-Driven Development (TDD):** Write tests *before* implementation for any new feature.
- **Test Management:** NEVER edit or remove existing tests; always add new ones to cover new functionality or bugs.
- **ROADMAP.md Update:** Move completed tasks to the 'DONE' section after successful implementation.
