import html
import json
import traceback
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .config import TELEGRAM_TOKEN, AUTHORIZED_USER_ID, logger
from .database import init_db
from .i18n import load_responses
from .handlers import (
    start,
    set_language,
    setlang_callback,
    set_reminder,
    upload_command,
    schedule_text,
    today_classes,
    photo_upload,
    confirm_schedule_processing,  # Added
    handle_unknown_text,
    attendance_callback,
)
from .jobs import send_reminders


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks here.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python traceback list of strings
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some simplified context about the update.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message to the developer
    try:
        await context.bot.send_message(
            chat_id=AUTHORIZED_USER_ID, text=message, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send error message to authorized user: {e}")


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
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_text)
    )
    app.add_handler(
        CallbackQueryHandler(confirm_schedule_processing, pattern="^process_schedule:")
    )  # Added
    app.add_handler(CallbackQueryHandler(setlang_callback, pattern="^setlang:"))
    app.add_handler(CallbackQueryHandler(attendance_callback))

    # Error Handler
    app.add_error_handler(error_handler)

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
