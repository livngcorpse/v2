import json

with open("config/settings.json") as f:
    settings = json.load(f)

BOT = None

def set_bot_instance(bot):
    global BOT
    BOT = bot

def is_owner(user_id):
    return user_id == settings["owner_id"]

def is_dev(user_id):
    return user_id in settings["devs"] or is_owner(user_id)

def access_mode():
    return settings["access"]
