import logging
import os

from dotenv import load_dotenv
from google import genai

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
if DATABASE_PATH == ":memory:":
    logging.getLogger(__name__).warning(
        "DATABASE_PATH is set to ':memory:'. Data will not persist between connections and background jobs will fail. Use a file path for persistence."
    )
elif not os.path.isabs(DATABASE_PATH):
    DATABASE_PATH = os.path.abspath(DATABASE_PATH)
RESPONSES_PATH = os.getenv(
    "RESPONSES_PATH",
    os.path.join(os.path.dirname(__file__), "responses.json"),
)
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

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Extraction will fail.")

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
WEEKDAYS_PTBR_SHORT = ["SEG", "TER", "QUA", "QUI", "SEX"]

TIMEZONE = os.getenv("TIMEZONE", "UTC")

try:
    from zoneinfo import ZoneInfo

    LOCAL_ZONE = ZoneInfo(TIMEZONE)
except Exception:
    LOCAL_ZONE = None

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def get_model_candidates():
    candidates = []
    configured = GEMINI_MODEL
    if configured:
        candidates.append(configured)

    for fallback in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        if fallback not in candidates:
            candidates.append(fallback)

    return candidates
