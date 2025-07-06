from pyrogram import Client, filters  # ADDED: filters import
from config.settings import API_ID, API_HASH, BOT_TOKEN
from core.role_manager import set_bot_instance, is_dev, is_owner, access_mode  # ADDED: is_owner, access_mode
from modules.command_router import register_commands
from modules.plugin_loader import load_plugins
from core.intent_classifier import intent_classifier
from jarvis_engine import jarvis_engine
from core.sandbox_manager import sandbox_manager
from memory.access_control import has_access
from memory.memory_manager import get_pending_tasks
from memory.conversation_manager import get_chat_memory, save_chat_memory  # ADDED: conversation memory imports
import os
import json

bot = Client("JarvisBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
set_bot_instance(bot)

# ADDED: Basic Commands
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply("🤖 **JARVIS Bot** - AI Assistant\n\nSend me natural language requests to build features, ask questions, or chat!")

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    user_id = message.from_user.id
    if is_dev(user_id):
        help_text = """
🔧 **Developer Commands:**
/memory - Show recent AI tasks
/diff <file> - Show file changes
/undo <file> - Restore file backup
/plugins - List all plugins
/info - Bot status
/clearhistory - Clear chat memory
        """
    else:
        help_text = """
💬 **Available Commands:**
/start - Welcome message
/help - Show this help
/info - Bot information
/clearhistory - Clear chat history
        """
    await message.reply(help_text)

@bot.on_message(filters.command("info") & filters.private)
async def info_command(client, message):
    user_id = message.from_user.id
    role = "Owner" if is_owner(user_id) else "Developer" if is_dev(user_id) else "Public"
    mode = access_mode()
    
    # Count plugins
    plugin_count = len([f for f in os.listdir("plugins") if os.path.isdir(os.path.join("plugins", f))]) if os.path.exists("plugins") else 0
    
    info_text = f"""
🤖 **JARVIS Bot Status**
👤 Your Role: {role}
🔒 Access Mode: {mode}
🔌 Plugins: {plugin_count}
📁 Sandbox Tasks: {len(get_pending_tasks(user_id))}
    """
    await message.reply(info_text)

@bot.on_message(filters.command("clearhistory") & filters.private)
async def clear_history_command(client, message):
    save_chat_memory(message.from_user.id, [])
    await message.reply("✅ Chat history cleared!")

@bot.on_message(filters.command("memory") & filters.private)
async def memory_command(client, message):
    if not is_dev(message.from_user.id):
        await message.reply("❌ Developer access required.")
        return
    
    tasks = get_pending_tasks(message.from_user.id)
    if not tasks:
        await message.reply("📝 No pending tasks.")
        return
    
    memory_text = "📝 **Recent Tasks:**\n\n"
    for task in tasks[-5:]:  # Show last 5 tasks
        memory_text += f"🔹 Task {task['id']}: {len(task.get('files', []))} files\n"
    
    await message.reply(memory_text)

@bot.on_message(filters.command("plugins") & filters.private)
async def plugins_command(client, message):
    if not is_dev(message.from_user.id):
        await message.reply("❌ Developer access required.")
        return
    
    if not os.path.exists("plugins"):
        await message.reply("🔌 No plugins directory found.")
        return
        
    plugins = [f for f in os.listdir("plugins") if os.path.isdir(os.path.join("plugins", f))]
    
    if not plugins:
        await message.reply("🔌 No plugins found.")
        return
    
    plugin_text = "🔌 **Installed Plugins:**\n\n"
    for plugin in plugins:
        plugin_text += f"▫️ {plugin}\n"
    
    await message.reply(plugin_text)

# EXISTING: Main message handler with ADDED conversation memory integration
@bot.on_message(filters.text & filters.private)
async def handle_message(client, message):
    """Main message handler for natural language processing"""
    
    user_id = message.from_user.id
    user_text = message.text
    
    # Check access
    if not has_access(user_id):
        await message.reply("❌ Access denied.")
        return
    
    # Classify intent
    intent, metadata = intent_classifier.classify_intent(
        user_text, 
        user_id, 
        is_dev=is_dev(user_id)
    )
    
    # Handle different intents
    if intent == "CREATE":
        await handle_create_intent(client, message, user_text)
    elif intent == "INTEGRATE":
        await handle_integrate_intent(client, message, metadata)
    elif intent == "CONVERSATION":
        await handle_conversation(client, message, user_text)
    elif intent == "QUESTION":
        await handle_question(client, message, user_text)
    elif intent == "CLARIFY":
        await message.reply(metadata.get("question", "Please clarify your request."))
    else:
        await handle_conversation(client, message, user_text)

async def handle_create_intent(client, message, user_text):
    """Handle code creation requests"""
    
    await message.reply("🔧 Generating code...")
    
    # Generate code using AI
    result = jarvis_engine.generate_code(user_text)
    
    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return
    
    # Create sandbox files
    task_info = sandbox_manager.create_sandbox_files(result, message.from_user.id)
    
    if task_info["errors"]:
        error_msg = "⚠️ Code generated with issues:\n"
        for error in task_info["errors"]:
            error_msg += f"• {error}\n"
        await message.reply(error_msg)
    else:
        await message.reply(f"✅ Code generated! Task ID: {task_info['id']}\nSay 'integrate it' to move to plugins.")

async def handle_integrate_intent(client, message, metadata):
    """Handle integration requests"""
    
    pending_tasks = metadata.get("pending_tasks", [])
    
    if not pending_tasks:
        await message.reply("❌ No pending tasks to integrate.")
        return
    
    # Get latest task
    latest_task = pending_tasks[-1]
    task_id = latest_task["id"]
    
    # Integrate to plugins
    result = sandbox_manager.integrate_to_plugins(task_id)
    
    if result["success"]:
        await message.reply(f"✅ Integrated to plugins/{result['plugin_name']}")
    else:
        await message.reply(f"❌ Integration failed: {result['error']}")

async def handle_conversation(client, message, user_text):
    """Handle general conversation - MODIFIED: Added conversation memory"""
    
    # Get and update conversation memory
    chat_memory = get_chat_memory(message.from_user.id)
    chat_memory.append({"role": "user", "content": user_text})
    
    response = jarvis_engine.generate_conversation_response(user_text)
    
    # Save response to memory
    chat_memory.append({"role": "assistant", "content": response})
    save_chat_memory(message.from_user.id, chat_memory)
    
    await message.reply(response)

async def handle_question(client, message, user_text):
    """Handle questions - MODIFIED: Added conversation memory"""
    
    # Get and update conversation memory
    chat_memory = get_chat_memory(message.from_user.id)
    chat_memory.append({"role": "user", "content": user_text})
    
    response = jarvis_engine.generate_conversation_response(user_text)
    
    # Save response to memory
    chat_memory.append({"role": "assistant", "content": response})
    save_chat_memory(message.from_user.id, chat_memory)
    
    await message.reply(response)

if __name__ == '__main__':
    load_plugins(bot)
    register_commands(bot)
    print("\n🚀 Jarvis is starting...")
    bot.run()
