import os

from tradepilot import create_app

# Production must set TRADEPILOT_ENV=production and DATABASE_URL or TRADEPILOT_DB_PATH.
os.environ.setdefault("TRADEPILOT_ENV", os.getenv("TRADEPILOT_ENV", "development"))
app = create_app()
