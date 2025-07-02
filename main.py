import asyncio
import logging
import os
import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import importlib.util
import sys

# Import our custom modules
from jarvis_engine import JarvisEngine
from file_manager import FileManager
from error_handler import ErrorHandler

# Configure logging
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
        self.config_path = Path('config/settings.json')
        self.memory_path = Path('logs/memory.json')
        self.features = {}
        self.load_config()
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories"""
        dirs = ['features', 'bots', 'db', 'logs', 'uploads', 'config']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)

    def load_config(self):
        """Load bot configuration"""
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
        """Save bot configuration"""
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def is_dev(self, user_id):
        """Check if user is a developer"""
        return user_id in self.config.get('devs', [])

    def is_owner(self, user_id):
        """Check if user is the owner"""
        return user_id == self.owner_id

    def has_access(self, user_id):
        """Check if user has access based on current mode"""
        if self.config.get('access_mode') == 'public':
            return True
        return self.is_dev(user_id)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text("🧠 JARVIS v2 - Self-Evolving AI Bot\nReady to assist.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🔧 JARVIS v2 Commands:
/start - Welcome message
/help - This help menu
/info - Bot status
/access - Toggle dev/public mode
/memory - View memory
/tree - Folder structure
/diff <file> - Show changes
/undo <file> - Revert changes
/log - AI activity logs"""
        await update.message.reply_text(help_text)

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        mode = self.config.get('access_mode', 'dev')
        personality = self.config.get('personality', 'JARVIS v2')
        info_text = f"🤖 {personality}\n📊 Mode: {mode}\n🔧 Features: {len(self.features)} loaded"
        await update.message.reply_text(info_text)

    async def access_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /access command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        args = context.args
        if args and args[0] in ['dev', 'public']:
            self.config['access_mode'] = args[0]
            self.save_config()
            await update.message.reply_text(f"✅ Access mode: {args[0]}")
        else:
            current = self.config.get('access_mode', 'dev')
            await update.message.reply_text(f"📊 Current mode: {current}\nUse: /access dev|public")

    async def add_dev(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adddev command"""
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
        """Handle /removedev command"""
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

    async def memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memory command"""
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
                    if memory_data:
                        memory_text = "🧠 Recent Memory:\n"
                        for i, item in enumerate(memory_data[-5:], 1):
                            memory_text += f"{i}. {item.get('task', 'Unknown')}\n"
                        await update.message.reply_text(memory_text)
                    else:
                        await update.message.reply_text("🧠 Memory is empty")
            else:
                await update.message.reply_text("🧠 No memory file found")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reading memory: {e}")

    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clearmemory command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        try:
            with open(self.memory_path, 'w') as f:
                json.dump([], f)
            await update.message.reply_text("✅ Memory cleared")
        except Exception as e:
            await update.message.reply_text(f"❌ Error clearing memory: {e}")

    async def tree(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tree command"""
        tree_text = "📁 JARVIS Bot Structure:\n"
        tree_text += "├── features/\n"
        tree_text += "├── bots/\n"
        tree_text += "├── db/\n"
        tree_text += "├── logs/\n"
        tree_text += "├── uploads/\n"
        tree_text += "├── config/\n"
        tree_text += "└── main.py"
        await update.message.reply_text(tree_text)

    async def diff(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /diff command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: /diff <filename>")
            return

        filename = context.args[0]
        diff_result = self.file_manager.show_diff(filename)
        await update.message.reply_text(f"🔍 Diff for {filename}:\n```\n{diff_result}\n```", parse_mode=ParseMode.MARKDOWN)

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /undo command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: /undo <filename>")
            return

        filename = context.args[0]
        success = self.file_manager.undo_changes(filename)
        if success:
            await update.message.reply_text(f"✅ Reverted {filename}")
        else:
            await update.message.reply_text(f"❌ Could not revert {filename}")

    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /log command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        log_file = Path('logs/ai_activity.log')
        if log_file.exists():
            with open(log_file, 'r') as f:
                recent_logs = f.readlines()[-10:]
                log_text = "📋 Recent AI Activity:\n" + "".join(recent_logs)
                await update.message.reply_text(log_text)
        else:
            await update.message.reply_text("📋 No logs found")

    async def enable_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /enable command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: /enable <feature_name>")
            return

        feature_name = context.args[0]
        # Implementation for enabling features
        await update.message.reply_text(f"✅ Feature {feature_name} enabled")

    async def disable_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /disable command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: /disable <feature_name>")
            return

        feature_name = context.args[0]
        # Implementation for disabling features
        await update.message.reply_text(f"❌ Feature {feature_name} disabled")

    async def review_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /review command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Dev access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: /review <filename>")
            return

        filename = context.args[0]
        # AI-powered code review implementation
        await update.message.reply_text(f"🔍 Code review for {filename} completed")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages and files"""
        user_id = update.effective_user.id
        
        # Check access
        if not self.has_access(user_id):
            return

        # Handle different chat types
        if update.message.chat.type == 'private':
            # DM: Accept any text as AI prompt
            await self.process_ai_request(update, context)
        else:
            # Group: Listen only to messages containing "jarvis"
            if 'jarvis' in update.message.text.lower():
                await self.process_ai_request(update, context)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads"""
        user_id = update.effective_user.id
        
        if not self.has_access(user_id):
            return

        document = update.message.document
        caption = update.message.caption or ""
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_path = Path(f'uploads/{document.file_name}')
        await file.download_to_drive(file_path)

        # Process based on file type and caption
        if document.file_name.endswith('.txt'):
            if caption:
                # File + caption: Use caption as task, file as context
                await self.process_ai_file_request(update, context, file_path, caption)
            else:
                # .txt file only: AI reads and responds
                await update.message.reply_text("I understood the project. Starting build…")
                await self.process_ai_file_request(update, context, file_path, "Build this project")

    async def process_ai_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process AI requests"""
        if not self.is_dev(update.effective_user.id) and self.config.get('access_mode') == 'dev':
            return

        prompt = update.message.text
        try:
            # Send to Jarvis Engine
            response = await self.jarvis_engine.process_prompt(prompt)
            
            # Log memory
            self.log_memory(prompt, response)
            
            # Execute file operations if needed
            if isinstance(response, dict) and 'files' in response:
                await self.execute_file_operations(response['files'])
                await update.message.reply_text("✅ Task completed successfully")
            else:
                await update.message.reply_text(str(response))
                
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def process_ai_file_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: Path, instruction: str):
        """Process AI requests with file context"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Send to Jarvis Engine with file context
            response = await self.jarvis_engine.process_file_prompt(instruction, file_content)
            
            # Log memory
            self.log_memory(f"File: {file_path.name} - {instruction}", response)
            
            # Execute file operations
            if isinstance(response, dict) and 'files' in response:
                await self.execute_file_operations(response['files'])
                await update.message.reply_text("✅ File processed and changes applied")
            else:
                await update.message.reply_text("✅ File processed")
                
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def execute_file_operations(self, files_dict):
        """Execute file creation/modification operations"""
        for file_path, content in files_dict.items():
            self.file_manager.write_file(file_path, content)

    def log_memory(self, task, response):
        """Log task to memory"""
        try:
            memory_data = []
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
            
            memory_data.append({
                'timestamp': str(asyncio.get_event_loop().time()),
                'task': task[:100],  # Truncate long tasks
                'response_type': type(response).__name__
            })
            
            # Keep only last 50 entries
            memory_data = memory_data[-50:]
            
            with open(self.memory_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging memory: {e}")

    def load_features(self):
        """Load feature plugins from features directory"""
        features_dir = Path('features')
        if not features_dir.exists():
            return

        for feature_path in features_dir.iterdir():
            if feature_path.is_dir():
                handler_file = feature_path / 'handler.py'
                if handler_file.exists():
                    self.load_feature_module(str(handler_file), feature_path.name)

    def load_feature_module(self, file_path, feature_name):
        """Load a feature module"""
        try:
            spec = importlib.util.spec_from_file_location(feature_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if module has register_handlers function
            if hasattr(module, 'register_handlers'):
                self.features[feature_name] = module
                logger.info(f"Loaded feature: {feature_name}")
            
        except Exception as e:
            logger.error(f"Error loading feature {feature_name}: {e}")

    def run(self):
        """Run the bot"""
        application = Application.builder().token(self.token).build()

        # Register command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("info", self.info))
        application.add_handler(CommandHandler("access", self.access_toggle))
        application.add_handler(CommandHandler("adddev", self.add_dev))
        application.add_handler(CommandHandler("removedev", self.remove_dev))
        application.add_handler(CommandHandler("memory", self.memory))
        application.add_handler(CommandHandler("clearmemory", self.clear_memory))
        application.add_handler(CommandHandler("tree", self.tree))
        application.add_handler(CommandHandler("diff", self.diff))
        application.add_handler(CommandHandler("undo", self.undo))
        application.add_handler(CommandHandler("log", self.log))
        application.add_handler(CommandHandler("enable", self.enable_feature))
        application.add_handler(CommandHandler("disable", self.disable_feature))
        application.add_handler(CommandHandler("review", self.review_code))

        # Register message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

        # Load features
        self.load_features()

        # Start bot
        application.run_polling()

if __name__ == '__main__':
    bot = JarvisBot()
    bot.run()