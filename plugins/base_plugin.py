"""
Base Plugin System - For custom parsing logic when configuration-based scraping isn't sufficient
"""

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import logging


class BasePlugin(ABC):
    """
    Base class for custom parsing plugins.
    Plugins are used when the standard configuration-based scraping isn't sufficient.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"Plugin-{self.__class__.__name__}")
    
    @abstractmethod
    def parse(self, soup: BeautifulSoup, scraper_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse content and return list of updates.
        
        Args:
            soup: BeautifulSoup object of the webpage
            scraper_config: The scraper configuration
            
        Returns:
            List of update dictionaries
        """
        pass
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about this plugin"""
        return {
            'name': self.__class__.__name__,
            'version': getattr(self, 'version', '1.0.0'),
            'description': getattr(self, 'description', 'Custom parsing plugin'),
            'author': getattr(self, 'author', 'Unknown')
        }


class PluginManager:
    """
    Manages custom parsing plugins
    """
    
    def __init__(self):
        self.plugins = {}
        self.logger = logging.getLogger(__name__)
    
    def register_plugin(self, name: str, plugin_class: type):
        """Register a plugin class"""
        self.plugins[name] = plugin_class
        self.logger.info(f"Registered plugin: {name}")
    
    def create_plugin(self, name: str, config: Dict[str, Any]) -> BasePlugin:
        """Create a plugin instance"""
        if name not in self.plugins:
            raise ValueError(f"Plugin {name} not found")
        
        plugin_class = self.plugins[name]
        return plugin_class(config)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins"""
        return list(self.plugins.keys())
    
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get information about a plugin"""
        if name not in self.plugins:
            return {}
        
        plugin_class = self.plugins[name]
        return {
            'name': name,
            'class': plugin_class.__name__,
            'module': plugin_class.__module__
        }
