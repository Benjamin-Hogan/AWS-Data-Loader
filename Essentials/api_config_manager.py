"""
API Configuration Manager.
Manages multiple OpenAPI specifications with different ports and endpoints.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from openapi_parser import OpenAPIParser
from api_client import APIClient


class APIConfig:
    """Represents a single API configuration."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        openapi_spec_path: Optional[str] = None,
        auth_token: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize an API configuration.
        
        Args:
            name: Unique name for this API configuration
            base_url: Base URL for the API (e.g., 'http://localhost:8000')
            openapi_spec_path: Path to OpenAPI specification file
            auth_token: Optional authentication token
            port: Optional port number (will override base_url port if provided)
        """
        self.name = name
        self.base_url = base_url.rstrip('/')
        if port:
            # Extract scheme and hostname, replace port
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(self.base_url)
            netloc = f"{parsed.hostname}:{port}" if parsed.hostname else f":{port}"
            self.base_url = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        
        self.openapi_spec_path = openapi_spec_path
        self.auth_token = auth_token
        self.openapi_spec: Optional[Dict[str, Any]] = None
        self.endpoints: Dict[str, Any] = {}
        self.api_client: Optional[APIClient] = None
        self.parser: Optional[OpenAPIParser] = None
        
        # Initialize API client
        self._init_client()
        
        # Load OpenAPI spec if path provided
        if self.openapi_spec_path:
            self.load_openapi_spec()
    
    def _init_client(self):
        """Initialize the API client."""
        self.api_client = APIClient(self.base_url)
        if self.auth_token:
            self.api_client.set_auth_token(self.auth_token)
    
    def load_openapi_spec(self, file_path: Optional[str] = None):
        """
        Load OpenAPI specification.
        
        Args:
            file_path: Path to OpenAPI spec file (uses self.openapi_spec_path if not provided)
        """
        spec_path = file_path or self.openapi_spec_path
        if not spec_path:
            raise ValueError("No OpenAPI spec path provided")
        
        parser = OpenAPIParser()
        self.openapi_spec = parser.parse(spec_path)
        self.endpoints = parser.get_endpoints()
        self.parser = parser
        
        # Update base URL from spec if not already set
        spec_base_url = parser.get_base_url()
        if spec_base_url and not self.base_url:
            self.base_url = spec_base_url.rstrip('/')
            self._init_client()
    
    def set_auth_token(self, token: str):
        """Set authentication token."""
        self.auth_token = token
        if self.api_client:
            self.api_client.set_auth_token(token)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'name': self.name,
            'base_url': self.base_url,
            'openapi_spec_path': self.openapi_spec_path,
            'auth_token': self.auth_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIConfig':
        """Create configuration from dictionary."""
        return cls(
            name=data['name'],
            base_url=data['base_url'],
            openapi_spec_path=data.get('openapi_spec_path'),
            auth_token=data.get('auth_token')
        )


class APIConfigManager:
    """Manages multiple API configurations."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to JSON file for persisting configurations
        """
        self.configs: Dict[str, APIConfig] = {}
        self.active_config: Optional[str] = None
        self.config_file = config_file or 'api_configs.json'
        
        # Load saved configurations
        self.load_configs()
    
    def add_config(
        self,
        name: str,
        base_url: str,
        openapi_spec_path: Optional[str] = None,
        auth_token: Optional[str] = None,
        port: Optional[int] = None
    ) -> APIConfig:
        """
        Add a new API configuration.
        
        Args:
            name: Unique name for this configuration
            base_url: Base URL for the API
            openapi_spec_path: Path to OpenAPI specification file
            auth_token: Optional authentication token
            port: Optional port number
            
        Returns:
            The created APIConfig instance
            
        Raises:
            ValueError: If name already exists
        """
        if name in self.configs:
            raise ValueError(f"Configuration '{name}' already exists")
        
        config = APIConfig(
            name=name,
            base_url=base_url,
            openapi_spec_path=openapi_spec_path,
            auth_token=auth_token,
            port=port
        )
        
        self.configs[name] = config
        
        # Set as active if it's the first one
        if not self.active_config:
            self.active_config = name
        
        self.save_configs()
        return config
    
    def remove_config(self, name: str) -> bool:
        """
        Remove an API configuration.
        
        Args:
            name: Name of configuration to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self.configs:
            del self.configs[name]
            # If it was active, set another as active
            if self.active_config == name:
                self.active_config = next(iter(self.configs.keys())) if self.configs else None
            self.save_configs()
            return True
        return False
    
    def get_config(self, name: Optional[str] = None) -> Optional[APIConfig]:
        """
        Get an API configuration.
        
        Args:
            name: Name of configuration (uses active if not provided)
            
        Returns:
            APIConfig instance or None if not found
        """
        config_name = name or self.active_config
        return self.configs.get(config_name) if config_name else None
    
    def set_active_config(self, name: str) -> bool:
        """
        Set the active configuration.
        
        Args:
            name: Name of configuration to activate
            
        Returns:
            True if set, False if not found
        """
        if name in self.configs:
            self.active_config = name
            self.save_configs()
            return True
        return False
    
    def get_all_configs(self) -> List[APIConfig]:
        """Get all configurations."""
        return list(self.configs.values())
    
    def get_config_names(self) -> List[str]:
        """Get all configuration names."""
        return list(self.configs.keys())
    
    def refresh_config(self, name: str) -> bool:
        """
        Refresh OpenAPI specification for a configuration.
        
        Args:
            name: Name of configuration to refresh
            
        Returns:
            True if refreshed successfully, False if not found or no spec path
        """
        config = self.get_config(name)
        if not config:
            return False
        
        if not config.openapi_spec_path:
            return False
        
        try:
            # Reload the OpenAPI spec from the stored path
            config.load_openapi_spec()
            # Save the config (though spec path hasn't changed, this ensures consistency)
            self.save_configs()
            return True
        except Exception as e:
            raise ValueError(f"Failed to refresh OpenAPI spec: {str(e)}")
    
    def load_configs(self):
        """Load configurations from file."""
        config_path = Path(self.config_file)
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load configurations
            for config_data in data.get('configs', []):
                try:
                    config = APIConfig.from_dict(config_data)
                    # Reload OpenAPI spec if path exists
                    if config.openapi_spec_path and Path(config.openapi_spec_path).exists():
                        config.load_openapi_spec()
                    self.configs[config.name] = config
                except Exception as e:
                    print(f"Failed to load config {config_data.get('name', 'unknown')}: {e}")
            
            # Set active config
            self.active_config = data.get('active_config')
            if self.active_config and self.active_config not in self.configs:
                self.active_config = next(iter(self.configs.keys())) if self.configs else None
                
        except Exception as e:
            print(f"Failed to load configurations: {e}")
    
    def save_configs(self):
        """Save configurations to file."""
        try:
            data = {
                'configs': [config.to_dict() for config in self.configs.values()],
                'active_config': self.active_config
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save configurations: {e}")

