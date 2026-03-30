import os
import re
import sqlite3

from telegram import Update
from telegram.ext import ContextTypes

from .config import AUTHORIZED_USER_ID, ALLOWED_TELEGRAM_IDS, DATABASE_PATH

SQL_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE NOT NULL, lang TEXT DEFAULT 'en')",
    "CREATE TABLE IF NOT EXISTS raw_images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mime_type TEXT, image_blob BLOB, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, day_index INTEGER NOT NULL, class_date TEXT NOT NULL, start_time TEXT, end_time TEXT, subject TEXT NOT NULL, room TEXT NOT NULL, professor TEXT NOT NULL, code TEXT NOT NULL, raw TEXT NOT NULL, source_image_id INTEGER, FOREIGN KEY(source_image_id) REFERENCES raw_images(id))",
    "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, class_id INTEGER NOT NULL, class_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('attended','skipped')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
]


def db_connect():
    database_path = os.getenv("DATABASE_PATH", DATABASE_PATH)
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def drop_all_tables():
    conn = db_connect()
    cur = conn.cursor()
    table_names = []
    for stmt in SQL_SCHEMA:
        match = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", stmt)
        if match:
            table_names.append(match.group(1))

    for table_name in reversed(table_names):
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()


def init_db():
    conn = db_connect()
    cur = conn.cursor()
    for stmt in SQL_SCHEMA:
        cur.execute(stmt)

    # Migration: add start_time and end_time if they don't exist
    cur.execute("PRAGMA table_info(classes)")
    columns = [column[1] for column in cur.fetchall()]
    if "start_time" not in columns:
        cur.execute("ALTER TABLE classes ADD COLUMN start_time TEXT")
    if "end_time" not in columns:
        cur.execute("ALTER TABLE classes ADD COLUMN end_time TEXT")

    conn.commit()
    conn.close()


def get_user_lang(
    update: Update = None,
    context: ContextTypes.DEFAULT_TYPE = None,
    user_id: int = None,
) -> str:
    # First, try to get user_id if not provided
    if user_id is None:
        if update and update.effective_user:
            user_id = update.effective_user.id
        elif (
            not context and not update
        ):  # If no update and no context, we have no user info
            return "en"  # Default to English early

    # Try to get language from context.user_data first (if context is available)
    if (
        context
        and hasattr(context, "user_data")
        and isinstance(context.user_data, dict)
        and context.user_data.get("lang")
    ):
        return context.user_data["lang"]

    # If user_id is still None at this point, it means neither update.effective_user nor
    # an explicit user_id was provided, and context.user_data didn't have a lang.
    # In this specific scenario, we must return a default as we can't query the DB.
    if (
        user_id is None
    ):  # This could happen if only context was available but no user_data.lang
        return "en"

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE telegram_id = ?", (user_id,))
    user_row = cur.fetchone()
    if not user_row:
        cur.execute("INSERT INTO users (telegram_id) VALUES (?)", (user_id,))
        conn.commit()
        lang = "en"
    else:
        lang = user_row["lang"]
    if (
        context
        and hasattr(context, "user_data")
        and isinstance(context.user_data, dict)
    ):  # Only set in user_data if context is available and user_data is a dict
        context.user_data["lang"] = lang
    return lang


def is_owner(user_id: int) -> bool:
    return user_id == AUTHORIZED_USER_ID


def auth_user(user_id: int) -> bool:
    return is_owner(user_id) or user_id in ALLOWED_TELEGRAM_IDS


def check_auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not auth_user(user_id):
            if update.message:
                from .i18n import t

                await update.message.reply_text(
                    t("auth_denied", update=update, context=context)
                )
            elif update.callback_query:
                from .i18n import t

                await update.callback_query.answer(
                    t("auth_denied", update=update, context=context), show_alert=True
                )
            return
        return await func(update, context)

    return wrapper


def check_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not is_owner(user_id):
            from .i18n import t

            if update.message:
                await update.message.reply_text(
                    t("auth_denied", update=update, context=context)
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    t("auth_denied", update=update, context=context), show_alert=True
                )
            return
        return await func(update, context)

    return wrapper
