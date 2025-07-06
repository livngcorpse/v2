import json
import os

def get_chat_memory(chat_id):
    path = f"logs/conversations/{chat_id}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save_chat_memory(chat_id, memory):
    path = f"logs/conversations/{chat_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)