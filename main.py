from pyrogram import Client
from config.settings import API_ID, API_HASH, BOT_TOKEN
from core.role_manager import set_bot_instance
from modules.command_router import register_commands
from modules.plugin_loader import load_plugins
import os

bot = Client("JarvisBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
set_bot_instance(bot)

if __name__ == '__main__':
    load_plugins(bot)
    register_commands(bot)
    print("\n🚀 Jarvis is starting...")
    bot.run()
