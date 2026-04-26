import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def get_supabase():
    from supabase import create_client
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)
