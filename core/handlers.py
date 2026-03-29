import os
import sqlite3
import mimetypes
from datetime import datetime, timedelta
import tempfile
import functools

from telegram import Update
from telegram.ext import ContextTypes

from .config import WEEKDAYS_PTBR_SHORT, logger
from .database import db_connect, check_auth, check_owner, auth_user
from .i18n import t
from .parsing import (
    assign_dates_to_classes,
    generate_with_model_fallback,
    get_monday_of_week,
    get_today_date,
    normalize_row,
    should_skip_row,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t(update, context, "welcome"))


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
    context.user_data["lang"] = choice
    await update.message.reply_text(
        t(update, context, "setlang_success", language=choice)
    )


@check_auth
async def schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()

    today = get_today_date()
    monday_of_week = get_monday_of_week(today)
    friday_of_week = monday_of_week + timedelta(days=4)

    cur.execute(
        "SELECT * FROM classes WHERE class_date BETWEEN ? AND ? ORDER BY day_index, class_date",
        (monday_of_week.isoformat(), friday_of_week.isoformat()),
    )
    items = cur.fetchall()
    if not items:
        await update.message.reply_text(
            t(update, context, "no_schedule", monday=monday_of_week.strftime("%d/%m"))
        )
        conn.close()
        return

    text = [
        t(
            update,
            context,
            "schedule_header",
            monday=monday_of_week.strftime("%d/%m"),
            friday=friday_of_week.strftime("%d/%m"),
        )
    ]
    current_day_index = -1
    for r in items:
        if r["day_index"] != current_day_index:
            current_day_index = r["day_index"]
            class_date_obj = datetime.fromisoformat(r["class_date"]).date()
            text.append(
                f"\n{WEEKDAYS_PTBR_SHORT[current_day_index]} ({class_date_obj.strftime('%d/%m')})"
            )

        text.append(
            f"• {r['code']} - {r['subject']}"
            f"\n└ 👤 Prof. {r['professor']} | 📍 {r['room']}"
        )

    await update.message.reply_text("\n".join(text), parse_mode="Markdown")
    conn.close()


@check_auth
async def today_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_connect()
    cur = conn.cursor()

    today = get_today_date()
    today_iso = today.isoformat()

    cur.execute(
        "SELECT * FROM classes WHERE class_date = ? ORDER BY day_index, class_date",
        (today_iso,),
    )
    items = cur.fetchall()
    if not items:
        await update.message.reply_text(
            t(update, context, "no_today_classes", today=today.strftime("%d/%m"))
        )
        conn.close()
        return

    text = [t(update, context, "today_header", today=today.strftime("%d/%m"))]
    text.append(f"\n{WEEKDAYS_PTBR_SHORT[today.weekday()]} ({today.strftime('%d/%m')})")

    for r in items:
        text.append(
            f"• {r['code']} - {r['subject']}"
            f"\n└ 👤 Prof. {r['professor']} | 📍 {r['room']}"
        )

    await update.message.reply_text("\n".join(text), parse_mode="Markdown")
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

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        ext = ".jpg"
    elif update.message.document and update.message.document.mime_type.startswith(
        "image/"
    ):
        file = await update.message.document.get_file()
        ext = os.path.splitext(update.message.document.file_name)[1] or ".png"
    else:
        await update.message.reply_text(t(update, context, "send_image_only"))
        return

    # Use NamedTemporaryFile for secure temporary file handling
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
        path = temp_file.name
    await file.download_to_drive(path)

    await update.message.reply_text(t(update, context, "image_received"))

    with open(path, "rb") as f:
        image_bytes = f.read()

    # Clean up the temporary file
    os.unlink(path)

    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
        mime_type = "image/jpeg"

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO raw_images (filename, mime_type, image_blob) VALUES (?, ?, ?)",
        (os.path.basename(path), mime_type, sqlite3.Binary(image_bytes)),
    )
    source_image_id = cur.lastrowid
    conn.commit()
    conn.close()

    prompt = (
        "Extract class schedule entries from the provided image, which is an Excel screenshot. "
        "Focus solely on individual class rows. "
        "Disregard all header information, including semester titles (e.g., '5o Semestre', 'Fall 2024'), "
        "column headers (e.g., 'Sala', 'Professor', 'Subject'), and any other non-class-related text. "
        "For each detected class entry, provide the following four fields precisely: "
        "1. `class_code`: Extract the unique course identifier (e.g., 'TES/II', 'MATH101', 'PHY-201'). This often contains a mix of letters, numbers, and symbols like '/-'. "
        "2. `class_name`: Identify the subject or discipline name (e.g., 'Programação Orientada a Objetos', 'Calculus I', 'Thermodynamics'). This should be the name *without* the `class_code` if the code is prepended. "
        "3. `professor`: Extract the full name of the professor or instructor. If the professor's name is not explicitly present, leave this field empty. "
        "4. `classroom`: Determine the physical location where the class takes place (e.g., 'LAB 302', 'SALA 101', 'Room 205', 'Online'). If multiple classrooms are listed in a single cell, separate them using a single forward slash (e.g., 'LAB 302/SALA 101'). If the classroom is not specified, leave this field empty. "
        "Ensure that each extracted field is clean and free of extraneous whitespace. "
        "If a field is clearly absent or cannot be determined, it should be returned as an empty string."
    )

    try:
        await update.message.reply_text(t(update, context, "extracting_schedule"))
        response, used_model = await generate_with_model_fallback(
            image_bytes, mime_type, prompt
        )
        structured_data = response.parsed
        if not structured_data or not structured_data.rows:
            await update.message.reply_text(t(update, context, "no_rows_parsed"))
            return

        await update.message.reply_text(
            t(update, context, "parsed_rows", count=len(structured_data.rows))
        )

        conn = db_connect()
        cur = conn.cursor()

        today = get_today_date()
        monday_of_week = get_monday_of_week(today)
        friday_of_week = monday_of_week + timedelta(days=4)

        logger.info(
            f"Deleting classes for the week of {monday_of_week.isoformat()} to {friday_of_week.isoformat()}"
        )
        cur.execute(
            "DELETE FROM classes WHERE class_date BETWEEN ? AND ?",
            (monday_of_week.isoformat(), friday_of_week.isoformat()),
        )

        inserted = 0
        processed_rows = []
        for row in structured_data.rows:
            normalized = normalize_row(row)
            if should_skip_row(normalized):
                continue
            processed_rows.append(normalized)

        assigned_classes = assign_dates_to_classes(processed_rows)

        for class_item in assigned_classes:
            cur.execute(
                "INSERT INTO classes (day_index, class_date, code, subject, professor, room, raw, source_image_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    class_item.day_index,
                    class_item.class_date,
                    class_item.class_code,
                    class_item.class_name,
                    class_item.professor,
                    class_item.classroom,
                    "Gemini parsed",
                    source_image_id,
                ),
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
    cur.execute(
        "INSERT INTO attendance (class_id, class_date, status) VALUES (?, ?, ?)",
        (class_id, class_date, status),
    )
    conn.commit()
    conn.close()
    await query.answer(f"Marcado como {status}")
    await query.edit_message_text(f"Presença para {class_date}: {status}")
