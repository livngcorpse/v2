import json
import os

MEMORY_FILE = "logs/memory.json"

if not os.path.exists("logs"):
    os.makedirs("logs")

if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)

def log_task(task):
    with open(MEMORY_FILE, "r+") as f:
        data = json.load(f)
        data.append(task)
        f.seek(0)
        json.dump(data, f, indent=2)

def load_tasks():
    with open(MEMORY_FILE, 'r') as f:
        return json.load(f)

def get_task_by_id(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None

def restore_file(file_path): 
    backup_path = f"{file_path}.bak"
    if os.path.exists(backup_path):
        with open(backup_path, "rb") as src, open(file_path, "wb") as dst:
            dst.write(src.read())
        return True
    return False

def revert_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return False, "Task not found."
    for file in task["files"]:
        restored = restore_file(file)
        if not restored:
            return False, f"Backup not found for {file}"
    return True, "Task reverted."