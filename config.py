import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    exit("Error: BOT_TOKEN is not set in .env")

admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

if not ADMIN_IDS:
    print("Warning: ADMIN_IDS is empty or invalid. Admin features will not work.")

# Webhook & Server Config
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "False").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 3000))

# Redis (Optional)
REDIS_URL = os.getenv("REDIS_URL", "")
