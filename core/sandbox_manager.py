import os
import shutil
import json
import time
from typing import Dict, List, Any, Optional
from core.task_manager import backup_file
from memory.memory_manager import log_task, get_task_by_id
from modules.regression_checker import regression_checker
from error_handler import capture_exception

class SandboxManager:
    def __init__(self):
        self.sandbox_dir = "sandbox"
        self.plugins_dir = "plugins"
        os.makedirs(self.sandbox_dir, exist_ok=True)
        os.makedirs(self.plugins_dir, exist_ok=True)
    
    def create_sandbox_files(self, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Create files in sandbox based on AI-generated code
        
        Args:
            task_data: Dictionary containing files and their content
            user_id: User ID who initiated the task
            
        Returns:
            Dictionary with task information and file paths
        """
        
        task_id = int(time.time())
        task_info = {
            "id": task_id,
            "user_id": user_id,
            "timestamp": time.time(),
            "status": "sandboxed",
            "files": [],
            "errors": []
        }
        
        try:
            files_data = task_data.get("files", {})
            
            for file_path, content in files_data.items():
                full_path = os.path.join(os.getcwd(), file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Backup existing file if it exists
                if os.path.exists(full_path):
                    backup_file(full_path)
                
                # Write new content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                task_info["files"].append(full_path)
                
                # Run regression checker
                check_result = regression_checker.comprehensive_check(full_path)
                if not check_result.passed:
                    task_info["errors"].append({
                        "file": file_path,
                        "message": f"Quality check failed (Score: {check_result.score}/100)",
                        "details": check_result.errors + check_result.warnings
                    })
            
            # Log the task
            log_task(task_info)
            
            return task_info
            
        except Exception as e:
            error_msg = capture_exception(e)
            task_info["errors"].append({
                "type": "creation_error",
                "message": error_msg
            })
            return task_info

    
    def test_sandbox_feature(self, task_id: int) -> Dict[str, Any]:
        """
        Test sandbox feature by attempting to import/validate code
        
        Args:
            task_id: Task ID to test
            
        Returns:
            Dictionary with test results
        """
        
        task = get_task_by_id(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        test_results = {
            "task_id": task_id,
            "success": True,
            "file_tests": [],
            "errors": []
        }
        
        try:
            for file_path in task.get("files", []):
                if file_path.endswith(".py"):
                    # Test Python syntax
                    with open(file_path, 'r') as f:
                        code = f.read()
                    
                    try:
                        compile(code, file_path, 'exec')
                        test_results["file_tests"].append({
                            "file": file_path,
                            "syntax_valid": True
                        })
                    except SyntaxError as e:
                        test_results["success"] = False
                        test_results["errors"].append({
                            "file": file_path,
                            "error": f"Syntax error: {e}"
                        })
                        test_results["file_tests"].append({
                            "file": file_path,
                            "syntax_valid": False,
                            "error": str(e)
                        })
            
            return test_results
            
        except Exception as e:
            return {
                "success": False,
                "error": capture_exception(e)
            }
    
    def integrate_to_plugins(self, task_id: int, plugin_name: str = None) -> Dict[str, Any]:
        """
        Move sandbox files to plugins directory
        
        Args:
            task_id: Task ID to integrate
            plugin_name: Optional custom plugin name
            
        Returns:
            Dictionary with integration results
        """
        
        task = get_task_by_id(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        if task.get("status") != "sandboxed":
            return {"success": False, "error": "Task is not in sandbox state"}
        
        try:
            # Determine plugin name
            if not plugin_name:
                plugin_name = self._extract_plugin_name(task)
            
            plugin_dir = os.path.join(self.plugins_dir, plugin_name)
            os.makedirs(plugin_dir, exist_ok=True)
            
            moved_files = []
            
            for file_path in task.get("files", []):
                if file_path.startswith("sandbox/"):
                    # Get relative path within sandbox
                    rel_path = os.path.relpath(file_path, "sandbox")
                    
                    # Skip the plugin directory part if it exists
                    path_parts = rel_path.split(os.sep)
                    if len(path_parts) > 1:
                        filename = path_parts[-1]
                    else:
                        filename = rel_path
                    
                    dest_path = os.path.join(plugin_dir, filename)
                    
                    # Move file
                    shutil.move(file_path, dest_path)
                    moved_files.append(dest_path)
            
            # Update task status
            task["status"] = "integrated"
            task["plugin_name"] = plugin_name
            task["plugin_dir"] = plugin_dir
            task["integrated_files"] = moved_files
            
            # Update task in memory
            self._update_task_status(task_id, task)
            
            # Clean up empty sandbox directories
            self._cleanup_empty_dirs(os.path.join(self.sandbox_dir, plugin_name))
            
            return {
                "success": True,
                "plugin_name": plugin_name,
                "plugin_dir": plugin_dir,
                "moved_files": moved_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": capture_exception(e)
            }
    
    def list_sandbox_tasks(self, user_id: int = None) -> List[Dict[str, Any]]:
        """
        List all sandbox tasks, optionally filtered by user
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of sandbox tasks
        """
        
        from memory.memory_manager import load_tasks
        
        tasks = load_tasks()
        sandbox_tasks = [
            task for task in tasks 
            if task.get("status") == "sandboxed" and 
            (user_id is None or task.get("user_id") == user_id)
        ]
        
        return sandbox_tasks
    
    def cleanup_sandbox(self, task_id: int) -> bool:
        """
        Clean up sandbox files for a specific task
        
        Args:
            task_id: Task ID to clean up
            
        Returns:
            True if successful, False otherwise
        """
        
        task = get_task_by_id(task_id)
        if not task:
            return False
        
        try:
            for file_path in task.get("files", []):
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Update task status
            task["status"] = "cleaned"
            self._update_task_status(task_id, task)
            
            return True
            
        except Exception as e:
            print(f"Error cleaning sandbox: {e}")
            return False
    
    def _extract_plugin_name(self, task: Dict[str, Any]) -> str:
        """Extract plugin name from task files"""
        
        files = task.get("files", [])
        if not files:
            return f"plugin_{task['id']}"
        
        # Try to extract from sandbox path
        for file_path in files:
            if file_path.startswith("sandbox/"):
                parts = file_path.split("/")
                if len(parts) > 1:
                    return parts[1]
        
        return f"plugin_{task['id']}"
    
    def _update_task_status(self, task_id: int, updated_task: Dict[str, Any]):
        """Update task status in memory"""
        
        from memory.memory_manager import MEMORY_FILE
        
        try:
            with open(MEMORY_FILE, 'r') as f:
                tasks = json.load(f)
            
            for i, task in enumerate(tasks):
                if task.get("id") == task_id:
                    tasks[i] = updated_task
                    break
            
            with open(MEMORY_FILE, 'w') as f:
                json.dump(tasks, f, indent=2)
                
        except Exception as e:
            print(f"Error updating task status: {e}")
    
    def _cleanup_empty_dirs(self, dir_path: str):
        """Remove empty directories recursively"""
        
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                # Remove empty subdirectories first
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if os.path.isdir(item_path):
                        self._cleanup_empty_dirs(item_path)
                
                # Remove directory if empty
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    
        except Exception as e:
            print(f"Error cleaning up directories: {e}")

# Global instance
sandbox_manager = SandboxManager()
