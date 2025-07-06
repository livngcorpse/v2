from pyrogram import Client, filters
from config.settings import API_ID, API_HASH, BOT_TOKEN
from core.role_manager import set_bot_instance, is_dev
from modules.command_router import register_commands
from modules.plugin_loader import load_plugins
from core.intent_classifier import intent_classifier
from jarvis_engine import jarvis_engine  # Updated import
from core.sandbox_manager import sandbox_manager
from memory.access_control import has_access
from memory.memory_manager import get_pending_tasks
from memory.conversation_manager import get_chat_memory, save_chat_memory

bot = Client("JarvisBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
set_bot_instance(bot)


@bot.on_message(filters.text & filters.private)
async def handle_message(client, message):
    user_id = message.from_user.id
    user_text = message.text

    if not has_access(user_id):
        await message.reply("❌ Access denied.")
        return

    # Intent classification
    intent, metadata = intent_classifier.classify_intent(
        user_text, user_id, is_dev=is_dev(user_id)
    )

    if intent == "CREATE":
        await handle_create_intent(client, message, user_text)
    elif intent == "EDIT":
        await handle_edit_intent(client, message, user_text)
    elif intent == "RECODE":
        await handle_recode_intent(client, message, user_text)
    elif intent == "INTEGRATE":
        await handle_integrate_intent(client, message, metadata)
    elif intent in ("CONVERSATION", "QUESTION"):
        await handle_conversation(client, message, user_text)
    elif intent == "CLARIFY":
        await message.reply(metadata.get("question", "Please clarify your request."))
    else:
        await handle_conversation(client, message, user_text)


async def handle_create_intent(client, message, user_text):
    await message.reply("🔧 Generating code...")
    result = jarvis_engine.generate_code(user_text, task_type="CREATE")

    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return

    task_info = sandbox_manager.create_sandbox_files(result, message.from_user.id)
    if task_info["errors"]:
        error_msg = "\n".join([f"• {e.get('message', str(e))}" for e in task_info["errors"]])
        await message.reply(f"⚠️ Generated with issues:\n{error_msg}")
    else:
        await message.reply(f"✅ Code generated! Task ID: {task_info['id']}\nSay 'integrate it' to move to plugins.")


async def handle_edit_intent(client, message, user_text):
    await message.reply("🔧 Editing code...")
    result = jarvis_engine.generate_code(user_text, task_type="EDIT")

    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return

    task_info = sandbox_manager.create_sandbox_files(result, message.from_user.id)
    if task_info["errors"]:
        error_msg = "\n".join([f"• {e.get('message', str(e))}" for e in task_info["errors"]])
        await message.reply(f"⚠️ Edited with issues:\n{error_msg}")
    else:
        await message.reply(f"✅ Code edited! Task ID: {task_info['id']}\nSay 'integrate it' to move to plugins.")


async def handle_recode_intent(client, message, user_text):
    await message.reply("🔧 Recoding from scratch...")
    result = jarvis_engine.generate_code(user_text, task_type="RECODE")

    if "error" in result:
        await message.reply(f"❌ Error: {result['error']}")
        return

    task_info = sandbox_manager.create_sandbox_files(result, message.from_user.id)
    if task_info["errors"]:
        error_msg = "\n".join([f"• {e.get('message', str(e))}" for e in task_info["errors"]])
        await message.reply(f"⚠️ Recoded with issues:\n{error_msg}")
    else:
        await message.reply(f"✅ Code recoded! Task ID: {task_info['id']}\nSay 'integrate it' to move to plugins.")


async def handle_integrate_intent(client, message, metadata):
    pending_tasks = metadata.get("pending_tasks", [])
    if not pending_tasks:
        await message.reply("❌ No pending tasks to integrate.")
        return

    latest_task = pending_tasks[-1]
    result = sandbox_manager.integrate_to_plugins(latest_task["id"])

    if result["success"]:
        await message.reply(f"✅ Integrated to `plugins/{result['plugin_name']}`.")
    else:
        await message.reply(f"❌ Integration failed: {result['error']}")


async def handle_conversation(client, message, user_text):
    memory = get_chat_memory(message.from_user.id)
    memory.append({"role": "user", "content": user_text})

    response = jarvis_engine.generate_conversation_response(user_text, memory)

    memory.append({"role": "assistant", "content": response})
    save_chat_memory(message.from_user.id, memory)

    await message.reply(response)


if __name__ == "__main__":
    load_plugins(bot)
    register_commands(bot)
    print("🚀 Jarvis is starting...")
    bot.run()
