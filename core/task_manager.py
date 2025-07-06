import json
import shutil
import os
from memory.memory_manager import log_task

TASK_DIR = "logs/tasks"
os.makedirs(TASK_DIR, exist_ok=True)


def backup_file(path):
    if os.path.exists(path):
        shutil.copy(path, path + ".bak")


def restore_file(path):
    bak = path + ".bak"
    if os.path.exists(bak):
        shutil.copy(bak, path)
        return True
    return False


def diff_file(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        return "No backup found."
    with open(path, 'r') as f1, open(bak, 'r') as f2:
        from difflib import unified_diff
        diff = list(unified_diff(f2.readlines(), f1.readlines(), fromfile="original", tofile="current"))
    return "".join(diff) or "No differences."