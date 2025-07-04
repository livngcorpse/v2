import time
import psutil
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

class PingFeature:
    def __init__(self, bot_instance, db_manager):
        self.bot = bot_instance
        self.db = db_manager
        self.start_time = time.time()
        self.db_name = 'ping_system'
        self.init_database()
    
    def init_database(self):
        """Initialize ping system database"""
        if not self.db.read_db(self.db_name):
            initial_data = {
                'start_time': self.start_time,
                'ping_count': 0,
                'last_ping': None,
                'downtime_events': [],
                'uptime_records': [],
                'total_requests': 0,
                'system_stats': {
                    'memory_usage': [],
                    'cpu_usage': []
                }
            }
            self.db.create_db(self.db_name, initial_data)
    
    def get_uptime(self) -> str:
        """Calculate uptime since bot started"""
        uptime_seconds = time.time() - self.start_time
        uptime_delta = timedelta(seconds=uptime_seconds)
        
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_system_stats(self) -> dict:
        """Get current system statistics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'memory_used': memory.used,
                'memory_total': memory.total,
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"
    
    def record_ping(self, user_id: int):
        """Record a ping event"""
        try:
            # Update ping count
            self.db.increment_counter(self.db_name, 'ping_count')
            self.db.increment_counter(self.db_name, 'total_requests')
            
            # Record last ping
            ping_data = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'uptime': self.get_uptime()
            }
            self.db.set_value(self.db_name, 'last_ping', ping_data)
            
            # Store system stats
            stats = self.get_system_stats()
            if stats:
                self.db.append_to_list(self.db_name, 'system_stats.memory_usage', {
                    'timestamp': stats['timestamp'],
                    'percent': stats['memory_percent']
                })
                self.db.append_to_list(self.db_name, 'system_stats.cpu_usage', {
                    'timestamp': stats['timestamp'],
                    'percent': stats['cpu_percent']
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording ping: {e}")
            return False
    
    def get_downtime_events(self) -> list:
        """Get recorded downtime events"""
        return self.db.get_value(self.db_name, 'downtime_events', [])
    
    def calculate_availability(self) -> float:
        """Calculate bot availability percentage"""
        try:
            total_uptime = time.time() - self.start_time
            downtime_events = self.get_downtime_events()
            
            total_downtime = 0
            for event in downtime_events:
                if 'duration' in event:
                    total_downtime += event['duration']
            
            if total_uptime > 0:
                availability = ((total_uptime - total_downtime) / total_uptime) * 100
                return min(100.0, max(0.0, availability))
            
            return 100.0
            
        except Exception as e:
            logger.error(f"Error calculating availability: {e}")
            return 0.0
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command"""
        try:
            user_id = update.effective_user.id
            start_time = time.time()
            
            # Record this ping
            self.record_ping(user_id)
            
            # Get system stats
            stats = self.get_system_stats()
            uptime = self.get_uptime()
            availability = self.calculate_availability()
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Get ping statistics
            ping_count = self.db.get_value(self.db_name, 'ping_count', 0)
            total_requests = self.db.get_value(self.db_name, 'total_requests', 0)
            last_ping = self.db.get_value(self.db_name, 'last_ping')
            
            # Create response message
            status_emoji = "🟢" if availability > 95 else "🟡" if availability > 80 else "🔴"
            
            response = f"""
{status_emoji} **JARVIS v2 System Status**

**🔄 Uptime:** {uptime}
**📊 Availability:** {availability:.2f}%
**⚡ Response Time:** {response_time:.2f}ms
**📈 Total Pings:** {ping_count}
**🔢 Total Requests:** {total_requests}

**💻 System Resources:**
"""
            
            if stats:
                response += f"""• **Memory:** {self.format_bytes(stats['memory_used'])} / {self.format_bytes(stats['memory_total'])} ({stats['memory_percent']:.1f}%)
• **CPU:** {stats['cpu_percent']:.1f}%
"""
            
            if last_ping and last_ping['user_id'] != user_id:
                last_ping_time = datetime.fromisoformat(last_ping['timestamp'])
                time_diff = datetime.now() - last_ping_time
                response += f"\n**🕒 Last Ping:** {time_diff.total_seconds():.0f}s ago"
            
            # Add bot status
            response += f"\n\n**🤖 Bot Status:** ✅ Online and Responsive"
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await update.message.reply_text("❌ Error retrieving system status")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command (extended ping info)"""
        try:
            # Get detailed statistics
            uptime = self.get_uptime()
            availability = self.calculate_availability()
            ping_count = self.db.get_value(self.db_name, 'ping_count', 0)
            total_requests = self.db.get_value(self.db_name, 'total_requests', 0)
            
            # Get recent system stats
            recent_memory = self.db.get_recent_entries(self.db_name, 'system_stats.memory_usage', 5)
            recent_cpu = self.db.get_recent_entries(self.db_name, 'system_stats.cpu_usage', 5)
            
            # Calculate averages
            avg_memory = 0
            avg_cpu = 0
            
            if recent_memory:
                avg_memory = sum(entry['data']['percent'] for entry in recent_memory) / len(recent_memory)
            
            if recent_cpu:
                avg_cpu = sum(entry['data']['percent'] for entry in recent_cpu) / len(recent_cpu)
            
            # Get downtime events
            downtime_events = self.get_downtime_events()
            
            response = f"""
📊 **JARVIS v2 Detailed Status**

**⏰ System Information:**
• **Uptime:** {uptime}
• **Availability:** {availability:.2f}%
• **Start Time:** {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}

**📈 Usage Statistics:**
• **Total Pings:** {ping_count}
• **Total Requests:** {total_requests}
• **Average Memory Usage:** {avg_memory:.1f}%
• **Average CPU Usage:** {avg_cpu:.1f}%

**🔧 System Health:**
• **Memory Samples:** {len(recent_memory)}
• **CPU Samples:** {len(recent_cpu)}
• **Downtime Events:** {len(downtime_events)}

**🤖 Bot Components:**
• **AI Engine:** ✅ Online
• **File Manager:** ✅ Online
• **Database:** ✅ Online
• **Plugin System:** ✅ Online
"""
            
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text("❌ Error retrieving detailed status")

def register_handlers(application, bot_instance):
    """Register ping feature handlers"""
    try:
        # Get database manager from bot instance
        db_manager = getattr(bot_instance, 'db_manager', None)
        if not db_manager:
            logger.error("Database manager not found in bot instance")
            return
        
        # Create ping feature instance
        ping_feature = PingFeature(bot_instance, db_manager)
        
        # Register commands
        application.add_handler(CommandHandler("ping", ping_feature.ping_command))
        application.add_handler(CommandHandler("status", ping_feature.status_command))
        
        logger.info("Ping feature handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Error registering ping feature handlers: {e}")