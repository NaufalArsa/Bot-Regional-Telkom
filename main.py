"""
Main bot runner module.
Entry point for the Telegram bot application.
"""

import logging
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN
from handlers import setup_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot."""
    # Initialize client
    client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    
    # Setup handlers
    setup_handlers(client)
    
    logger.info("Bot is starting...")
    
    # Run the bot
    client.run_until_disconnected()

if __name__ == "__main__":
    main()