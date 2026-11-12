import os
from pathlib import Path

from tradepilot.env_loader import load_default_env
from tradepilot import create_app

# Local: Neon CLI writes `.env.local` (DATABASE_URL, …). Production injects env at runtime.
_repo_root = Path(__file__).resolve().parents[2]
load_default_env(_repo_root)

# Production must set TRADEPILOT_ENV=production and DATABASE_URL or TRADEPILOT_DB_PATH.
os.environ.setdefault("TRADEPILOT_ENV", os.getenv("TRADEPILOT_ENV", "development"))
app = create_app()
