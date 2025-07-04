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
from dotenv import load_dotenv
load_dotenv()

# Import our custom modules
from jarvis_engine import JarvisEngine
from file_manager import FileManager
from error_handler import ErrorHandler
from db.db_manager import DatabaseManager
from plugin_manager import PluginManager

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
        
        # Initialize core components
        self.jarvis_engine = JarvisEngine()
        self.file_manager = FileManager()
        self.error_handler = ErrorHandler()
        self.db_manager = DatabaseManager()
        self.plugin_manager = PluginManager(self)
        
        # Configuration paths
        self.config_path = Path('config/settings.json')
        self.memory_path = Path('logs/memory.json')
        
        # Feature systems - both legacy and modern
        self.features = {}  # Legacy file-based features
        self.plugins = {}   # Modern plugin system
        
        # Initialize
        self.load_config()
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories"""
        dirs = ['features', 'bots', 'db', 'logs', 'uploads', 'config', 'plugins']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)

    def load_config(self):
        """Load bot configuration with enhanced error handling"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded successfully")
            else:
                self.config = {
                    'devs': [self.owner_id],
                    'access_mode': 'dev',
                    'personality': 'JARVIS v2 - Self-Evolving AI Assistant',
                    'features_enabled': True,
                    'plugins_enabled': True,
                    'auto_backup': True
                }
                self.save_config()
                logger.info("Default configuration created")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {
                'devs': [self.owner_id], 
                'access_mode': 'dev', 
                'personality': 'JARVIS v2',
                'features_enabled': True,
                'plugins_enabled': True
            }

    def save_config(self):
        """Save bot configuration"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

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
        """Handle /start command with interactive keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 Bot Info", callback_data='info')],
            [InlineKeyboardButton("📋 Help", callback_data='help')],
            [InlineKeyboardButton("🧠 Memory", callback_data='memory')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_msg = f"🧠 {self.config.get('personality', 'JARVIS v2')}\n\nReady to assist you with advanced AI capabilities!"
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command with comprehensive help"""
        help_text = """🔧 JARVIS v2 - Complete Command Reference:

📋 **Basic Commands:**
/start - Welcome message with interactive menu
/help - Complete command reference
/info - Bot status and statistics
/memory - View recent memory entries
/tree - Display folder structure

🔧 **Administration (Dev Only):**
/access <dev|public> - Toggle access mode
/adddev <user_id> - Add developer access
/removedev <user_id> - Remove developer access

🧠 **Memory Management:**
/clearmemory - Clear bot memory (Dev only)
/log - View AI activity logs

📁 **File Operations (Dev Only):**
/diff <file> - Show file changes
/undo <file> - Revert file changes
/review <file> - AI-powered code review

🔌 **Plugin Management (Dev Only):**
/enable <plugin> - Enable plugin
/disable <plugin> - Disable plugin
/plugins - List available plugins

🎯 **Legacy Features (Dev Only):**
/loadfeatures - Load file-based features
/features - List loaded features

💡 **Usage Tips:**
- In private chats: Send any message for AI processing
- In groups: Mention 'jarvis' to trigger AI
- Upload .txt files for project analysis
- Add captions to files for specific instructions"""

        await update.message.reply_text(help_text)

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command with detailed statistics"""
        mode = self.config.get('access_mode', 'dev')
        personality = self.config.get('personality', 'JARVIS v2')
        features_count = len(self.features)
        plugins_count = len(self.plugin_manager.enabled_plugins) if hasattr(self.plugin_manager, 'enabled_plugins') else 0
        
        info_text = f"""🤖 **{personality}**

📊 **Status:**
• Mode: {mode.upper()}
• Legacy Features: {features_count} loaded
• Modern Plugins: {plugins_count} active
• Memory Entries: {self.get_memory_count()}

🔧 **Capabilities:**
• AI Processing: ✅ Active
• File Management: ✅ Active
• Database: ✅ Connected
• Plugin System: ✅ Active

🛡️ **Access Control:**
• Developers: {len(self.config.get('devs', []))}
• Your Access: {'✅ Developer' if self.is_dev(update.effective_user.id) else '👤 User'}"""

        await update.message.reply_text(info_text)

    async def access_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /access command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        args = context.args
        if args and args[0] in ['dev', 'public']:
            old_mode = self.config.get('access_mode', 'dev')
            self.config['access_mode'] = args[0]
            self.save_config()
            await update.message.reply_text(f"✅ Access mode changed: {old_mode} → {args[0]}")
        else:
            current = self.config.get('access_mode', 'dev')
            await update.message.reply_text(f"📊 Current access mode: **{current}**\n\nUsage: `/access dev|public`")

    async def add_dev(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /adddev command"""
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/adddev <user_id>`")
            return

        try:
            user_id = int(context.args[0])
            if user_id not in self.config['devs']:
                self.config['devs'].append(user_id)
                self.save_config()
                await update.message.reply_text(f"✅ Developer added: {user_id}")
                logger.info(f"New developer added: {user_id}")
            else:
                await update.message.reply_text("⚠️ User is already a developer")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format")

    async def remove_dev(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removedev command"""
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/removedev <user_id>`")
            return

        try:
            user_id = int(context.args[0])
            if user_id in self.config['devs'] and user_id != self.owner_id:
                self.config['devs'].remove(user_id)
                self.save_config()
                await update.message.reply_text(f"✅ Developer removed: {user_id}")
                logger.info(f"Developer removed: {user_id}")
            else:
                await update.message.reply_text("❌ Cannot remove owner or user not found")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format")

    async def memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memory command with enhanced display"""
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
                    if memory_data:
                        memory_text = "🧠 **Recent Memory Entries:**\n\n"
                        for i, item in enumerate(memory_data[-10:], 1):
                            task = item.get('task', 'Unknown')[:50] + "..." if len(item.get('task', '')) > 50 else item.get('task', 'Unknown')
                            memory_text += f"{i}. {task}\n"
                        
                        memory_text += f"\n📊 Total entries: {len(memory_data)}"
                        await update.message.reply_text(memory_text)
                    else:
                        await update.message.reply_text("🧠 Memory is empty")
            else:
                await update.message.reply_text("🧠 No memory file found")
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            await update.message.reply_text(f"❌ Error accessing memory: {str(e)}")

    async def clear_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clearmemory command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        try:
            # Create backup before clearing
            if self.memory_path.exists() and self.config.get('auto_backup', True):
                backup_path = Path(f'logs/memory_backup_{int(asyncio.get_event_loop().time())}.json')
                import shutil
                shutil.copy2(self.memory_path, backup_path)
                logger.info(f"Memory backup created: {backup_path}")

            with open(self.memory_path, 'w') as f:
                json.dump([], f)
            
            await update.message.reply_text("✅ Memory cleared successfully\n💾 Backup created automatically")
            logger.info("Memory cleared by user")
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            await update.message.reply_text(f"❌ Error clearing memory: {str(e)}")

    async def tree(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tree command with enhanced structure"""
        tree_text = """📁 **JARVIS Bot Directory Structure:**

```
JARVIS-Bot/
├── 📁 features/          # Legacy file-based features
├── 📁 plugins/           # Modern plugin system
├── 📁 bots/              # Bot instances
├── 📁 db/                # Database files
├── 📁 logs/              # Activity & memory logs
├── 📁 uploads/           # User uploaded files
├── 📁 config/            # Configuration files
├── 📄 main.py            # Core bot file
├── 📄 jarvis_engine.py   # AI processing engine
├── 📄 file_manager.py    # File operations
├── 📄 error_handler.py   # Error management
├── 📄 db_manager.py      # Database operations
└── 📄 plugin_manager.py  # Plugin management
```"""
        await update.message.reply_text(tree_text)

    async def diff(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /diff command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/diff <filename>`")
            return

        filename = context.args[0]
        try:
            diff_result = self.file_manager.show_diff(filename)
            await update.message.reply_text(f"🔍 **Diff for {filename}:**\n```\n{diff_result}\n```", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await update.message.reply_text(f"❌ Error showing diff: {str(e)}")

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /undo command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/undo <filename>`")
            return

        filename = context.args[0]
        try:
            success = self.file_manager.undo_changes(filename)
            if success:
                await update.message.reply_text(f"✅ Successfully reverted changes to {filename}")
            else:
                await update.message.reply_text(f"❌ Could not revert {filename} - no backup found")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reverting file: {str(e)}")

    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /log command with enhanced logging"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        log_file = Path('logs/ai_activity.log')
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    recent_logs = f.readlines()[-15:]
                    log_text = "📋 **Recent AI Activity:**\n\n```\n" + "".join(recent_logs) + "\n```"
                    await update.message.reply_text(log_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("📋 No activity logs found")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reading logs: {str(e)}")

    # Modern Plugin System Commands
    async def enable_plugin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /enable command for plugins"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/enable <plugin_name>`")
            return

        plugin_name = context.args[0]
        try:
            if self.plugin_manager.enable_plugin(plugin_name, context.application):
                await update.message.reply_text(f"✅ Plugin '{plugin_name}' enabled and loaded successfully")
                logger.info(f"Plugin enabled: {plugin_name}")
            else:
                await update.message.reply_text(f"❌ Failed to enable plugin '{plugin_name}'")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enabling plugin: {str(e)}")

    async def disable_plugin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /disable command for plugins"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/disable <plugin_name>`")
            return

        plugin_name = context.args[0]
        try:
            if self.plugin_manager.disable_plugin(plugin_name):
                await update.message.reply_text(f"❌ Plugin '{plugin_name}' disabled successfully")
                logger.info(f"Plugin disabled: {plugin_name}")
            else:
                await update.message.reply_text(f"⚠️ Failed to disable plugin '{plugin_name}'")
        except Exception as e:
            await update.message.reply_text(f"❌ Error disabling plugin: {str(e)}")

    async def list_plugins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugins command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        try:
            enabled_plugins = getattr(self.plugin_manager, 'enabled_plugins', {})
            available_plugins = self.plugin_manager.get_available_plugins() if hasattr(self.plugin_manager, 'get_available_plugins') else []
            
            plugin_text = "🔌 **Plugin Status:**\n\n"
            plugin_text += f"**Enabled Plugins ({len(enabled_plugins)}):**\n"
            for plugin_name in enabled_plugins:
                plugin_text += f"✅ {plugin_name}\n"
            
            plugin_text += f"\n**Available Plugins ({len(available_plugins)}):**\n"
            for plugin_name in available_plugins:
                status = "✅" if plugin_name in enabled_plugins else "❌"
                plugin_text += f"{status} {plugin_name}\n"
            
            await update.message.reply_text(plugin_text)
        except Exception as e:
            await update.message.reply_text(f"❌ Error listing plugins: {str(e)}")

    # Legacy Feature System Commands
    async def load_features(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /loadfeatures command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        try:
            loaded_count = self.load_legacy_features()
            await update.message.reply_text(f"✅ Loaded {loaded_count} legacy features")
        except Exception as e:
            await update.message.reply_text(f"❌ Error loading features: {str(e)}")

    async def list_features(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /features command"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        feature_text = f"🎯 **Legacy Features ({len(self.features)}):**\n\n"
        for feature_name in self.features:
            feature_text += f"✅ {feature_name}\n"
        
        await update.message.reply_text(feature_text)

    async def review_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /review command with AI-powered code review"""
        if not self.is_dev(update.effective_user.id):
            await update.message.reply_text("❌ Developer access required")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/review <filename>`")
            return

        filename = context.args[0]
        try:
            # AI-powered code review implementation
            file_path = Path(filename)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    code_content = f.read()
                
                # Send to AI for review
                review_prompt = f"Please review this code for security, performance, and best practices:\n\n{code_content}"
                review_result = await self.jarvis_engine.process_prompt(review_prompt)
                
                await update.message.reply_text(f"🔍 **Code Review for {filename}:**\n\n{review_result}")
            else:
                await update.message.reply_text(f"❌ File not found: {filename}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reviewing code: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages with enhanced logic"""
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
        """Handle file uploads with smart processing"""
        user_id = update.effective_user.id
        
        if not self.has_access(user_id):
            return

        document = update.message.document
        caption = update.message.caption or ""
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_path = Path(f'uploads/{document.file_name}')
            await file.download_to_drive(file_path)

            # Smart processing based on file type and caption
            if document.file_name.endswith('.txt'):
                if caption:
                    # File + caption: Use caption as task, file as context
                    await self.process_ai_file_request(update, context, file_path, caption)
                else:
                    # .txt file only: AI reads and responds with special message
                    await update.message.reply_text("🤖 I understood the project. Starting build…")
                    await self.process_ai_file_request(update, context, file_path, "Analyze this project and build it")
            else:
                # Other files: Use caption or default instruction
                instruction = caption or "Analyze this file and provide insights"
                await self.process_ai_file_request(update, context, file_path, instruction)
                
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def process_ai_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process AI requests with enhanced features"""
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
                await update.message.reply_text("✅ File processed successfully")
                
        except Exception as e:
            await self.error_handler.handle_error(update, context, e)

    async def execute_file_operations(self, files_dict):
        """Execute file creation/modification operations"""
        for file_path, content in files_dict.items():
            try:
                self.file_manager.write_file(file_path, content)
                logger.info(f"File operation completed: {file_path}")
            except Exception as e:
                logger.error(f"Error in file operation for {file_path}: {e}")

    def log_memory(self, task, response):
        """Log task to memory with enhanced data"""
        try:
            memory_data = []
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
            
            memory_data.append({
                'timestamp': str(asyncio.get_event_loop().time()),
                'task': task[:100],  # Truncate long tasks
                'response_type': type(response).__name__,
                'success': True
            })
            
            # Keep only last 100 entries
            memory_data = memory_data[-100:]
            
            with open(self.memory_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging memory: {e}")

    def get_memory_count(self):
        """Get current memory entry count"""
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
                    return len(memory_data)
            return 0
        except:
            return 0

    def load_legacy_features(self):
        """Load legacy feature plugins from features directory"""
        features_dir = Path('features')
        if not features_dir.exists():
            return 0

        loaded_count = 0
        for feature_path in features_dir.iterdir():
            if feature_path.is_dir():
                handler_file = feature_path / 'handler.py'
                if handler_file.exists():
                    if self.load_feature_module(str(handler_file), feature_path.name):
                        loaded_count += 1
        
        return loaded_count

    def load_feature_module(self, file_path, feature_name):
        """Load a legacy feature module"""
        try:
            spec = importlib.util.spec_from_file_location(feature_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if module has register_handlers function
            if hasattr(module, 'register_handlers'):
                self.features[feature_name] = module
                logger.info(f"Loaded legacy feature: {feature_name}")
                return True
            
        except Exception as e:
            logger.error(f"Error loading legacy feature {feature_name}: {e}")
        
        return False

    def run(self):
        """Run the bot with complete initialization"""
        try:
            application = Application.builder().token(self.token).build()

            # Register all command handlers
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
            
            # Modern plugin system
            application.add_handler(CommandHandler("enable", self.enable_plugin))
            application.add_handler(CommandHandler("disable", self.disable_plugin))
            application.add_handler(CommandHandler("plugins", self.list_plugins))
            
            # Legacy feature system
            application.add_handler(CommandHandler("loadfeatures", self.load_features))
            application.add_handler(CommandHandler("features", self.list_features))
            
            # Advanced commands
            application.add_handler(CommandHandler("review", self.review_code))

            # Message handlers
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

            # Load both legacy features and modern plugins
            if self.config.get('features_enabled', True):
                legacy_count = self.load_legacy_features()
                logger.info(f"Loaded {legacy_count} legacy features")

            if self.config.get('plugins_enabled', True):
                plugin_count = self.plugin_manager.load_plugins(application)
                logger.info(f"Loaded {plugin_count} modern plugins")

            # Register legacy feature handlers
            for feature_name, feature_module in self.features.items():
                if hasattr(feature_module, 'register_handlers'):
                    try:
                        feature_module.register_handlers(application)
                        logger.info(f"Registered handlers for feature: {feature_name}")
                    except Exception as e:
                        logger.error(f"Error registering handlers for {feature_name}: {e}")

            # Add error handler
            application.add_error_handler(self.error_handler.handle_error)

            # Initialize database
            self.db_manager.initialize()

            # Start the bot
            logger.info("Starting JARVIS Bot...")
            logger.info(f"Owner ID: {self.owner_id}")
            logger.info(f"Access Mode: {self.config.get('access_mode', 'dev')}")
            logger.info(f"Features Enabled: {self.config.get('features_enabled', True)}")
            logger.info(f"Plugins Enabled: {self.config.get('plugins_enabled', True)}")
            
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Fatal error starting bot: {e}")
            raise

if __name__ == "__main__":
    try:
        bot = JarvisBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise