import os
import re
import sqlite3

from telegram import Update
from telegram.ext import ContextTypes

from .config import AUTHORIZED_USER_ID, ALLOWED_TELEGRAM_IDS, DATABASE_PATH

SQL_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE NOT NULL, lang TEXT DEFAULT 'en')",
    "CREATE TABLE IF NOT EXISTS raw_images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mime_type TEXT, image_blob BLOB, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, day_index INTEGER NOT NULL, class_date TEXT NOT NULL, subject TEXT NOT NULL, room TEXT NOT NULL, professor TEXT NOT NULL, code TEXT NOT NULL, raw TEXT NOT NULL, source_image_id INTEGER, FOREIGN KEY(source_image_id) REFERENCES raw_images(id))",
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
    conn.commit()
    conn.close()


def get_user_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_user.id
    if context.user_data.get("lang"):
        return context.user_data["lang"]

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
    conn.close()
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
                await update.message.reply_text(t(update, context, "auth_denied"))
            elif update.callback_query:
                from .i18n import t
                await update.callback_query.answer(t(update, context, "auth_denied"), show_alert=True)
            return
        return await func(update, context)

    return wrapper


def check_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not is_owner(user_id):
            from .i18n import t
            if update.message:
                await update.message.reply_text(t(update, context, "auth_denied"))
            elif update.callback_query:
                await update.callback_query.answer(t(update, context, "auth_denied"), show_alert=True)
            return
        return await func(update, context)

    return wrapper
