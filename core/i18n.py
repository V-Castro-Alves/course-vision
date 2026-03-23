import json

from telegram import Update
from telegram.ext import ContextTypes

from .config import RESPONSES_PATH
from .database import get_user_lang

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


def t(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    lang = get_user_lang(update, context)
    if lang not in RESPONSES:
        lang = "en"

    text = RESPONSES.get(lang, {}).get(key) or RESPONSES.get("en", {}).get(key, key)
    return text.format(**kwargs)
