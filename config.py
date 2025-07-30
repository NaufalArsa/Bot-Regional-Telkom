"""
Configuration module for the Telegram bot.
Handles environment variables and application settings.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_env_var(name, required=True):
    """Get environment variable with optional requirement check."""
    value = os.environ.get(name)
    if required and not value:
        raise ValueError(f"{name} environment variable not set!")
    return value

# Telegram Bot Configuration
API_ID = int(get_env_var('API_ID'))
API_HASH = get_env_var('API_HASH')
BOT_TOKEN = get_env_var('BOT_TOKEN')

# Google Sheets Configuration
SHEET_NAME = "Rekap Visit AM"
GOOGLE_CREDS_JSON = get_env_var('GOOGLE_CREDS_JSON')
GOOGLE_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Supabase Configuration
SUPABASE_URL = get_env_var('SUPABASE_URL', required=False)
SUPABASE_KEY = get_env_var('SUPABASE_KEY', required=False)
SUPABASE_BUCKET = "photo"

# Channel Configuration
CHANNEL_ID = -1002591459174  # Replace with your channel ID

# Parse Google credentials
def get_google_credentials_dict():
    """Parse Google credentials from environment variable."""
    return json.loads(GOOGLE_CREDS_JSON)