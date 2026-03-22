import json
import logging
import os
import re
import sqlite3
import mimetypes
from datetime import datetime, timedelta
from typing import List
import asyncio

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes, MessageHandler, filters)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "0"))
ALLOWED_TELEGRAM_IDS = [
    int(user_id)
    for user_id in os.getenv("ALLOWED_TELEGRAM_IDS", "").split(",")
    if user_id
]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is required")
if AUTHORIZED_USER_ID == 0:
    raise RuntimeError("AUTHORIZED_USER_ID is required")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY is not set. Extraction will fail.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

DAYS_PTBR = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
WEEKDAYS_PTBR = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
WEEKDAYS_PTBR_SHORT = ["SEG", "TER", "QUA", "QUI", "SEX"]

RESPONSES_PATH = os.getenv("RESPONSES_PATH", "responses.json")
RESPONSES = {}


def load_responses(path: str = RESPONSES_PATH):
    global RESPONSES
    try:
        with open(path, "r", encoding="utf-8") as f:
            responses = json.load(f)
            if not isinstance(responses, dict):
                raise ValueError("Responses file must be a JSON object")
            RESPONSES = responses
    except FileNotFoundError:
        raise RuntimeError(f"Translations file not found: {path}")
    except Exception as exc:
        raise RuntimeError(f"Error loading translations from {path}: {exc}")


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


def t(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = get_user_lang(update, context)
    if lang not in RESPONSES:
        lang = "en"
    text = RESPONSES.get(lang, {}).get(key) or RESPONSES.get("en", {}).get(key, key)
    return text.format(**kwargs)

# Gemini Client setup
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ClassRow(BaseModel):
    day_index: int = -1
    class_date: str = ""
    class_code: str = ""
    class_name: str = ""
    professor: str = ""
    classroom: str = ""

class TableData(BaseModel):
    rows: List[ClassRow]

SQL_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE NOT NULL, lang TEXT DEFAULT 'en')",
    "CREATE TABLE IF NOT EXISTS raw_images (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, mime_type TEXT, image_blob BLOB, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, day_index INTEGER NOT NULL, class_date TEXT NOT NULL, subject TEXT NOT NULL, room TEXT NOT NULL, professor TEXT NOT NULL, code TEXT NOT NULL, raw TEXT NOT NULL, source_image_id INTEGER, FOREIGN KEY(source_image_id) REFERENCES raw_images(id))",
    "CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, date TEXT NOT NULL, notes TEXT)",
    "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, class_id INTEGER NOT NULL, class_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('attended','skipped')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
]

def db_connect():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def drop_all_tables():
    conn = db_connect()
    cur = conn.cursor()
    # Extract table names from CREATE TABLE statements
    table_names = []
    for stmt in SQL_SCHEMA:
        match = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", stmt)
        if match:
            table_names.append(match.group(1))
    
    # Drop tables in reverse order of creation to handle foreign key constraints
    for table_name in reversed(table_names):
        logger.info(f"Dropping table: {table_name}")
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

def is_owner(user_id: int) -> bool:
    return user_id == AUTHORIZED_USER_ID

def auth_user(user_id: int) -> bool:
    return is_owner(user_id) or user_id in ALLOWED_TELEGRAM_IDS

def check_auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not auth_user(user_id):
            if update.message:
                await update.message.reply_text(t(update, context, "auth_denied"))
            elif update.callback_query:
                await update.callback_query.answer(t(update, context, "auth_denied"), show_alert=True)
            return
        return await func(update, context)
    return wrapper

def check_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else None
        if not is_owner(user_id):
            if update.message:
                await update.message.reply_text(t(update, context, "auth_denied"))
            elif update.callback_query:
                await update.callback_query.answer(t(update, context, "auth_denied"), show_alert=True)
            return
        return await func(update, context)
    return wrapper

...
def get_model_candidates():
    candidates = []

    configured = os.getenv("GEMINI_MODEL")
    if configured:
        candidates.append(configured)

    # Flash models are usually available on free tier.
    for fallback in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        if fallback not in candidates:
            candidates.append(fallback)

    return candidates

    
async def generate_with_model_fallback(image_bytes, mime_type, prompt):
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured.")
    
    last_quota_error = None
    candidates = get_model_candidates()

    logger.info(f"Image details: size={len(image_bytes)} bytes, mime_type={mime_type}")
    logger.debug(f"Prompt sent to Gemini: {prompt}")
    
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
            logger.debug(f"Raw Gemini response from {model_id}: {response.text}")
            return response, model_id
        except genai_errors.ClientError as err:
            status_code = getattr(err, "status_code", None)
            if status_code is None:
                if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                    status_code = 429
            
            if status_code == 429 or status_code == "429":
                last_quota_error = err
                logger.warning(f"Quota exceeded for model '{model_id}'. Waiting 2s before next model...")
                await asyncio.sleep(2)  # Pause to respect rate limits
                continue
            
            logger.error(f"ClientError with model {model_id}: {err}")
            raise
        except Exception as err:
            logger.error(f"Unexpected error with model {model_id}: {err}")
            last_quota_error = err
            continue
            
    raise RuntimeError(
        f"All Gemini models ({candidates}) failed. Check quota at https://aistudio.google.com/"
    ) from last_quota_error

