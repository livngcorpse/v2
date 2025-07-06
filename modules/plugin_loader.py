import os
import importlib.util
import json

def load_plugins(bot):
    folder = "plugins"
    disabled_path = "config/disabled_plugins.json"

    # Load disabled plugins
    disabled = []
    if os.path.exists(disabled_path):
        with open(disabled_path, "r") as f:
            disabled = json.load(f)

    for plugin_name in os.listdir(folder):
        plugin_dir = os.path.join(folder, plugin_name)

        # Skip non-directories and disabled plugins
        if not os.path.isdir(plugin_dir) or plugin_name in disabled:
            continue

        handler_path = os.path.join(plugin_dir, "handler.py")
        if not os.path.exists(handler_path):
            print(f"[WARN] Plugin '{plugin_name}' missing handler.py")
            continue

        try:
            spec = importlib.util.spec_from_file_location(plugin_name, handler_path)
            mod = importlib.util.module_from_spec(spec)
            mod.bot = bot  # Optional: provide shared bot instance
            spec.loader.exec_module(mod)

            if hasattr(mod, "register_handlers"):
                mod.register_handlers(bot)

            print(f"[PLUGIN LOADED] {plugin_name}")

        except Exception as e:
            print(f"[ERROR] Failed to load plugin '{plugin_name}': {e}")
