import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOWNLOAD_DIR = DATA_DIR / "downloads"
CHART_DIR = DATA_DIR / "charts"

DB_PATH = DATA_DIR / "state.db"
EXCEL_PATH = DATA_DIR / "financial_usage.xlsx"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
LOCAL_TIMEZONE = os.getenv("LOCAL_TIMEZONE", "Asia/Bangkok")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID", "").strip()

POLL_TIMEOUT = int(os.getenv("POLL_TIMEOUT", "30"))
RETRY_SECONDS = int(os.getenv("RETRY_SECONDS", "10"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}"

TZ = ZoneInfo(LOCAL_TIMEZONE)

for directory in (DATA_DIR, DOWNLOAD_DIR, CHART_DIR):
    directory.mkdir(parents=True, exist_ok=True)
