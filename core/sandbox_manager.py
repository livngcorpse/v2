import os

def move_to_plugin(task):
    plugin_dir = f"plugins/{task['name']}"
    os.makedirs(plugin_dir, exist_ok=True)
    for file in task["files"]:
        os.rename(file, os.path.join(plugin_dir, os.path.basename(file)))