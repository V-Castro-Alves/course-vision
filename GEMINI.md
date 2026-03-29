# Gemini Instructions for CourseVision

This project uses the `google-genai` SDK and Structured Outputs to parse class schedules from images.

## Core Mandates

- **SDK:** Always use the `google-genai` SDK (`from google import genai`).
- **Structured Output:** Use Pydantic models for Gemini responses to ensure reliability. The `ClassRow` model now focuses on extracting `class_code`, `class_name`, `professor`, and `classroom`. Day and date information is assigned deterministically after extraction.
- **Fallbacks:** Maintain the `generate_with_model_fallback` logic to handle quota issues by switching between available models (e.g., Gemini 2.5 Flash, 2.0 Flash, 3.0 Flash Preview, etc.).
- **Validation:** Always normalize extracted strings (strip whitespace, capitalize days) before saving to the database.
- **Documentation Updates:** When updating user-facing documentation (e.g., `README.md`), ensure all language versions (English and Portuguese) are updated consistently.

## Environment Variables

The project uses a `.env` file to configure sensitive information and customizable settings.

-   `TELEGRAM_TOKEN`: **Required.** Your Telegram Bot API token, obtained from BotFather.
-   `AUTHORIZED_USER_ID`: **Required.** The numeric user ID of the Telegram user authorized to use the bot.
-   `GEMINI_API_KEY`: **Required.** Your Google Gemini API key.
-   `DATABASE_PATH`: **Optional.** Path to the SQLite database file (default: `database.db`).
-   `GEMINI_MODEL`: **Optional.** Specifies a preferred Gemini model for extraction (e.g., `gemini-2.5-flash`). If not set, the system will attempt to use a list of available flash models.


## Technical Details

- **Database:** SQLite3.
    -   Table `classes` now includes `day_index` (0-6, where 0 is Monday) and `class_date` (YYYY-MM-DD).
    -   When a schedule image is uploaded, existing classes for the *current week* (Monday to Friday) are deleted, and new classes are added.
    -   Date assignment is deterministic: the first two extracted classes are assigned to Monday of the current week, the next two to Tuesday, and so on, up to Friday.
- **Time Format:** Time extraction has been removed from Gemini's parsing.

## Bot Commands

-   `/upload`: Initiates the process to send a schedule image for parsing.
- `/schedule`: Displays all classes for the current week (Monday to Friday) in pt-br, with dates formatted as DD/MM and enhanced display.
- `/today`: Displays only the classes scheduled for the current day in pt-br, with dates formatted as DD/MM and enhanced display.
-   `/add_exam YYYY-MM-DD Subject [notes]`: Adds an exam to the schedule.
-   `/exams`: Lists all scheduled exams.

## Development Lifecycle

- **Research:** If extraction fails, check the `prompt` in `main.py` and the `ClassRow` model.
- **Testing:** Use `parsing.py` for standalone testing of the extraction logic without running the full Telegram bot.
- **Testing Workflow:** When implementing new features, prioritize targeted local checks and rely on GitHub Actions for the full CI suite.

- **Test-Driven Development (TDD):** For any new feature or significant change, write tests *before* writing the implementation code.
