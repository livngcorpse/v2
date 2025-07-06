from pyrogram import filters
from pyrogram.enums import ParseMode
from core.role_manager import is_owner
import os
from core.task_manager import diff_file, restore_file
from memory.memory_manager import revert_task
import json

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

    @bot.on_message(filters.command("memory") & filters.private)
    async def memory_command(client, message):
        if not is_dev(message.from_user.id):
            return await message.reply("❌ Access denied.")
        
        from memory.memory_manager import load_tasks
        tasks = load_tasks()[-10:]  # Last 10 tasks
        
        if not tasks:
            await message.reply("No tasks in memory.")
            return
        
        response = "📋 Recent Tasks:\n"
        for task in tasks:
            response += f"• Task {task['id']}: {task.get('status', 'unknown')}\n"
        
        await message.reply(response)

    @bot.on_message(filters.command("clearmemory") & filters.private)
    async def clear_memory_command(client, message):
        if not is_dev(message.from_user.id):
            return await message.reply("❌ Access denied.")
        
        with open("logs/memory.json", "w") as f:
            json.dump([], f)
        
        await message.reply("🧹 Memory cleared.")

    @bot.on_message(filters.command("plugins") & filters.private)
    async def plugins_command(client, message):
        if not is_dev(message.from_user.id):
            return await message.reply("❌ Access denied.")
        
        plugins_dir = "plugins"
        if not os.path.exists(plugins_dir):
            await message.reply("No plugins directory found.")
            return
        
        plugins = [d for d in os.listdir(plugins_dir) if os.path.isdir(os.path.join(plugins_dir, d))]
        
        if not plugins:
            await message.reply("No plugins found.")
            return
        
        response = "🔌 Available Plugins:\n"
        for plugin in plugins:
            response += f"• {plugin}\n"
        
        await message.reply(response)

    @bot.on_message(filters.command("adddev") & filters.private)
    async def add_dev_command(client, message):
        if not is_owner(message.from_user.id):
            return await message.reply("❌ Owner only.")
        
        if len(message.command) < 2:
            return await message.reply("Usage: /adddev <user_id>")
        
        try:
            user_id = int(message.command[1])
            
            with open("config/settings.json", "r") as f:
                settings = json.load(f)
            
            if user_id not in settings["devs"]:
                settings["devs"].append(user_id)
                
                with open("config/settings.json", "w") as f:
                    json.dump(settings, f, indent=2)
                
                await message.reply(f"✅ Added user {user_id} as developer.")
            else:
                await message.reply("User is already a developer.")
        
        except ValueError:
            await message.reply("Invalid user ID.")

    @bot.on_message(filters.command("removedev") & filters.private)
    async def remove_dev_command(client, message):
        if not is_owner(message.from_user.id):
            return await message.reply("❌ Owner only.")
        
        if len(message.command) < 2:
            return await message.reply("Usage: /removedev <user_id>")
        
        try:
            user_id = int(message.command[1])
            
            with open("config/settings.json", "r") as f:
                settings = json.load(f)
            
            if user_id in settings["devs"]:
                settings["devs"].remove(user_id)
                
                with open("config/settings.json", "w") as f:
                    json.dump(settings, f, indent=2)
                
                await message.reply(f"✅ Removed user {user_id} from developers.")
            else:
                await message.reply("User is not a developer.")
        
        except ValueError:
            await message.reply("Invalid user ID.")

    @bot.on_message(filters.command("access") & filters.private)
    async def access_command(client, message):
        if not is_owner(message.from_user.id):
            return await message.reply("❌ Owner only.")
        
        if len(message.command) < 2:
            current_mode = access_mode()
            await message.reply(f"Current access mode: {current_mode}")
            return
        
        mode = message.command[1].lower()
        if mode not in ["dev", "public"]:
            await message.reply("Usage: /access <dev|public>")
            return
        
        with open("config/settings.json", "r") as f:
            settings = json.load(f)
        
        settings["access"] = mode
        
        with open("config/settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        
        await message.reply(f"✅ Access mode set to: {mode}")
