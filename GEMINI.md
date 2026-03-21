# Gemini Instructions for CourseVision

This project uses the `google-genai` SDK and Structured Outputs to parse class schedules from images.

## Core Mandates

- **SDK:** Always use the `google-genai` SDK (`from google import genai`).
- **Structured Output:** Use Pydantic models for Gemini responses to ensure reliability.
- **Fallbacks:** Maintain the `generate_with_model_fallback` logic to handle quota issues by switching between available models (e.g., Gemini 2.5 Flash, 2.0 Flash, 3.0 Flash Preview, etc.).
- **Validation:** Always normalize extracted strings (strip whitespace, capitalize days) before saving to the database.

## Environment Variables

The project uses a `.env` file to configure sensitive information and customizable settings.

-   `TELEGRAM_TOKEN`: **Required.** Your Telegram Bot API token, obtained from BotFather.
-   `AUTHORIZED_USER_ID`: **Required.** The numeric user ID of the Telegram user authorized to use the bot.
-   `GEMINI_API_KEY`: **Required.** Your Google Gemini API key.
-   `DATABASE_PATH`: **Optional.** Path to the SQLite database file (default: `database.db`).
-   `GEMINI_MODEL`: **Optional.** Specifies a preferred Gemini model for extraction (e.g., `gemini-2.5-flash`). If not set, the system will attempt to use a list of available flash models.
-   `DEBUG`: **Optional.** Set to `TRUE` to enable debug mode, which will drop and recreate all database tables on every application startup. Useful for development and testing.

## Technical Details

- **Database:** SQLite3. Table `classes` requires `day_index` (0-6).
- **Time Format:** HH:MM. Ensure Gemini extracts or formats it this way.
- **Reminders:** Sent 10 minutes before class. Ensure the `job_queue` is running.

## Development Lifecycle

- **Research:** If extraction fails, check the `prompt` in `main.py` and the `ClassRow` model.
- **Testing:** Use `parsing.py` for standalone testing of the extraction logic without running the full Telegram bot.
