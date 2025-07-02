import logging
import traceback
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self):
        self.error_log_path = Path('logs/errors.log')
        self.error_log_path.parent.mkdir(exist_ok=True)

    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle errors and log them"""
        try:
            # Log error details
            error_msg = f"Error: {str(error)}\nTraceback: {traceback.format_exc()}"
            self.log_error(error_msg, update)
            
            # Send user-friendly message
            if update and update.message:
                await update.message.reply_text("❌ An error occurred. Please try again or contact support.")
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    def log_error(self, error_msg, update=None):
        """Log error to file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_info = ""
            
            if update and update.effective_user:
                user_info = f"User: {update.effective_user.id} ({update.effective_user.username})"
            
            log_entry = f"[{timestamp}] {user_info}\n{error_msg}\n{'-'*50}\n"
            
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    async def log_activity(self, activity_type, details):
        """Log AI activity"""
        try:
            activity_log_path = Path('logs/ai_activity.log')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_entry = f"[{timestamp}] {activity_type}: {details}\n"
            
            with open(activity_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")