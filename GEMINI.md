# Gemini Instructions for CourseVision

This project uses the `google-genai` SDK and Structured Outputs to parse class schedules from images.

## Core Mandates

- **SDK:** Always use the `google-genai` SDK (`from google import genai`).
- **Structured Output:** Use Pydantic models for Gemini responses to ensure reliability.
- **Fallbacks:** Maintain the `generate_with_model_fallback` logic to handle quota issues by switching between available models (e.g., Gemini 2.5 Flash, 2.0 Flash, 3.0 Flash Preview, etc.).
- **Validation:** Always normalize extracted strings (strip whitespace, capitalize days) before saving to the database.

## Technical Details

- **Database:** SQLite3. Table `classes` requires `day_index` (0-6).
- **Time Format:** HH:MM. Ensure Gemini extracts or formats it this way.
- **Reminders:** Sent 10 minutes before class. Ensure the `job_queue` is running.

## Development Lifecycle

- **Research:** If extraction fails, check the `prompt` in `main.py` and the `ClassRow` model.
- **Testing:** Use `parsing.py` for standalone testing of the extraction logic without running the full Telegram bot.
