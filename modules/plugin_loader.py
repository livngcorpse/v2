import os
import importlib.util

def load_plugins(bot):
    folder = "plugins"
    for file in os.listdir(folder):
        if file.endswith(".py"):
            path = os.path.join(folder, file)
            name = file[:-3]
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            mod.bot = bot
            spec.loader.exec_module(mod)