def clean_cell(value: str) -> str:
    return " ".join((value or "").split())

def looks_like_class_code(value: str) -> bool:
    token = value.strip()
    if not token:
        return False

    if not re.fullmatch(r"[A-Za-z0-9/]+", token):
        return False

    return any(ch.isalpha() for ch in token)

def split_class_code_and_name(class_code: str, class_name: str) -> tuple[str, str]:
    code = clean_cell(class_code)
    name = clean_cell(class_name)

    if not code and name and "-" in name:
        possible_code, possible_name = name.split("-", 1)
        if looks_like_class_code(possible_code):
            code = possible_code.strip()
            name = possible_name.strip()

    if code and name:
        prefixed_name = f"{code}-"
        if name.startswith(prefixed_name):
            name = name[len(prefixed_name):].strip()

    return code, name

def normalize_classroom(value: str) -> str:
    classroom = clean_cell(value)
    if not classroom:
        return classroom

    # Keep existing explicit separators untouched.
    if any(separator in classroom for separator in ["/", ",", ";"]):
        return classroom

    # Example: "F-311 LAB C321B" -> "F-311/LAB C321B"
    classroom = re.sub(
        r"(?<=\d)\s+(?=(LAB\.?|SALA|ROOM)\b)",
        "/",
        classroom,
        count=1,
        flags=re.IGNORECASE,
    )

    return classroom

def normalize_row(row: ClassRow) -> ClassRow:
    class_code, class_name = split_class_code_and_name(row.class_code, row.class_name)
    professor = clean_cell(row.professor)
    classroom = normalize_classroom(row.classroom)

    # Fallback split if Gemini returns "... Prof. Name" inside class_name.
    if not professor:
        marker = " prof."
        lowered = class_name.lower()
        marker_index = lowered.rfind(marker)
        if marker_index != -1:
            professor = class_name[marker_index + len(marker):].strip()
            class_name = class_name[:marker_index].strip(" -")

    return ClassRow(
        class_code=class_code,
        class_name=class_name,
        professor=professor,
        classroom=classroom,
    )

def should_skip_row(row: ClassRow) -> bool:
    class_code = row.class_code.lower()
    class_name = row.class_name.lower()
    professor = row.professor.lower()
    classroom = row.classroom.lower()
    combined_text = " ".join([class_code, class_name, professor, classroom])

    if not (class_code or class_name or professor or classroom):
        return True

    # Typical title/header rows found in schedule screenshots.
    if "semestre" in combined_text:
        return True

    if class_code in {"codigo", "código"}:
        return True

    if class_name in {"disciplina", "materia", "matéria", "aula", "turma"}:
        return True

    if professor in {"professor", "professora", "docente"}:
        return True

    if not professor and classroom in {"sala", "local", "room"}:
        return True

    return False

def get_monday_of_week(today: datetime.date) -> datetime.date:
    """
    Calculates the Monday of the relevant week based on the current day.
    - If today is Sunday, it returns the upcoming Monday.
    - For any other day (Mon-Sat), it returns the Monday of the current week.
    """
    if today.weekday() == 6:  # Sunday
        return today + timedelta(days=1)
    else:  # Monday to Saturday
        return today - timedelta(days=today.weekday())

def assign_dates_to_classes(rows: List[ClassRow]) -> List[ClassRow]:
    today = datetime.now().date()
    # Calculate the Monday of the current week
    monday_of_week = get_monday_of_week(today)

    class_assignments_per_day = {} # To keep track of how many classes have been assigned to each day

    assigned_rows = []
    current_day_offset = 0 # 0 for Monday, 1 for Tuesday, etc.

    for row in rows:
        if current_day_offset >= len(WEEKDAYS): # Stop assigning after Friday
            break

        current_day_name = WEEKDAYS[current_day_offset]
        
        # Get count for current day, default to 0
        assigned_count = class_assignments_per_day.get(current_day_name, 0)

        # Assign date and day_index
        row.day_index = monday_of_week.weekday() + current_day_offset
        row.class_date = (monday_of_week + timedelta(days=current_day_offset)).isoformat()
        
        assigned_rows.append(row)
        class_assignments_per_day[current_day_name] = assigned_count + 1

        # If 2 classes have been assigned to the current day, move to the next day
        if class_assignments_per_day[current_day_name] >= 2:
            current_day_offset += 1
            
    return assigned_rows

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        t(update, context, "welcome")
    )

