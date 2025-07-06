import traceback

def capture_exception(e):
    return traceback.format_exc()


def safe_run(fn):
    try:
        return fn()
    except Exception as e:
        return str(e)