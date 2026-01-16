
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FREECRYPTO_API_KEY = os.getenv("FREECRYPTO_API_KEY")
FREECRYPTO_API_BASE_URL = os.getenv("FREECRYPTO_API_BASE_URL", "https://api.freecryptoapi.com/v1")

COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / os.getenv("RAW_DATA_DIR", "data/raw")
CLEANED_DATA_DIR = BASE_DIR / os.getenv("CLEANED_DATA_DIR", "data/cleaned")
LABELED_DATA_DIR = BASE_DIR / os.getenv("LABELED_DATA_DIR", "data/labeled")
QUALITY_REPORTS_DIR = BASE_DIR / "data/quality_reports"

EVALUATION_DB_PATH = BASE_DIR / os.getenv("EVALUATION_DB_PATH", "data/evaluations.db")

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LABELED_DATA_DIR.mkdir(parents=True, exist_ok=True)
QUALITY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

if not FREECRYPTO_API_KEY:
    raise ValueError("FREECRYPTO_API_KEY not found in environment variables")

