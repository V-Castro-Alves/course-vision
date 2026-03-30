from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import TELEGRAM_TOKEN, logger
from .database import init_db
from .i18n import load_responses
from .handlers import (
    start,
    set_language,
    upload_command,
    schedule_text,
    today_classes,
    photo_upload,
    confirm_schedule_processing,  # Added
    attendance_callback,
)


def main():
    load_responses()
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("schedule", schedule_text))
    app.add_handler(CommandHandler("today", today_classes))
    app.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo_upload)
    )
    app.add_handler(
        CallbackQueryHandler(confirm_schedule_processing, pattern="^process_schedule:")
    )  # Added
    app.add_handler(CallbackQueryHandler(attendance_callback))

    logger.info("Bot iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
