import logging
import os
import sqlite3
import mimetypes
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes, MessageHandler, filters)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "0"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is required")
if AUTHORIZED_USER_ID == 0:
    raise RuntimeError("AUTHORIZED_USER_ID is required")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Gemini Client setup
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ClassRow(BaseModel):
    day: str = ""
    start_time: str = ""
    end_time: str = ""
    class_code: str = ""
    class_name: str = ""
    professor: str = ""
    classroom: str = ""

class TableData(BaseModel):
    rows: List[ClassRow]

SQL_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS raw_images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mime_type TEXT, image_blob BLOB, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, day_index INTEGER NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL, subject TEXT NOT NULL, room TEXT NOT NULL, raw TEXT NOT NULL, source_image_id INTEGER, FOREIGN KEY(source_image_id) REFERENCES raw_images(id))",
    "CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, date TEXT NOT NULL, notes TEXT)",
    "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, class_id INTEGER NOT NULL, class_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('attended','skipped')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
]

def db_connect():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_connect()
    cur = conn.cursor()
    for stmt in SQL_SCHEMA:
        cur.execute(stmt)
    conn.commit()
    conn.close()

def auth_user(user_id):
    return user_id == AUTHORIZED_USER_ID

def check_auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not auth_user(user_id):
            if update.message:
                await update.message.reply_text("Unauthorized. This bot is private.")
            elif update.callback_query:
                await update.callback_query.answer("Unauthorized", show_alert=True)
            return
        return await func(update, context)
    return wrapper

def get_model_candidates():
    candidates = []
    if GEMINI_MODEL:
        candidates.append(GEMINI_MODEL)
    # Flash models are preferred for free tier. 
    # List based on current available models in AI Studio.
    for fallback in [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3-flash-preview",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
    ]:
        if fallback not in candidates:
            candidates.append(fallback)
    return candidates

def generate_with_model_fallback(image_bytes, mime_type, prompt):
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured.")
    
    last_quota_error = None
    candidates = get_model_candidates()
    
    for model_id in candidates:
        try:
            logger.info(f"Attempting extraction with model: {model_id}")
            response = client.models.generate_content(
                model=model_id,
                contents=[
                    prompt,
                    {"inline_data": {"data": image_bytes, "mime_type": mime_type}}
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TableData,
                }
            )
            return response, model_id
        except genai_errors.ClientError as err:
            # The SDK might return status_code as an int or a string, or it might be in 'code'
            status_code = getattr(err, "status_code", None)
            if status_code is None:
                # Try to extract from the error message or other attributes if possible
                if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                    status_code = 429
            
            if status_code == 429 or status_code == "429":
                last_quota_error = err
                logger.warning(f"Quota exceeded for model '{model_id}'. Trying next candidate...")
                continue
            
            logger.error(f"ClientError with model {model_id}: {err}")
            raise
        except Exception as err:
            logger.error(f"Unexpected error with model {model_id}: {err}")
            last_quota_error = err
            continue
            
    raise RuntimeError(
        f"All configured Gemini models ({candidates}) are out of quota or failed. "
        "Check your API key and quota at https://aistudio.google.com/"
    ) from last_quota_error

def clean_cell(value: str) -> str:
    return " ".join((value or "").split())

def normalize_row(row: ClassRow) -> ClassRow:
    row.day = clean_cell(row.day).capitalize()
    row.start_time = clean_cell(row.start_time)
    row.end_time = clean_cell(row.end_time)
    row.class_name = clean_cell(row.class_name)
    row.classroom = clean_cell(row.classroom)
    row.professor = clean_cell(row.professor)
    return row

def should_skip_row(row: ClassRow) -> bool:
    combined = (row.day + row.class_name + row.classroom).lower()
    if not combined:
        return True
    if "semestre" in combined or "sala" in combined or "professor" in combined:
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to CourseVision!\nCommands:\n"
        "/upload send schedule image\n"
        "/schedule show classes\n"
        "/add_exam YYYY-MM-DD Subject [notes]\n"
        "/exams\n"
        "/stats\n"
    )

