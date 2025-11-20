"""
REST API Client for making HTTP requests.
Handles authentication, request formatting, and response processing.
"""

import http.client
import json
import time
import urllib.parse
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class RequestException(Exception):
    """Exception raised for request errors."""
    pass


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
        
        # Parse base URL to extract scheme, hostname, port, and base path
        parsed = urlparse(self.base_url)
        self.scheme = parsed.scheme
        self.hostname = parsed.hostname
        self.port = parsed.port or (443 if self.scheme == 'https' else 80)
        self.base_path = parsed.path.rstrip('/')  # Base path from URL (e.g., '/v1')
        
        # Retry configuration
        self.retry_total = 3
        self.retry_backoff_factor = 1
        self.retry_status_codes = [429, 500, 502, 503, 504]
        
        # Default headers
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Session headers (for auth and custom headers)
        self.session_headers: Dict[str, str] = {}
        
    def set_auth_token(self, token: str, auth_type: str = 'Bearer'):
        """
        Set authentication token.
        
        Args:
            token: Authentication token
            auth_type: Type of authentication (Bearer, Token, etc.)
        """
        self.session_headers['Authorization'] = f'{auth_type} {token}'
        
    def set_headers(self, headers: Dict[str, str]):
        """
        Set custom headers.
        
        Args:
            headers: Dictionary of header key-value pairs
        """
        self.session_headers.update(headers)
        
    def _create_connection(self) -> http.client.HTTPConnection:
        """Create an HTTP or HTTPS connection based on the scheme."""
        if self.scheme == 'https':
            return http.client.HTTPSConnection(self.hostname, self.port, timeout=self.timeout)
        else:
            return http.client.HTTPConnection(self.hostname, self.port, timeout=self.timeout)
    
    def _build_path(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build the full path with base path and query parameters."""
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        # Combine base path with endpoint path
        full_path = self.base_path + path
        
        # Add query parameters if provided
        if params:
            query_string = urllib.parse.urlencode(params)
            return f"{full_path}?{query_string}"
        return full_path
    
    def _make_single_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Make a single HTTP request without retry logic."""
        conn = None
        try:
            conn = self._create_connection()
            conn.request(method.upper(), path, body=body, headers=headers)
            response = conn.getresponse()
            
            # Read response body
            response_body = response.read()
            response_text = response_body.decode('utf-8', errors='replace')
            
            # Get response headers
            response_headers = {}
            for header, value in response.getheaders():
                response_headers[header.lower()] = value
            
            # Build full URL for result
            full_url = f"{self.base_url}{path}"
            
            result = {
                'status_code': response.status,
                'headers': response_headers,
                'url': full_url,
                'method': method.upper(),
                'body': response_text,
                'json': None
            }
            
            # Try to parse JSON response
            try:
                result['json'] = json.loads(response_text)
            except (ValueError, json.JSONDecodeError):
                pass
            
            return result
            
        except (ConnectionError, OSError, TimeoutError) as e:
            raise RequestException(f"Failed to connect to {self.base_url}: {str(e)}")
        except Exception as e:
            raise RequestException(f"Request failed: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic.
        
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
            RequestException: If the request fails
        """
        # Build full path with query parameters
        full_path = self._build_path(path, params)
        
        # Prepare headers (merge default, session, and request headers)
        request_headers = self.default_headers.copy()
        request_headers.update(self.session_headers)
        if headers:
            request_headers.update(headers)
        
        # Prepare body
        body_bytes = None
        if body:
            try:
                # Try to parse as JSON to validate
                json.loads(body)
                # If valid JSON, send as-is
                body_bytes = body.encode('utf-8')
            except json.JSONDecodeError:
                # If not valid JSON, send as raw string
                request_headers['Content-Type'] = 'text/plain'
                body_bytes = body.encode('utf-8')
        
        # Retry logic
        last_exception = None
        for attempt in range(self.retry_total):
            try:
                result = self._make_single_request(
                    method, full_path, request_headers, body_bytes
                )
                
                # Check if we should retry based on status code
                if result['status_code'] in self.retry_status_codes:
                    if attempt < self.retry_total - 1:
                        # Calculate backoff delay
                        delay = self.retry_backoff_factor * (2 ** attempt)
                        time.sleep(delay)
                        continue
                
                # Success or non-retryable status code
                return result
                
            except RequestException as e:
                last_exception = e
                if attempt < self.retry_total - 1:
                    # Calculate backoff delay
                    delay = self.retry_backoff_factor * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RequestException("Request failed after retries")
            
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
        """Close the session (no-op for http.client, kept for compatibility)."""
        pass

