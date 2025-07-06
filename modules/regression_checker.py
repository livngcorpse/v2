import subprocess

def lint_code(file_path: str) -> str:
    result = subprocess.run(["pyflakes", file_path], capture_output=True, text=True)
    return result.stdout + result.stderr