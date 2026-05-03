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
    set_reminder,
    upload_command,
    schedule_text,
    today_classes,
    photo_upload,
    confirm_schedule_processing,  # Added
    attendance_callback,
)
from .jobs import send_reminders


def main():
    load_responses()
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("setlang", set_language))
    app.add_handler(CommandHandler("remind", set_reminder))
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

    # Job Queue
    if app.job_queue:
        app.job_queue.run_repeating(send_reminders, interval=60, first=10)
        logger.info("Job queue iniciado.")
    else:
        logger.warning("Job queue não disponível. Lembretes não funcionarão.")

    logger.info("Bot iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
