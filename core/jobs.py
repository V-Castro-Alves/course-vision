import logging
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from .database import db_connect
from .i18n import t
from .config import LOCAL_ZONE

logger = logging.getLogger(__name__)


async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()

    # Get current time in the configured timezone
    if LOCAL_ZONE:
        now = datetime.now(tz=LOCAL_ZONE)
    else:
        now = datetime.now()

    # We run this every minute. We look for classes starting in X minutes.
    # To be safe and handle potential small delays, we can look at a 2-minute window.
    # But for simplicity, let's start with exact minute match.

    cur.execute(
        "SELECT telegram_id, reminder_minutes FROM users WHERE reminder_minutes IS NOT NULL"
    )
    users = cur.fetchall()

    for user in users:
        user_id = user["telegram_id"]
        minutes = user["reminder_minutes"]

        # Target time for the class to start
        target_time = now + timedelta(minutes=minutes)
        target_date_iso = target_time.date().isoformat()
        target_time_str = target_time.strftime("%H:%M")

        cur.execute(
            "SELECT * FROM classes WHERE class_date = ? AND start_time = ?",
            (target_date_iso, target_time_str),
        )
        classes = cur.fetchall()

        for cls in classes:
            class_id = cls["id"]

            # Check if already sent
            cur.execute(
                "SELECT 1 FROM sent_reminders WHERE user_id = ? AND class_id = ?",
                (user_id, class_id),
            )
            if cur.fetchone():
                continue

            # Send reminder
            try:
                message = t(
                    "reminder_message",
                    user_id=user_id,
                    subject=cls["subject"],
                    minutes=minutes,
                    room=cls["room"],
                    professor=cls["professor"],
                )
                await context.bot.send_message(
                    chat_id=user_id, text=message, parse_mode="Markdown"
                )

                # Mark as sent
                cur.execute(
                    "INSERT INTO sent_reminders (user_id, class_id) VALUES (?, ?)",
                    (user_id, class_id),
                )
                conn.commit()
                logger.info(f"Sent reminder to {user_id} for class {class_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {user_id}: {e}")

    conn.close()
