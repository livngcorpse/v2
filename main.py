from pyrogram import Client
from config.settings import API_ID, API_HASH, BOT_TOKEN
from core.role_manager import set_bot_instance
from modules.command_router import register_commands
from modules.plugin_loader import load_plugins
from core.intent_classifier import intent_classifier
from jarvis_engine import jarvis_engine
from core.sandbox_manager import sandbox_manager
from memory.access_control import has_access
from memory.memory_manager import get_pending_tasks
import os
from core.role_manager import is_dev
import json

bot = Client("JarvisBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
set_bot_instance(bot)

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
    """Handle general conversation"""
    
    response = jarvis_engine.generate_conversation_response(user_text)
    await message.reply(response)

async def handle_question(client, message, user_text):
    """Handle questions"""
    
    response = jarvis_engine.generate_conversation_response(user_text)
    await message.reply(response)
if __name__ == '__main__':
    load_plugins(bot)
    register_commands(bot)
    print("\n🚀 Jarvis is starting...")
    bot.run()
