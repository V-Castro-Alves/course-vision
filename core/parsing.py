import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List

from google.genai import errors as genai_errors
from pydantic import BaseModel

from .config import client, get_model_candidates, WEEKDAYS, LOCAL_ZONE

logger = logging.getLogger(__name__)


class ClassRow(BaseModel):
    day_index: int = -1
    class_date: str = ""
    start_time: str = ""
    end_time: str = ""
    class_code: str = ""
    class_name: str = ""
    professor: str = ""
    classroom: str = ""


class TableData(BaseModel):
    rows: List[ClassRow]


def clean_cell(value: str) -> str:
    return " ".join((value or "").split())


def looks_like_class_code(value: str) -> bool:
    token = value.strip()
    if not token:
        return False

    if not re.fullmatch(
        r"[A-Za-z0-9/.-]+", token
    ):  # Added '-' and '.' to allowed characters
        return False

    # Must contain at least one letter and (at least one digit OR a '/')
    has_alpha = any(ch.isalpha() for ch in token)
    has_digit_or_slash = any(ch.isdigit() or ch == "/" for ch in token)

    return has_alpha and has_digit_or_slash


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
            name = name[len(prefixed_name) :].strip()

    return code, name


def normalize_classroom(value: str) -> str:
    classroom = clean_cell(value)
    if not classroom:
        return classroom

    if any(separator in classroom for separator in ["/", ",", ";"]):
        return classroom

    classroom = re.sub(
        r"(?<=\d)\s+(?=(LAB\.?|SALA|ROOM(?!\s*\d))\b)",
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

    if not professor:
        marker = " prof."
        lowered = class_name.lower()
        marker_index = lowered.rfind(marker)
        if marker_index != -1:
            professor = class_name[marker_index + len(marker) :].strip()
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


def get_today_date() -> datetime.date:
    if LOCAL_ZONE is not None:
        return datetime.now(tz=LOCAL_ZONE).date()
    return datetime.now().date()


def get_monday_of_week(today: datetime.date) -> datetime.date:
    return today - timedelta(days=today.weekday())


def assign_dates_to_classes(rows: List[ClassRow]) -> List[ClassRow]:
    today = get_today_date()
    monday_of_week = get_monday_of_week(today)

    class_assignments_per_day = {}
    assigned_rows = []
    current_day_offset = 0

    for row in rows:
        if current_day_offset >= len(WEEKDAYS):
            break

        current_day_name = WEEKDAYS[current_day_offset]
        assigned_count = class_assignments_per_day.get(current_day_name, 0)

        row.day_index = (monday_of_week.weekday() + current_day_offset) % 7
        row.class_date = (
            monday_of_week + timedelta(days=current_day_offset)
        ).isoformat()

        if assigned_count == 0:
            row.start_time = "19:00"
            row.end_time = "20:30"
        elif assigned_count == 1:
            row.start_time = "20:50"
            row.end_time = "22:30"

        assigned_rows.append(row)
        class_assignments_per_day[current_day_name] = assigned_count + 1

        if class_assignments_per_day[current_day_name] >= 2:
            current_day_offset += 1

    return assigned_rows


async def generate_with_model_fallback(image_bytes, mime_type, prompt):
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured.")

    last_quota_error = None

    for model_id in get_model_candidates():
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=[
                    prompt,
                    {"inline_data": {"data": image_bytes, "mime_type": mime_type}},
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TableData,
                },
            )
            return response, model_id
        except genai_errors.ClientError as err:
            status_code = getattr(err, "status_code", None)
            if status_code is None and (
                "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err)
            ):
                status_code = 429

            if status_code == 429 or status_code == "429":
                last_quota_error = err
                logger.warning(
                    f"Quota exceeded for model '{model_id}'. Waiting 2s before next model..."
                )
                await asyncio.sleep(2)
                continue

            raise
        except Exception as err:
            last_quota_error = err
            continue

    raise RuntimeError(
        "All Gemini models failed. Check quota at https://aistudio.google.com/"
    ) from last_quota_error
