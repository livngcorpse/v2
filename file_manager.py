import os
import shutil
import difflib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_suffix = '.bak'

    def write_file(self, file_path, content):
        """Safely write file with backup"""
        try:
            path = Path(file_path)
            
            # Create backup if file exists
            if path.exists():
                backup_path = path.with_suffix(path.suffix + self.backup_suffix)
                shutil.copy2(path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Create directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write new content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"File written: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False

    def read_file(self, file_path):
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def show_diff(self, file_path):
        """Show difference between current file and backup"""
        try:
            path = Path(file_path)
            backup_path = path.with_suffix(path.suffix + self.backup_suffix)
            
            if not path.exists():
                return "File does not exist"
            
            if not backup_path.exists():
                return "No backup found"
            
            # Read both files
            current_content = self.read_file(path)
            backup_content = self.read_file(backup_path)
            
            if current_content is None or backup_content is None:
                return "Error reading files"
            
            # Generate diff
            diff = difflib.unified_diff(
                backup_content.splitlines(keepends=True),
                current_content.splitlines(keepends=True),
                fromfile=f"{file_path}.bak",
                tofile=file_path
            )
            
            return ''.join(diff) or "No differences found"
            
        except Exception as e:
            logger.error(f"Error showing diff for {file_path}: {e}")
            return f"Error: {str(e)}"

    def undo_changes(self, file_path):
        """Restore file from backup"""
        try:
            path = Path(file_path)
            backup_path = path.with_suffix(path.suffix + self.backup_suffix)
            
            if not backup_path.exists():
                logger.error(f"No backup found for {file_path}")
                return False
            
            # Restore from backup
            shutil.copy2(backup_path, path)
            logger.info(f"Restored {file_path} from backup")
            return True
            
        except Exception as e:
            logger.error(f"Error undoing changes for {file_path}: {e}")
            return False

    def delete_file(self, file_path):
        """Delete file safely"""
        try:
            path = Path(file_path)
            if path.exists():
                # Create backup before deletion
                backup_path = path.with_suffix(path.suffix + self.backup_suffix)
                shutil.copy2(path, backup_path)
                
                # Delete file
                path.unlink()
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False