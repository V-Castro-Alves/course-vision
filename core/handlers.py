import os
import sqlite3
import mimetypes
from datetime import datetime, timedelta
import tempfile


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    await update.message.reply_text(t("welcome", update=update, context=context))


@check_auth
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = context.args
    if not parts:
        return await update.message.reply_text(
            t("setlang_usage", update=update, context=context)
        )
    choice = parts[0].lower()
    if choice not in ("pt-br", "en"):
        return await update.message.reply_text(
            t("setlang_usage", update=update, context=context)
        )

    user_id = update.effective_user.id
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET lang = ? WHERE telegram_id = ?", (choice, user_id))
    conn.commit()
    conn.close()
    context.user_data["lang"] = choice
    await update.message.reply_text(
        t("setlang_success", update=update, context=context, language=choice)
    )


@check_auth
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = context.args
    if not parts:
        return await update.message.reply_text(
            t("remind_usage", update=update, context=context)
        )

    choice = parts[0].lower()
    user_id = update.effective_user.id
    conn = db_connect()
    cur = conn.cursor()

    if choice == "off":
        cur.execute(
            "UPDATE users SET reminder_minutes = NULL WHERE telegram_id = ?", (user_id,)
        )
        conn.commit()
        conn.close()
        return await update.message.reply_text(
            t("remind_off", update=update, context=context)
        )

    if not choice.isdigit():
        conn.close()
        return await update.message.reply_text(
            t("remind_usage", update=update, context=context)
        )

    minutes = int(choice)
    cur.execute(
        "UPDATE users SET reminder_minutes = ? WHERE telegram_id = ?",
        (minutes, user_id),
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        t("remind_success", update=update, context=context, minutes=minutes)
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
            t(
                "no_schedule",
                update=update,
                context=context,
                monday=monday_of_week.strftime("%d/%m"),
            )
        )
        conn.close()
        return

    text = [
        t(
            "schedule_header",
            update=update,
            context=context,
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
            f"• *{r['start_time']} - {r['end_time']}* | {r['code']} - {r['subject']}"
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
            t(
                "no_today_classes",
                update=update,
                context=context,
                today=today.strftime("%d/%m"),
            )
        )
        conn.close()
        return

    text = [
        t("today_header", update=update, context=context, today=today.strftime("%d/%m"))
    ]
    text.append(f"\n{WEEKDAYS_PTBR_SHORT[today.weekday()]} ({today.strftime('%d/%m')})")

    for r in items:
        text.append(
            f"• *{r['start_time']} - {r['end_time']}* | {r['code']} - {r['subject']}"
            f"\n└ 👤 Prof. {r['professor']} | 📍 {r['room']}"
        )

    await update.message.reply_text("\n".join(text), parse_mode="Markdown")
    conn.close()


@check_owner
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("upload_prompt", update=update, context=context))


@check_owner
async def photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        # Store photo file_id and original message_id for later use
        context.user_data["last_photo_file_id"] = file_id
        context.user_data["last_photo_message_id"] = update.message.message_id
    elif update.message.document and update.message.document.mime_type.startswith(
        "image/"
    ):
        document = update.message.document
        file_id = document.file_id
        context.user_data["last_photo_file_id"] = file_id
        context.user_data["last_photo_message_id"] = update.message.message_id
    else:
        await update.message.reply_text(
            t("send_image_only", update=update, context=context)
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                t("yes_process", update=update, context=context),
                callback_data="process_schedule:yes",
            ),
            InlineKeyboardButton(
                t("no_process", update=update, context=context),
                callback_data="process_schedule:no",
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        t("photo_received_ask_process", update=update, context=context),
        reply_markup=reply_markup,
    )

    # Exit here, actual processing will happen in confirm_schedule_processing
    return


async def _process_and_save_schedule(
    chat_id: int,
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
    ext: str,
):
    file = await context.bot.get_file(file_id)

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
        path = temp_file.name
    await file.download_to_drive(path)

    await context.bot.send_message(
        chat_id=chat_id, text=t("image_received", user_id=user_id, context=context)
    )

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
        await context.bot.send_message(
            chat_id=chat_id,
            text=t("extracting_schedule", user_id=user_id, context=context),
        )
        response, used_model = await generate_with_model_fallback(
            image_bytes, mime_type, prompt
        )
        structured_data = response.parsed
        if not structured_data or not structured_data.rows:
            await context.bot.send_message(
                chat_id=chat_id,
                text=t("no_rows_parsed", user_id=user_id, context=context),
            )
            return

        await context.bot.send_message(
            chat_id=chat_id,
            text=t(
                "parsed_rows",
                user_id=user_id,
                context=context,
                count=len(structured_data.rows),
            ),
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
                "INSERT INTO classes (day_index, class_date, start_time, end_time, code, subject, professor, room, raw, source_image_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    class_item.day_index,
                    class_item.class_date,
                    class_item.start_time,
                    class_item.end_time,
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

        await context.bot.send_message(
            chat_id=chat_id,
            text=t(
                "parsing_success",
                user_id=user_id,
                context=context,
                count=inserted,
                model=used_model,
            ),
        )

    except Exception as e:
        logger.exception("A extração do Gemini falhou")
        await context.bot.send_message(
            chat_id=chat_id,
            text=t("extraction_error", user_id=user_id, context=context, error=str(e)),
        )


async def confirm_schedule_processing(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":")[1]
    file_id = context.user_data.pop("last_photo_file_id", None)
    # message_id = context.user_data.pop("last_photo_message_id", None) # message_id is not needed here
    ext = ".jpg"  # Assuming .jpg for now, need a way to store original ext if necessary
    user_id = query.from_user.id  # Get user_id from the query

    if not file_id:
        await query.edit_message_text(
            t("photo_data_missing", update=update, context=context)
        )
        return

    if choice == "yes":
        await query.edit_message_text(
            t("processing_confirmed", update=update, context=context),
        )
        chat_id = update.effective_chat.id
        await _process_and_save_schedule(
            chat_id, user_id, context, file_id, ext
        )  # Pass user_id

    else:
        await query.edit_message_text(
            t("processing_cancelled", update=update, context=context)
        )


async def attendance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not auth_user(user_id):
        await query.answer(
            t("auth_denied", update=update, context=context), show_alert=True
        )
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