@check_auth
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = context.args
    if not parts:
        return await update.message.reply_text(t(update, context, "setlang_usage"))
    choice = parts[0].lower()
    if choice not in ("pt-br", "en"):
        return await update.message.reply_text(t(update, context, "setlang_usage"))

    user_id = update.effective_user.id
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET lang = ? WHERE telegram_id = ?", (choice, user_id))
    conn.commit()
    conn.close()
    context.user_data["lang"] = choice # Update cache
    await update.message.reply_text(t(update, context, "setlang_success", language=choice))

@check_auth
async def schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()

    today = datetime.now().date()
    monday_of_week = get_monday_of_week(today)
    friday_of_week = monday_of_week + timedelta(days=4) # Assuming classes are Mon-Fri

    cur.execute(
        "SELECT * FROM classes WHERE class_date BETWEEN ? AND ? ORDER BY day_index, class_date",
        (monday_of_week.isoformat(), friday_of_week.isoformat())
    )
    items = cur.fetchall()
    if not items:
        await update.message.reply_text(
            t(update, context, "no_schedule", monday=monday_of_week.strftime('%d/%m'))
        )
        conn.close()
        return

    text = [
        t(update, context, "schedule_header", monday=monday_of_week.strftime('%d/%m'), friday=friday_of_week.strftime('%d/%m'))
    ]
    current_day_index = -1
    for r in items:
        if r['day_index'] != current_day_index:
            current_day_index = r['day_index']
            class_date_obj = datetime.fromisoformat(r['class_date']).date()
            # Use WEEKDAYS_PTBR_SHORT for the day abbreviation
            text.append(f"\n{WEEKDAYS_PTBR_SHORT[current_day_index]} ({class_date_obj.strftime('%d/%m')})")
        
        text.append(
            f"• {r['code']} - {r['subject']}"
            f"\n└ 👤 Prof. {r['professor']} | 📍 {r['room']}"
        )
    await update.message.reply_text("\n".join(text), parse_mode='Markdown')
    conn.close()

@check_auth
async def today_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()

    today = datetime.now().date()
    today_iso = today.isoformat()

    cur.execute(
        "SELECT * FROM classes WHERE class_date = ? ORDER BY day_index, class_date",
        (today_iso,)
    )
    items = cur.fetchall()
    if not items:
        await update.message.reply_text(
            t(update, context, "no_today_classes", today=today.strftime('%d/%m'))
        )
        conn.close()
        return

    text = [t(update, context, "today_header", today=today.strftime('%d/%m'))]
    # Add a day header for today's classes
    text.append(f"\n{WEEKDAYS_PTBR_SHORT[today.weekday()]} ({today.strftime('%d/%m')})")

    for r in items:
        text.append(
            f"• {r['code']} - {r['subject']}"
            f"\n└ 👤 Prof. {r['professor']} | 📍 {r['room']}"
        )
    await update.message.reply_text("\n".join(text), parse_mode='Markdown')
    conn.close()

@check_auth
async def add_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = context.args
    if len(parts) < 2:
        await update.message.reply_text(t(update, context, "add_exam_usage"))
        return
    date_text = parts[0]
    subject = parts[1]
    notes = " ".join(parts[2:]) if len(parts) > 2 else ""
    try:
        exam_date = datetime.fromisoformat(date_text).date()
    except ValueError:
        await update.message.reply_text(t(update, context, "invalid_date_format"))
        return

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO exams (subject, date, notes) VALUES (?, ?, ?)", (subject, exam_date.isoformat(), notes))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        t(update, context, "exam_added", date=exam_date, subject=subject, notes=notes)
    )

@check_auth
async def list_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exams ORDER BY date")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text(t(update, context, "no_exams"))
        return
    lines = ["📚 Próximos exames:"]
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
        t(
            update,
            context,
            "stats_summary",
            total=total,
            attended=attended,
            skipped=skipped,
            rate=rate,
        )
    )
    conn.close()

@check_owner
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_photo"] = True
    await update.message.reply_text(t(update, context, "upload_prompt"))

