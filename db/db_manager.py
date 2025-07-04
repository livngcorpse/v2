import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_dir = Path('db')
        self.db_dir.mkdir(exist_ok=True)
        
    def get_db_path(self, db_name: str) -> Path:
        """Get database file path"""
        if not db_name.endswith('.json'):
            db_name += '.json'
        return self.db_dir / db_name
    
    def create_db(self, db_name: str, initial_data: Dict[str, Any] = None) -> bool:
        """Create a new database"""
        try:
            db_path = self.get_db_path(db_name)
            
            if db_path.exists():
                logger.warning(f"Database {db_name} already exists")
                return False
            
            data = initial_data or {}
            
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created database: {db_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database {db_name}: {e}")
            return False
    
    def read_db(self, db_name: str) -> Optional[Dict[str, Any]]:
        """Read entire database"""
        try:
            db_path = self.get_db_path(db_name)
            
            if not db_path.exists():
                logger.warning(f"Database {db_name} does not exist")
                return None
            
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading database {db_name}: {e}")
            return None
    
    def write_db(self, db_name: str, data: Dict[str, Any]) -> bool:
        """Write entire database"""
        try:
            db_path = self.get_db_path(db_name)
            
            # Create backup
            if db_path.exists():
                backup_path = db_path.with_suffix('.json.bak')
                db_path.replace(backup_path)
            
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing database {db_name}: {e}")
            return False
    
    def get_value(self, db_name: str, key: str, default: Any = None) -> Any:
        """Get a value from database"""
        try:
            data = self.read_db(db_name)
            if data is None:
                return default
            
            # Support nested keys with dot notation
            keys = key.split('.')
            value = data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting value {key} from {db_name}: {e}")
            return default
    
    def set_value(self, db_name: str, key: str, value: Any) -> bool:
        """Set a value in database"""
        try:
            data = self.read_db(db_name) or {}
            
            # Support nested keys with dot notation
            keys = key.split('.')
            current = data
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Set the final key
            current[keys[-1]] = value
            
            return self.write_db(db_name, data)
            
        except Exception as e:
            logger.error(f"Error setting value {key} in {db_name}: {e}")
            return False
    
    def delete_key(self, db_name: str, key: str) -> bool:
        """Delete a key from database"""
        try:
            data = self.read_db(db_name)
            if data is None:
                return False
            
            keys = key.split('.')
            current = data
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in current:
                    return False
                current = current[k]
            
            # Delete the final key
            if keys[-1] in current:
                del current[keys[-1]]
                return self.write_db(db_name, data)
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting key {key} from {db_name}: {e}")
            return False
    
    def append_to_list(self, db_name: str, key: str, value: Any) -> bool:
        """Append value to a list in database"""
        try:
            current_list = self.get_value(db_name, key, [])
            
            if not isinstance(current_list, list):
                current_list = []
            
            current_list.append(value)
            return self.set_value(db_name, key, current_list)
            
        except Exception as e:
            logger.error(f"Error appending to list {key} in {db_name}: {e}")
            return False
    
    def increment_counter(self, db_name: str, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in database"""
        try:
            current_value = self.get_value(db_name, key, 0)
            
            if not isinstance(current_value, (int, float)):
                current_value = 0
            
            new_value = current_value + amount
            
            if self.set_value(db_name, key, new_value):
                return new_value
            
            return None
            
        except Exception as e:
            logger.error(f"Error incrementing counter {key} in {db_name}: {e}")
            return None
    
    def add_timestamped_entry(self, db_name: str, key: str, data: Dict[str, Any]) -> bool:
        """Add a timestamped entry to database"""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            return self.append_to_list(db_name, key, entry)
            
        except Exception as e:
            logger.error(f"Error adding timestamped entry to {key} in {db_name}: {e}")
            return False
    
    def get_recent_entries(self, db_name: str, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent timestamped entries"""
        try:
            entries = self.get_value(db_name, key, [])
            
            if not isinstance(entries, list):
                return []
            
            # Sort by timestamp (newest first) and limit
            sorted_entries = sorted(
                entries,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )
            
            return sorted_entries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent entries from {key} in {db_name}: {e}")
            return []
    
    def list_databases(self) -> List[str]:
        """List all available databases"""
        try:
            db_files = []
            for db_file in self.db_dir.glob('*.json'):
                if not db_file.name.endswith('.bak'):
                    db_files.append(db_file.stem)
            
            return sorted(db_files)
            
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return []
    
    def backup_database(self, db_name: str) -> bool:
        """Create a backup of database"""
        try:
            db_path = self.get_db_path(db_name)
            
            if not db_path.exists():
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = db_path.with_suffix(f'.{timestamp}.bak')
            
            db_path.replace(backup_path)
            logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up database {db_name}: {e}")
            return False
    
    def restore_database(self, db_name: str, backup_name: str = None) -> bool:
        """Restore database from backup"""
        try:
            db_path = self.get_db_path(db_name)
            
            if backup_name:
                backup_path = self.db_dir / f"{db_name}.{backup_name}.bak"
            else:
                # Find latest backup
                backups = list(self.db_dir.glob(f"{db_name}.*.bak"))
                if not backups:
                    logger.error(f"No backups found for {db_name}")
                    return False
                
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            backup_path.replace(db_path)
            logger.info(f"Restored database {db_name} from backup")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring database {db_name}: {e}")
            return False