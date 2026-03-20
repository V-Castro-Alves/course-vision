from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel
from typing import List
import csv
import os
import mimetypes
import re

from dotenv import load_dotenv

# 1. Setup - Load API Key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Add it to your .env file.")

client = genai.Client(api_key=api_key)


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

# 2. Define the structure you want
class ClassRow(BaseModel):
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


def generate_with_model_fallback(image_bytes, mime_type, prompt):
    last_quota_error = None

    for model_id in get_model_candidates():
        try:
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
            if getattr(err, "status_code", None) == 429:
                last_quota_error = err
                print(f"Quota exceeded for model '{model_id}'. Trying another model...")
                continue
            raise

    raise RuntimeError(
        "All configured Gemini models are out of quota. "
        "Set GEMINI_MODEL in .env to a model available in your account or enable billing."
    ) from last_quota_error

def extract_excel_from_image(image_path, output_csv):
    # Load the image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

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

    # 3. Call Gemini with Structured Output
    response, used_model = generate_with_model_fallback(image_bytes, mime_type, prompt)

    # 4. Save to CSV
    structured_data = response.parsed
    if structured_data is None:
        raise RuntimeError("Gemini returned no structured data. Check the image quality and prompt.")

    rows_written = 0
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["class_code", "class_name", "professor", "classroom"])
        for row in structured_data.rows:
            normalized = normalize_row(row)
            if should_skip_row(normalized):
                continue

            writer.writerow([
                normalized.class_code,
                normalized.class_name,
                normalized.professor,
                normalized.classroom,
            ])
            rows_written += 1
    
    print(f"Done! Data saved to {output_csv} (model: {used_model}, rows: {rows_written})")

# Run it
if __name__ == "__main__":
    try:
        extract_excel_from_image("screenshot1.jpg", "output_data.csv")
    except RuntimeError as err:
        print(f"Error: {err}")