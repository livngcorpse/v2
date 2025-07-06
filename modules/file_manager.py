import re
import os
import shutil
from difflib import unified_diff

def clean_code_blocks(code: str) -> str:
    """Clean markdown code blocks from AI responses"""
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()

def backup_file(file_path: str) -> bool:
    """Create backup of file"""
    try:
        if os.path.exists(file_path):
            shutil.copy(file_path, file_path + ".bak")
            return True
        return False
    except Exception as e:
        print(f"Error backing up file: {e}")
        return False

def restore_file(file_path: str) -> bool:
    """Restore file from backup"""
    try:
        backup_path = file_path + ".bak"
        if os.path.exists(backup_path):
            shutil.copy(backup_path, file_path)
            return True
        return False
    except Exception as e:
        print(f"Error restoring file: {e}")
        return False

def diff_file(file_path: str) -> str:
    """Compare file with its backup"""
    try:
        backup_path = file_path + ".bak"
        if not os.path.exists(backup_path):
            return "No backup found."
        
        if not os.path.exists(file_path):
            return "Original file not found."
            
        with open(file_path, 'r') as f1, open(backup_path, 'r') as f2:
            diff = list(unified_diff(
                f2.readlines(), 
                f1.readlines(), 
                fromfile="original", 
                tofile="current"
            ))
        
        return "".join(diff) or "No differences."
    except Exception as e:
        return f"Error comparing files: {e}"

def read_file(file_path: str) -> str:
    """Safely read file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(file_path: str, content: str) -> bool:
    """Safely write file content"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False
