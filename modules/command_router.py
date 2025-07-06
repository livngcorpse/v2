from pyrogram import filters
from pyrogram.enums import ParseMode
from core.role_manager import is_owner
import os
from core.task_manager import diff_file, restore_file
from memory.memory_manager import revert_task

def register_commands(bot):

    @bot.on_message(filters.command("modules") & filters.private)
    async def list_modules(client, message):
        if not is_owner(message.from_user.id):
            return await message.reply("❌ Access denied.")
        files = os.listdir("modules")
        py_modules = [f[:-3] for f in files if f.endswith(".py")]
        await message.reply("\n".join([f"• {mod}" for mod in py_modules]) or "No modules.")

    @bot.on_message(filters.command("delete") & filters.private)
    async def delete_module(client, message):
        if not is_owner(message.from_user.id):
            return await message.reply("❌ Access denied.")
        if len(message.command) < 2:
            return await message.reply("Usage: /delete <mod>")
        mod_name = message.command[1]
        path = f"modules/{mod_name}.py"
        if os.path.exists(path):
            os.remove(path)
            await message.reply(f"🗑 Deleted `{mod_name}.py`")
        else:
            await message.reply("❌ Not found.")

    @bot.on_message(filters.command("diff") & filters.private)
    async def diff_command(client, message):
        if len(message.command) < 2:
            return await message.reply("Usage: /diff <file>")
        file = message.command[1]
        try:
            result = diff_file(file)
            await message.reply(f"```diff\n{result}```", parse_mode="markdown")
        except Exception as e:
            await message.reply(f"Error: {e}")

    @bot.on_message(filters.command("undo") & filters.private)
    async def undo_command(client, message):
        if len(message.command) < 2:
            return await message.reply("Usage: /undo <file|task ID>")
        arg = message.command[1]
        if arg.isdigit():
            success, msg = revert_task(int(arg))
        else:
            success = restore_file(arg)
            msg = "Restored." if success else "Backup not found."
        await message.reply(msg)

    @bot.on_message(filters.command("review") & filters.private)
    async def review_command(client, message):
        if len(message.command) < 2:
            return await message.reply("Usage: /review <file>")
        path = message.command[1]
        if not os.path.exists(path):
            return await message.reply("File not found.")
        with open(path, 'r') as f:
            code = f.read()
        from core.ai_engine import model
        prompt = f"Review this Pyrogram bot module code and provide concise suggestions:\n{code}"
        response = model.generate_content(prompt)
        await message.reply(response.text)
