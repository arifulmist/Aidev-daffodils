import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
SAVED_MODELS_DIR = BASE_DIR / "saved_models"

load_dotenv(ROOT_DIR / ".env")

# Handle Vercel / AWS Lambda read-only filesystem by copying SQLite to /tmp
if os.getenv("VERCEL"):
    import shutil
    tmp_db = Path("/tmp/upay_ops.db")
    src_db = BASE_DIR / "upay_ops.db"
    if src_db.exists() and not tmp_db.exists():
        try:
            shutil.copy2(src_db, tmp_db)
        except Exception as e:
            print(f"[Vercel Setup] Error copying db to /tmp: {e}")
    if tmp_db.exists():
        DEFAULT_DB_URL = f"sqlite:///{tmp_db}"
    else:
        DEFAULT_DB_URL = f"sqlite:///{src_db}"
else:
    DEFAULT_DB_URL = f"sqlite:///{BASE_DIR}/upay_ops.db"

class Settings(BaseModel):
    APP_NAME: str = "upay Ops Intelligence"
    APP_VERSION: str = "1.0.0"
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    SAVED_MODELS_DIR: Path = SAVED_MODELS_DIR
    
    # Database URL: defaults to local/tmp SQLite, can be overridden with Supabase PostgreSQL URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    
    # Supabase Integration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://mfpbiwqesrlcljkumgxc.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "sb_publishable_u9d8u7Ag6nv6pjXV30sVjA_8w6e7dVE")
    
    # LLM Settings
    BYNARA_API_KEY: str = os.getenv("BYNARA_API_KEY", "sk-nry-Dqhpbi5wZJ5uwxszJ6bEaTi_bSvfYpzOTM-ufdBpxhc")
    BYNARA_BASE_URL: str = os.getenv("BYNARA_BASE_URL", "https://router.bynara.id/v1")
    BYNARA_MODEL: str = os.getenv("BYNARA_MODEL", "agnes-2.5-flash")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "bynara")  # 'bynara', 'gemini', 'openai', or 'mock_smart'
    
    # Ground Truth Classes
    ROOT_CAUSE_CLASSES: list = [
        "SUCCESS",
        "MERCHANT_ACK_FAILURE",
        "MISSING_REVERSAL",
        "STATUS_SYNC_DELAY",
        "DUPLICATE_TRANSACTION",
        "NETWORK_TIMEOUT",
        "INSUFFICIENT_BALANCE",
        "SUSPICIOUS_ACTIVITY",
        "UNKNOWN_FAILURE"
    ]
    
    # Complaint Categories
    COMPLAINT_CATEGORIES: list = [
        "TRANSACTION_DISPUTE",
        "REFUND",
        "FAILED_PAYMENT",
        "DUPLICATE_PAYMENT",
        "ACCOUNT_ISSUE",
        "MERCHANT_ISSUE",
        "OTHER"
    ]
    
    # Operational Teams
    TEAMS: list = [
        "Reconciliation",
        "Merchant Operations",
        "Fraud & Security",
        "Network & Core Banking",
        "Customer Care Tier 2"
    ]

settings = Settings()
