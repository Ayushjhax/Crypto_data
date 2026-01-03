"""
Configuration settings for the crypto data pipeline.

INTERVIEW EXPLANATION:
This module demonstrates several important concepts:

1. ENVIRONMENT VARIABLES: Using os.getenv() to read from .env file
   - Why? Security - API keys never in source code
   - Why? Flexibility - Different configs per environment
   
2. PATH MANAGEMENT: Using pathlib.Path for file operations
   - Why? Cross-platform compatibility (Windows/Mac/Linux)
   - Why? Type safety and better error handling
   
3. CONFIGURATION VALIDATION: Checking required values exist
   - Why? Fail fast if misconfigured
   - Why? Clear error messages for debugging
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
FREECRYPTO_API_KEY = os.getenv("FREECRYPTO_API_KEY")
FREECRYPTO_API_BASE_URL = os.getenv("FREECRYPTO_API_BASE_URL", "https://api.freecryptoapi.com/v1")

# Data Collection Settings
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Storage Directories
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / os.getenv("RAW_DATA_DIR", "data/raw")
CLEANED_DATA_DIR = BASE_DIR / os.getenv("CLEANED_DATA_DIR", "data/cleaned")
LABELED_DATA_DIR = BASE_DIR / os.getenv("LABELED_DATA_DIR", "data/labeled")
QUALITY_REPORTS_DIR = BASE_DIR / "data/quality_reports"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LABELED_DATA_DIR.mkdir(parents=True, exist_ok=True)
QUALITY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Validation
if not FREECRYPTO_API_KEY:
    raise ValueError("FREECRYPTO_API_KEY not found in environment variables")

