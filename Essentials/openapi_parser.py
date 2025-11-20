"""
OpenAPI Specification Parser.
Parses OpenAPI 3.0 (Swagger 3.0), OpenAPI 3.1, and Swagger 2.0 specifications.
Extracts endpoint information and supports both JSON and YAML formats.
"""

import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class OpenAPIParser:
    """Parser for OpenAPI specifications."""
    
    def __init__(self):
        self.spec: Optional[Dict[str, Any]] = None
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an OpenAPI specification file.
        
        Args:
            file_path: Path to the OpenAPI spec file (JSON or YAML)
            
        Returns:
            Parsed OpenAPI specification as a dictionary
            
        Raises:
            ValueError: If the file format is not supported or parsing fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Determine file type and parse
        if path.suffix.lower() in ['.yaml', '.yml']:
            try:
                self.spec = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse YAML: {str(e)}")
        elif path.suffix.lower() == '.json':
            try:
                self.spec = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON: {str(e)}")
        else:
            # Try to parse as JSON first, then YAML
            try:
                self.spec = json.loads(content)
            except json.JSONDecodeError:
                try:
                    self.spec = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise ValueError(f"Failed to parse file: {str(e)}")
                    
        if not self.spec:
            raise ValueError("Empty or invalid OpenAPI specification")
            
        # Validate it's an OpenAPI spec
        if 'openapi' not in self.spec and 'swagger' not in self.spec:
            raise ValueError("File does not appear to be an OpenAPI specification")
            
        # Extract endpoints
        self._extract_endpoints()
        
        return self.spec
        
    def _extract_endpoints(self):
        """Extract endpoints from the OpenAPI/Swagger specification."""
        self.endpoints = {}
        
        if not self.spec or 'paths' not in self.spec:
            return
            
        paths = self.spec['paths']
        is_swagger_2 = 'swagger' in self.spec
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            methods = {}
            
            # HTTP methods (same for OpenAPI 3.0 and Swagger 2.0)
            http_methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
            
            for method in http_methods:
                if method in path_item:
                    operation = path_item[method]
                    
                    # Extract parameters
                    parameters = operation.get('parameters', [])
                    
                    # Handle request body differently for Swagger 2.0 vs OpenAPI 3.0
                    request_body = None
                    if is_swagger_2:
                        # Swagger 2.0: request body is in parameters with in: 'body'
                        body_params = [p for p in parameters if p.get('in') == 'body']
                        if body_params:
                            request_body = body_params[0].get('schema', {})
                            # Convert to OpenAPI 3.0 format for consistency
                            request_body = {
                                'content': {
                                    'application/json': {
                                        'schema': request_body
                                    }
                                }
                            }
                        # Remove body parameters from regular parameters list
                        parameters = [p for p in parameters if p.get('in') != 'body']
                    else:
                        # OpenAPI 3.0: request body is separate
                        request_body = operation.get('requestBody')
                        # Resolve $ref in request body schema if present
                        if request_body and isinstance(request_body, dict):
                            # Make a deep copy to avoid modifying the original spec
                            import copy
                            request_body = copy.deepcopy(request_body)
                            content = request_body.get('content', {})
                            for content_type, content_schema in content.items():
                                if 'application/json' in content_type or 'json' in content_type:
                                    schema = content_schema.get('schema')
                                    if schema and isinstance(schema, dict):
                                        if '$ref' in schema:
                                            # Resolve the $ref
                                            resolved_schema = self._resolve_schema(schema)
                                            if resolved_schema and resolved_schema != schema:
                                                content_schema['schema'] = resolved_schema
                                        else:
                                            # Even if no $ref, recursively resolve any nested $ref
                                            content_schema['schema'] = self._resolve_schema(schema)
                    
                    methods[method.upper()] = {
                        'operation_id': operation.get('operationId', f'{method}_{path}'),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'parameters': parameters,
                        'request_body': request_body,
                        'responses': operation.get('responses', {}),
                        'tags': operation.get('tags', [])
                    }
                    
            if methods:
                self.endpoints[path] = methods
                
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """
        Get extracted endpoints.
        
        Returns:
            Dictionary mapping paths to their HTTP methods and details
        """
        return self.endpoints
        
    def get_parameters_for_endpoint(self, path: str, method: str) -> List[Dict[str, Any]]:
        """
        Get parameters for a specific endpoint.
        
        Args:
            path: API path
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            List of parameter definitions
        """
        if path not in self.endpoints:
            return []
            
        method_lower = method.lower()
        if method_lower not in self.endpoints[path]:
            return []
            
        return self.endpoints[path][method_lower].get('parameters', [])
        
    def _resolve_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a $ref reference to the actual schema.
        
        Args:
            ref: Reference string (e.g., '#/components/schemas/UserInput')
            
        Returns:
            Resolved schema or None if not found
        """
        if not ref or not ref.startswith('#'):
            return None
            
        # Remove the leading '#'
        ref_path = ref[1:].split('/')
        
        # Navigate through the spec
        current = self.spec
        for part in ref_path:
            if part and isinstance(current, dict):
                current = current.get(part)
            else:
                return None
                
        return current if isinstance(current, dict) else None
    
    def _resolve_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve $ref references in a schema.
        
        Args:
            schema: Schema dictionary that may contain $ref
            
        Returns:
            Schema with all $ref references resolved
        """
        if not isinstance(schema, dict):
            return schema
            
        # If this schema has a $ref, resolve it
        if '$ref' in schema:
            resolved = self._resolve_ref(schema['$ref'])
            if resolved:
                # Merge any additional properties from the original schema
                result = self._resolve_schema(resolved.copy())
                # Merge in any additional properties (like description, example, etc.)
                for key, value in schema.items():
                    if key != '$ref' and key not in result:
                        result[key] = value
                return result
            return schema
            
        # Recursively resolve nested schemas
        result = {}
        for key, value in schema.items():
            if key == '$ref':
                resolved = self._resolve_ref(value)
                if resolved:
                    result.update(self._resolve_schema(resolved))
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._resolve_schema(value)
            elif isinstance(value, list):
                result[key] = [self._resolve_schema(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
                
        return result
    
    def get_request_body_schema(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Get request body schema for an endpoint.
        
        Args:
            path: API path
            method: HTTP method
            
        Returns:
            Request body schema with $ref references resolved, or None
        """
        if path not in self.endpoints:
            return None
            
        method_lower = method.lower()
        if method_lower not in self.endpoints[path]:
            return None
            
        request_body = self.endpoints[path][method_lower].get('request_body')
        if not request_body:
            return None
            
        # Extract schema from request body
        content = request_body.get('content', {})
        for content_type, content_schema in content.items():
            if 'application/json' in content_type or 'json' in content_type:
                schema = content_schema.get('schema', {})
                if schema:
                    # Resolve $ref references
                    return self._resolve_schema(schema)
                return schema
                
        return None
        
    def get_base_url(self) -> Optional[str]:
        """
        Get base URL from OpenAPI spec.
        
        Returns:
            Base URL or None if not specified
        """
        if not self.spec:
            return None
            
        # OpenAPI 3.0
        if 'servers' in self.spec and self.spec['servers']:
            return self.spec['servers'][0].get('url', '')
            
        # Swagger 2.0
        if 'host' in self.spec:
            scheme = self.spec.get('schemes', ['http'])[0]
            host = self.spec['host']
            base_path = self.spec.get('basePath', '')
            return f"{scheme}://{host}{base_path}"
            
        return None

