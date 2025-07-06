from core.role_manager import is_owner, is_dev, access_mode

def has_access(user_id):
    mode = access_mode()
    if mode == "dev":
        return is_dev(user_id)
    return True