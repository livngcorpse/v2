import os
import json
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from telegram.ext import Application

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.plugins = {}
        self.plugins_config_path = Path('config/plugins.json')
        self.features_dir = Path('features')
        self.load_plugins_config()
        
    def load_plugins_config(self):
        """Load plugins configuration"""
        try:
            if self.plugins_config_path.exists():
                with open(self.plugins_config_path, 'r') as f:
                    self.plugins_config = json.load(f)
            else:
                self.plugins_config = {
                    'enabled_plugins': [],
                    'disabled_plugins': [],
                    'plugin_settings': {}
                }
                self.save_plugins_config()
        except Exception as e:
            logger.error(f"Error loading plugins config: {e}")
            self.plugins_config = {
                'enabled_plugins': [],
                'disabled_plugins': [],
                'plugin_settings': {}
            }
    
    def save_plugins_config(self):
        """Save plugins configuration"""
        try:
            self.plugins_config_path.parent.mkdir(exist_ok=True)
            with open(self.plugins_config_path, 'w') as f:
                json.dump(self.plugins_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving plugins config: {e}")
    
    def discover_plugins(self):
        """Discover available plugins in features directory"""
        discovered = []
        if not self.features_dir.exists():
            self.features_dir.mkdir(exist_ok=True)
            return discovered
            
        for plugin_dir in self.features_dir.iterdir():
            if plugin_dir.is_dir():
                handler_file = plugin_dir / 'handler.py'
                if handler_file.exists():
                    discovered.append(plugin_dir.name)
                    
        return discovered
    
    def load_plugin(self, plugin_name: str, application: Application) -> bool:
        """Load a single plugin"""
        try:
            plugin_path = self.features_dir / plugin_name / 'handler.py'
            if not plugin_path.exists():
                logger.error(f"Plugin handler not found: {plugin_path}")
                return False
            
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", 
                str(plugin_path)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if module has required functions
            if not hasattr(module, 'register_handlers'):
                logger.error(f"Plugin {plugin_name} missing register_handlers function")
                return False
            
            # Register handlers
            module.register_handlers(application, self.bot)
            
            # Store plugin info
            self.plugins[plugin_name] = {
                'module': module,
                'enabled': True,
                'loaded_at': str(Path.cwd())
            }
            
            # Update config
            if plugin_name not in self.plugins_config['enabled_plugins']:
                self.plugins_config['enabled_plugins'].append(plugin_name)
            if plugin_name in self.plugins_config['disabled_plugins']:
                self.plugins_config['disabled_plugins'].remove(plugin_name)
            
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin (mark as disabled)"""
        try:
            if plugin_name in self.plugins:
                self.plugins[plugin_name]['enabled'] = False
                
                # Update config
                if plugin_name in self.plugins_config['enabled_plugins']:
                    self.plugins_config['enabled_plugins'].remove(plugin_name)
                if plugin_name not in self.plugins_config['disabled_plugins']:
                    self.plugins_config['disabled_plugins'].append(plugin_name)
                
                logger.info(f"Disabled plugin: {plugin_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
        
    def load_plugins(self, application: Application) -> int:
        """Load all enabled plugins from config/settings.json"""
        count = 0
        enabled_list = self.plugins_config.get('enabled_plugins', [])
        plugins_dir = Path("plugins")

        for plugin_name in enabled_list:
            plugin_path = plugins_dir / f"{plugin_name}.py"
            if plugin_path.exists():
                if self.load_plugin(plugin_name, application):
                    count += 1
            else:
                logger.warning(f"Plugin '{plugin_name}' not found in plugins/")
        
        return count

    
    def enable_plugin(self, plugin_name: str, application: Application) -> bool:
        """Enable a plugin"""
        return self.load_plugin(plugin_name, application)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        return self.unload_plugin(plugin_name)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        return None
    
    def list_plugins(self) -> Dict[str, list]:
        """List all available plugins"""
        discovered = self.discover_plugins()
        enabled = [name for name in discovered if name in self.plugins and self.plugins[name]['enabled']]
        disabled = [name for name in discovered if name not in enabled]
        
        return {
            'enabled': enabled,
            'disabled': disabled,
            'total': len(discovered)
        }
    
    def load_all_plugins(self, application: Application):
        """Load all enabled plugins"""
        discovered = self.discover_plugins()
        
        for plugin_name in discovered:
            # Skip if explicitly disabled
            if plugin_name in self.plugins_config['disabled_plugins']:
                continue
                
            success = self.load_plugin(plugin_name, application)
            if success:
                logger.info(f"Auto-loaded plugin: {plugin_name}")
        
        # Save updated config
        self.save_plugins_config()
    
    def get_plugin_settings(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin-specific settings"""
        return self.plugins_config['plugin_settings'].get(plugin_name, {})
    
    def set_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]):
        """Set plugin-specific settings"""
        self.plugins_config['plugin_settings'][plugin_name] = settings
        self.save_plugins_config()