@check_owner
async def photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_photo"):
        await update.message.reply_text(t(update, context, "execute_upload_first"))
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
        await update.message.reply_text(t(update, context, "send_image_only"))
        return

    path = f"/tmp/{file.file_unique_id}{ext}"
    await file.download_to_drive(path)

    await update.message.reply_text(t(update, context, "image_received"))

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
        "Extract only class schedule entries from this Excel screenshot. "
        "Ignore title/header rows, including semester labels like '5o Semestre ...' "
        "and column headers like 'Sala'. "
        "For each class row, return exactly these fields: "
        "class_code (course code only, e.g., TES/II), "
        "class_name (subject only, without the class code), "
        "professor (teacher name only), "
        "classroom (room/lab/location only). "
        "If there are multiple classrooms in the same cell, separate them with '/'."
    )

    try:
        await update.message.reply_text(t(update, context, "extracting_schedule"))
        response, used_model = await generate_with_model_fallback(image_bytes, mime_type, prompt)
        structured_data = response.parsed
        if not structured_data or not structured_data.rows:
            await update.message.reply_text(t(update, context, "no_rows_parsed"))
            return

        await update.message.reply_text(
            t(update, context, "parsed_rows", count=len(structured_data.rows))
        )

        conn = db_connect()
        cur = conn.cursor()

        # --- NEW LOGIC FOR DELETING EXISTING CLASSES ---
        today = datetime.now().date()
        monday_of_week = get_monday_of_week(today)
        friday_of_week = monday_of_week + timedelta(days=4) # Assuming classes are Mon-Fri

        logger.info(f"Deleting classes for the week of {monday_of_week.isoformat()} to {friday_of_week.isoformat()}")
        cur.execute(
            "DELETE FROM classes WHERE class_date BETWEEN ? AND ?",
            (monday_of_week.isoformat(), friday_of_week.isoformat())
        )
        # --- END NEW LOGIC ---

        inserted = 0
        
        processed_rows = []
        for row in structured_data.rows:
            normalized = normalize_row(row)
            if should_skip_row(normalized):
                continue
            processed_rows.append(normalized)

        # Assign dates to the processed rows
        assigned_classes = assign_dates_to_classes(processed_rows)

        for class_item in assigned_classes:
            # The 'subject' field in the DB will now store the class_name
            # The 'room' field in the DB will now store the classroom
            cur.execute(
                "INSERT INTO classes (day_index, class_date, code, subject, professor, room, raw, source_image_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (class_item.day_index, class_item.class_date, class_item.class_code, class_item.class_name, class_item.professor, class_item.classroom, "Gemini parsed", source_image_id),
            )
            inserted += 1
        
        conn.commit()
        conn.close()
        await update.message.reply_text(
            t(update, context, "parsing_success", count=inserted, model=used_model)
        )

    except Exception as e:
        logger.exception("A extração do Gemini falhou")
        await update.message.reply_text(
            t(update, context, "extraction_error", error=str(e))
        )

async def attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not auth_user(user_id):
        await query.answer(t(update, context, "auth_denied"), show_alert=True)
        return
    if not query.data.startswith("attendance:"):
        await query.answer("Callback inválido")
        return
    _, class_id, class_date, status = query.data.split(":", 3)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO attendance (class_id, class_date, status) VALUES (?, ?, ?)", (class_id, class_date, status))
    conn.commit()
    conn.close()
    await query.answer(f"Marcado como {status}")
    await query.edit_message_text(f"Presença para {class_date}: {status}")

# async def send_class_reminders(application):
#     now = datetime.now()
#     today_idx = now.weekday()
#     window_start = now + timedelta(minutes=10)
#     window_end = now + timedelta(minutes=11)
#     conn = db_connect()
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM classes WHERE day_index = ?", (today_idx,))
#     rows = cur.fetchall()
#     for c in rows:
#         try:
#             class_datetime = datetime.strptime(f"{now.date()} {c['start_time']}", "%Y-%m-%d %H:%M")
#         except ValueError:
#             continue
#         if window_start <= class_datetime < window_end:
#             keyboard = InlineKeyboardMarkup([[
#                 InlineKeyboardButton("✅ Attended", callback_data=f"attendance:{c['id']}:{now.date()}:attended"),
#                 InlineKeyboardButton("❌ Skipped", callback_data=f"attendance:{c['id']}:{now.date()}:skipped"),
#             ]])
#             await application.bot.send_message(
#                 chat_id=AUTHORIZED_USER_ID,
#                 text=f"⏰ Reminder: {c['subject']} at {c['start_time']} in {c['room']}",
#                 reply_markup=keyboard,
#             )
#     conn.close()

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
            msg = f"📢 Exame amanhã: {exam['subject']} ({exam['notes']})"
        elif exam_date == today:
            msg = f"⚠️ Exame hoje: {exam['subject']} ({exam['notes']})"
        else:
            continue
        await application.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=msg)

# async def periodic_jobs(context: ContextTypes.DEFAULT_TYPE):
#     await send_class_reminders(context.application)
#     await send_exam_alerts(context.application)

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
    app.add_handler(CommandHandler("add_exam", add_exam))
    app.add_handler(CommandHandler("exams", list_exams))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo_upload))
    app.add_handler(CallbackQueryHandler(attendance_callback))
    # app.job_queue.run_repeating(periodic_jobs, interval=60, first=10)
    print("Bot iniciado.")
    app.run_polling()

if __name__ == "__main__":
    main()
