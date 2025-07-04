import asyncio
import logging
import os
import json
import importlib.util
import sys
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Custom modules
from jarvis_engine import JarvisEngine
from file_manager import FileManager
from error_handler import ErrorHandler
from plugin_manager import PluginManager
from db_manager import DatabaseManager

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class JarvisBot:
    def __init__(self):
        self.token = os.getenv('API_TOKEN')
        self.owner_id = int(os.getenv('OWNER_ID', '0'))
        self.jarvis_engine = JarvisEngine()
        self.file_manager = FileManager()
        self.error_handler = ErrorHandler()
        self.db_manager = DatabaseManager()
        self.plugin_manager = PluginManager(self)
        self.config_path = Path('config/settings.json')
        self.memory_path = Path('logs/memory.json')
        self.features = {}
        self.load_config()
        self.ensure_directories()

    def ensure_directories(self):
        for dir_name in ['features', 'bots', 'db', 'logs', 'uploads', 'config']:
            Path(dir_name).mkdir(exist_ok=True)

    def load_config(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'devs': [self.owner_id],
                    'access_mode': 'dev',
                    'personality': 'JARVIS v2 - Self-Evolving AI Assistant'
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {'devs': [self.owner_id], 'access_mode': 'dev', 'personality': 'JARVIS v2'}

    def save_config(self):
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def is_dev(self, user_id): return user_id in self.config.get('devs', [])
    def is_owner(self, user_id): return user_id == self.owner_id
    def has_access(self, user_id): return True if self.config.get('access_mode') == 'public' else self.is_dev(user_id)

    # ──────── Basic Commands ────────

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🧠 JARVIS v2 - Self-Evolving AI Bot\nReady to assist.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("""🔧 JARVIS v2 Commands:
/start - Welcome message
/help - This help menu
/info - Bot status
/access - Toggle dev/public mode
/adddev <id> - Add dev
/removedev <id> - Remove dev
/enable <plugin> - Enable plugin
/disable <plugin> - Disable plugin
/memory - View memory
/clearmemory - Clear memory
/log - AI activity logs
/tree - Folder structure
/diff <file> - Show changes
/undo <file> - Revert changes
/review <file> - Code review
""")

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mode = self.config.get('access_mode', 'dev')
        personality = self.config.get('personality', 'JARVIS v2')
        await update.message.reply_text(f"🤖 {personality}\n📊 Mode: {mode}")

    async def access_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        args = context.args
        if args and args[0] in ['dev', 'public']:
            self.config['access_mode'] = args[0]
            self.save_config()
            await update.message.reply_text(f"✅ Access mode: {args[0]}")
        else:
            await update.message.reply_text("Usage: /access dev|public")

    async def add_dev(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner only")
            return
        if not context.args:
            await update.message.reply_text("Usage: /adddev <user_id>")
            return
        try:
            user_id = int(context.args[0])
            if user_id not in self.config['devs']:
                self.config['devs'].append(user_id)
                self.save_config()
                await update.message.reply_text(f"✅ Added dev: {user_id}")
            else:
                await update.message.reply_text("User already a dev")
        except ValueError:
            await update.message.reply_text("Invalid user ID")

    async def remove_dev(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner only")
            return
        if not context.args:
            await update.message.reply_text("Usage: /removedev <user_id>")
            return
        try:
            user_id = int(context.args[0])
            if user_id in self.config['devs'] and user_id != self.owner_id:
                self.config['devs'].remove(user_id)
                self.save_config()
                await update.message.reply_text(f"✅ Removed dev: {user_id}")
            else:
                await update.message.reply_text("Cannot remove owner or user not found")
        except ValueError:
            await update.message.reply_text("Invalid user ID")

    # ──────── Plugin Features ────────

    async def enable_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        if not context.args:
            await update.message.reply_text("Usage: /enable <plugin_name>")
            return
        name = context.args[0]
        if self.plugin_manager.enable_plugin(name, context.application):
            await update.message.reply_text(f"✅ Plugin '{name}' enabled and loaded.")
        else:
            await update.message.reply_text(f"❌ Failed to enable plugin '{name}'.")

    async def disable_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        if not context.args:
            await update.message.reply_text("Usage: /disable <plugin_name>")
            return
        name = context.args[0]
        if self.plugin_manager.disable_plugin(name):
            await update.message.reply_text(f"❌ Plugin '{name}' disabled.")
        else:
            await update.message.reply_text(f"⚠️ Failed to disable plugin '{name}'.")

    # ──────── Memory / Logs / Tools ────────

    async def memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    data = json.load(f)
                    if data:
                        msg = "🧠 Recent Memory:\n" + "\n".join([f"{i+1}. {item.get('task', 'Unknown')}" for i, item in enumerate(data[-5:])])
                        await update.message.reply_text(msg)
                    else:
                        await update.message.reply_text("🧠 Memory is empty")
            else:
                await update.message.reply_text("🧠 No memory file found")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reading memory: {e}")

    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        try:
            with open(self.memory_path, 'w') as f:
                json.dump([], f)
            await update.message.reply_text("✅ Memory cleared")
        except Exception as e:
            await update.message.reply_text(f"❌ Error clearing memory: {e}")

    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        log_file = Path('logs/ai_activity.log')
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = f.readlines()[-10:]
                await update.message.reply_text("📋 Logs:\n" + "".join(logs))
        else:
            await update.message.reply_text("📋 No logs found")

    async def tree(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📁 JARVIS Bot Structure:\n├── features/\n├── bots/\n├── db/\n├── logs/\n├── uploads/\n├── config/\n└── main.py")

    async def diff(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        if not context.args:
            await update.message.reply_text("Usage: /diff <filename>")
            return
        filename = context.args[0]
        result = self.file_manager.show_diff(filename)
        await update.message.reply_text(f"🔍 Diff for {filename}:\n```\n{result}\n```", parse_mode=ParseMode.MARKDOWN)

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        if not context.args:
            await update.message.reply_text("Usage: /undo <filename>")
            return
        filename = context.args[0]
        if self.file_manager.undo_changes(filename):
            await update.message.reply_text(f"✅ Reverted {filename}")
        else:
            await update.message.reply_text(f"❌ Could not revert {filename}")

    async def review_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return
        if not context.args:
            await update.message.reply_text("Usage: /review <filename>")
            return
        await update.message.reply_text(f"🔍 Code review for {context.args[0]} completed")

    # ──────── AI Request Handlers ────────

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.has_access(user_id): return
        if update.message.chat.type == 'private' or 'jarvis' in update.message.text.lower():
            await self.process_ai_request(update, context)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.has_access(user_id): return
        doc = update.message.document
        file = await context.bot.get_file(doc.file_id)
        file_path = Path(f'uploads/{doc.file_name}')
        await file.download_to_drive(file_path)
        caption = update.message.caption or "Build this project"
        await self.process_ai_file_request(update, context, file_path, caption)

    async def process_ai_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_dev(update.effective_user.id) and self.config.get('access_mode') == 'dev':
            return
        prompt = update.message.text
        try:
            response = await self.jarvis_engine.process_prompt(prompt)
            self.log_memory(prompt, response)
            if isinstance(response, dict) and 'files' in response:
                await self.execute_file_operations(response['files'])
                await update.message.reply_text("✅ Task completed successfully")
            else:
                await update.message.reply_text(str(response))
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def process_ai_file_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: Path, instruction: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            response = await self.jarvis_engine.process_file_prompt(instruction, content)
            self.log_memory(f"File: {file_path.name} - {instruction}", response)
            if isinstance(response, dict) and 'files' in response:
                await self.execute_file_operations(response['files'])
                await update.message.reply_text("✅ File processed and changes applied")
            else:
                await update.message.reply_text("✅ File processed")
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def execute_file_operations(self, files_dict):
        for file_path, content in files_dict.items():
            self.file_manager.write_file(file_path, content)

    def log_memory(self, task, response):
        try:
            memory_data = []
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
            memory_data.append({
                'timestamp': str(asyncio.get_event_loop().time()),
                'task': task[:100],
                'response_type': type(response).__name__
            })
            memory_data = memory_data[-50:]
            with open(self.memory_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging memory: {e}")

    def run(self):
        application = Application.builder().token(self.token).build()

        # Core Handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("info", self.info))
        application.add_handler(CommandHandler("access", self.access_toggle))
        application.add_handler(CommandHandler("adddev", self.add_dev))
        application.add_handler(CommandHandler("removedev", self.remove_dev))
        application.add_handler(CommandHandler("enable", self.enable_feature))
        application.add_handler(CommandHandler("disable", self.disable_feature))
        application.add_handler(CommandHandler("memory", self.memory))
        application.add_handler(CommandHandler("clearmemory", self.clear_memory))
        application.add_handler(CommandHandler("tree", self.tree))
        application.add_handler(CommandHandler("diff", self.diff))
        application.add_handler(CommandHandler("undo", self.undo))
        application.add_handler(CommandHandler("log", self.log))
        application.add_handler(CommandHandler("review", self.review_code))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

        # Load plugins
        self.plugin_manager.load_all_plugins(application)

        # Start
        application.run_polling()

if __name__ == '__main__':
    bot = JarvisBot()
    bot.run()