@check_auth
async def schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM classes ORDER BY day_index, start_time")
    items = cur.fetchall()
    if not items:
        await update.message.reply_text("No classes stored yet. Send a schedule image to upload.")
        conn.close()
        return

    text = ["📅 Stored classes:"]
    for r in items:
        text.append(
            f"{DAYS[r['day_index']]} {r['start_time']}-{r['end_time']} {r['subject']} [{r['room']}]"
        )
    await update.message.reply_text("\n".join(text))
    conn.close()

@check_auth
async def add_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = context.args
    if len(parts) < 2:
        await update.message.reply_text("Usage: /add_exam YYYY-MM-DD Subject [notes]")
        return
    date_text = parts[0]
    subject = parts[1]
    notes = " ".join(parts[2:]) if len(parts) > 2 else ""
    try:
        exam_date = datetime.fromisoformat(date_text).date()
    except ValueError:
        await update.message.reply_text("Invalid date format. Use YYYY-MM-DD")
        return

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO exams (subject, date, notes) VALUES (?, ?, ?)", (subject, exam_date.isoformat(), notes))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Exam added: {exam_date} - {subject} {notes}")

@check_auth
async def list_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exams ORDER BY date")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No exams scheduled yet.")
        return
    lines = ["📚 Upcoming exams:"]
    for r in rows:
        lines.append(f"{r['date']}: {r['subject']} ({r['notes']})")
    await update.message.reply_text("\n".join(lines))

@check_auth
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM attendance")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as attended FROM attendance WHERE status='attended'")
    attended = cur.fetchone()["attended"]
    cur.execute("SELECT COUNT(*) as skipped FROM attendance WHERE status='skipped'")
    skipped = cur.fetchone()["skipped"]
    rate = f"{attended / total * 100:.1f}%" if total > 0 else "N/A"
    await update.message.reply_text(
        "📊 Attendance Stats:\n"
        f"Total responses: {total}\n"
        f"Attended: {attended}\n"
        f"Skipped: {skipped}\n"
        f"Presence rate: {rate}"
    )
    conn.close()

@check_auth
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_photo"] = True
    await update.message.reply_text(
        "Send the schedule image now, and I will parse it into your classes using Gemini."
    )

