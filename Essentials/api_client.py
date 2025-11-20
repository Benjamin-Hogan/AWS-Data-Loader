"""
REST API Client for making HTTP requests.
Handles authentication, request formatting, and response processing.
"""

import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json


class APIClient:
    """Client for making REST API requests."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API (e.g., 'https://api.example.com')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def set_auth_token(self, token: str, auth_type: str = 'Bearer'):
        """
        Set authentication token.
        
        Args:
            token: Authentication token
            auth_type: Type of authentication (Bearer, Token, etc.)
        """
        self.session.headers['Authorization'] = f'{auth_type} {token}'
        
    def set_headers(self, headers: Dict[str, str]):
        """
        Set custom headers.
        
        Args:
            headers: Dictionary of header key-value pairs
        """
        self.session.headers.update(headers)
        
    def make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path (e.g., '/api/users')
            params: Query parameters
            headers: Additional headers (merged with session headers)
            body: Request body as string (JSON)
            
        Returns:
            Dictionary containing response information:
            {
                'status_code': int,
                'headers': dict,
                'body': str,
                'json': dict or None,
                'url': str,
                'method': str
            }
            
        Raises:
            requests.RequestException: If the request fails
        """
        # Construct full URL
        url = f"{self.base_url}{path}"
        
        # Prepare headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
            
        # Prepare body
        json_data = None
        if body:
            try:
                json_data = json.loads(body)
            except json.JSONDecodeError:
                # If not valid JSON, send as raw string
                request_headers['Content-Type'] = 'text/plain'
                json_data = body
                
        # Make request
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=request_headers,
                json=json_data if isinstance(json_data, dict) else None,
                data=body if not isinstance(json_data, dict) else None,
                timeout=self.timeout
            )
            
            # Parse response
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'url': response.url,
                'method': method.upper(),
                'body': response.text,
                'json': None
            }
            
            # Try to parse JSON response
            try:
                result['json'] = response.json()
            except (ValueError, json.JSONDecodeError):
                pass
                
            return result
            
        except requests.exceptions.Timeout:
            raise requests.RequestException("Request timed out")
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"Failed to connect to {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")
            
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.make_request('GET', path, params=params, headers=headers)
        
    def post(self, path: str, body: Optional[str] = None, 
             params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self.make_request('POST', path, params=params, headers=headers, body=body)
        
    def put(self, path: str, body: Optional[str] = None,
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.make_request('PUT', path, params=params, headers=headers, body=body)
        
    def delete(self, path: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.make_request('DELETE', path, params=params, headers=headers)
        
    def close(self):
        """Close the session."""
        self.session.close()