@check_auth
async def photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_photo"):
        await update.message.reply_text("Please run /upload first.")
        return
    context.user_data["awaiting_photo"] = False

    # Check if it's a photo or a document
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        ext = ".jpg"
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        file = await update.message.document.get_file()
        # Use the actual extension from the filename or guess from mime_type
        ext = os.path.splitext(update.message.document.file_name)[1] or ".png"
    else:
        await update.message.reply_text("Please send an image (JPG or PNG).")
        return

    path = f"/tmp/{file.file_unique_id}{ext}"
    await file.download_to_drive(path)

    with open(path, "rb") as f:
        image_bytes = f.read()
    
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
        mime_type = "image/jpeg"

    # Save raw image to DB
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO raw_images (filename, mime_type, image_blob) VALUES (?, ?, ?)",
        (os.path.basename(path), mime_type, sqlite3.Binary(image_bytes))
    )
    source_image_id = cur.lastrowid
    conn.commit()
    conn.close()

    prompt = (
        "Extract class schedule entries from this screenshot. "
        "For each class, return: day (e.g. Monday), start_time (HH:MM), end_time (HH:MM), "
        "class_code, class_name, professor, and classroom. "
        "If multiple classes are on the same row, extract them all. "
        "If times are not explicitly mentioned, leave them empty."
    )

    try:
        response, used_model = generate_with_model_fallback(image_bytes, mime_type, prompt)
        structured_data = response.parsed
        if not structured_data or not structured_data.rows:
            await update.message.reply_text("Gemini could not find any class data in that image.")
            return

        conn = db_connect()
        cur = conn.cursor()
        inserted = 0
        day_counts = {}
        for row in structured_data.rows:
            normalized = normalize_row(row)
            if should_skip_row(normalized):
                continue
            
            day_idx = -1
            for i, d in enumerate(DAYS):
                if d.lower() in normalized.day.lower():
                    day_idx = i
                    break
            
            if day_idx == -1:
                continue

            # Default time logic: 1st class 19:00-20:30, 2nd class 20:50-22:30
            if not normalized.start_time or not normalized.end_time or normalized.start_time == "00:00":
                count = day_counts.get(day_idx, 0)
                if count == 0:
                    normalized.start_time = "19:00"
                    normalized.end_time = "20:30"
                else:
                    normalized.start_time = "20:50"
                    normalized.end_time = "22:30"
                day_counts[day_idx] = count + 1

            subject = f"{normalized.class_code} {normalized.class_name} ({normalized.professor})".strip()
            cur.execute(
                "INSERT INTO classes (day_index, start_time, end_time, subject, room, raw, source_image_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (day_idx, normalized.start_time, normalized.end_time, subject, normalized.classroom, "Gemini parsed", source_image_id),
            )
            inserted += 1
        
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Successfully parsed {inserted} classes using {used_model}.")

    except Exception as e:
        logger.exception("Gemini extraction failed")
        await update.message.reply_text(f"Error during extraction: {str(e)}")

async def attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not auth_user(user_id):
        await query.answer("Unauthorized", show_alert=True)
        return
    if not query.data.startswith("attendance:"):
        await query.answer("Invalid callback")
        return
    _, class_id, class_date, status = query.data.split(":", 3)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO attendance (class_id, class_date, status) VALUES (?, ?, ?)", (class_id, class_date, status))
    conn.commit()
    conn.close()
    await query.answer(f"Marked as {status}")
    await query.edit_message_text(f"Attendance for {class_date}: {status}")

async def send_class_reminders(application):
    now = datetime.now()
    today_idx = now.weekday()
    window_start = now + timedelta(minutes=10)
    window_end = now + timedelta(minutes=11)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM classes WHERE day_index = ?", (today_idx,))
    rows = cur.fetchall()
    for c in rows:
        try:
            class_datetime = datetime.strptime(f"{now.date()} {c['start_time']}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if window_start <= class_datetime < window_end:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Attended", callback_data=f"attendance:{c['id']}:{now.date()}:attended"),
                InlineKeyboardButton("❌ Skipped", callback_data=f"attendance:{c['id']}:{now.date()}:skipped"),
            ]])
            await application.bot.send_message(
                chat_id=AUTHORIZED_USER_ID,
                text=f"⏰ Reminder: {c['subject']} at {c['start_time']} in {c['room']}",
                reply_markup=keyboard,
            )
    conn.close()

async def send_exam_alerts(application):
    today = datetime.now().date()
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    conn.close()
    for exam in exams:
        exam_date = datetime.fromisoformat(exam["date"])
        if exam_date == today + timedelta(days=1):
            msg = f"📢 Exam tomorrow: {exam['subject']} ({exam['notes']})"
        elif exam_date == today:
            msg = f"⚠️ Exam today: {exam['subject']} ({exam['notes']})"
        else:
            continue
        await application.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=msg)

async def periodic_jobs(context: ContextTypes.DEFAULT_TYPE):
    await send_class_reminders(context.application)
    await send_exam_alerts(context.application)

def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("schedule", schedule_text))
    app.add_handler(CommandHandler("add_exam", add_exam))
    app.add_handler(CommandHandler("exams", list_exams))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo_upload))
    app.add_handler(CallbackQueryHandler(attendance_callback))
    app.job_queue.run_repeating(periodic_jobs, interval=60, first=10)
    print("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
