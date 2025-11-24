"""
Autonomous Data Loader.
Automatically executes API requests based on configuration files.
"""

import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from api_config_manager import APIConfigManager, APIConfig


class RequestTask:
    """Represents a single request task."""
    
    def __init__(
        self,
        config_name: str,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        delay_before: float = 0.0,
        delay_after: float = 0.0
    ):
        """
        Initialize a request task.
        
        Args:
            config_name: Name of API configuration to use
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            headers: Additional headers
            body: Request body (JSON string)
            delay_before: Delay in seconds before making request
            delay_after: Delay in seconds after making request
        """
        self.config_name = config_name
        self.method = method.upper()
        self.path = path
        self.params = params or {}
        self.headers = headers or {}
        self.body = body
        self.delay_before = delay_before
        self.delay_after = delay_after
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'config_name': self.config_name,
            'method': self.method,
            'path': self.path,
            'params': self.params,
            'headers': self.headers,
            'body': self.body,
            'delay_before': self.delay_before,
            'delay_after': self.delay_after
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestTask':
        """Create task from dictionary."""
        return cls(
            config_name=data['config_name'],
            method=data['method'],
            path=data['path'],
            params=data.get('params'),
            headers=data.get('headers'),
            body=data.get('body'),
            delay_before=data.get('delay_before', 0.0),
            delay_after=data.get('delay_after', 0.0)
        )


class AutonomousLoader:
    """Autonomous data loader that executes requests automatically."""
    
    def __init__(
        self,
        config_manager: APIConfigManager,
        on_progress: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[List[RequestTask]], None]] = None,
        on_error: Optional[Callable[[RequestTask, str], None]] = None,
        on_task_complete: Optional[Callable[[RequestTask, Dict[str, Any]], None]] = None
    ):
        """
        Initialize the autonomous loader.
        
        Args:
            config_manager: APIConfigManager instance
            on_progress: Callback for progress updates (receives message string)
            on_complete: Callback when all tasks complete (receives list of tasks)
            on_error: Callback for errors (receives task and error message)
            on_task_complete: Callback when a task completes (receives task and result dict)
        """
        self.config_manager = config_manager
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_task_complete = on_task_complete
        self.is_running = False
        self.tasks: List[RequestTask] = []
        self.results: List[Dict[str, Any]] = []
        self.variables: Dict[str, Any] = {}  # Store variables for substitution
        self.enable_variable_substitution = True  # Enable variable substitution
    
    def load_tasks_from_file(self, file_path: str) -> List[RequestTask]:
        """
        Load tasks from a JSON configuration file.
        
        Args:
            file_path: Path to JSON file containing task definitions
            
        Returns:
            List of RequestTask instances
            
        Example JSON format:
        {
            "tasks": [
                {
                    "config_name": "api1",
                    "method": "GET",
                    "path": "/api/users",
                    "params": {"limit": 10},
                    "delay_before": 1.0,
                    "delay_after": 0.5
                },
                {
                    "config_name": "api2",
                    "method": "POST",
                    "path": "/api/data",
                    "body": "{\"key\": \"value\"}",
                    "headers": {"Content-Type": "application/json"}
                },
                {
                    "config_name": "api3",
                    "method": "POST",
                    "path": "/api/data",
                    "body_file": "example_request.json",
                    "headers": {"Content-Type": "application/json"}
                }
            ]
        }
        
        Note: If both "body" and "body_file" are specified, "body_file" takes precedence.
        The "body_file" path is resolved relative to the task file's directory.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {file_path}")
        
        task_file_dir = path.parent
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tasks = []
        for task_data in data.get('tasks', []):
            try:
                # Handle body_file: load JSON from file and convert to string
                if 'body_file' in task_data:
                    body_file_path = Path(task_data['body_file'])
                    
                    # Resolve path relative to task file directory if not absolute
                    if not body_file_path.is_absolute():
                        body_file_path = task_file_dir / body_file_path
                    
                    if not body_file_path.exists():
                        raise FileNotFoundError(
                            f"Body file not found: {body_file_path} "
                            f"(resolved from: {task_data['body_file']})"
                        )
                    
                    # Load JSON from file
                    with open(body_file_path, 'r', encoding='utf-8') as body_f:
                        body_data = json.load(body_f)
                    
                    # Convert to JSON string
                    task_data['body'] = json.dumps(body_data, ensure_ascii=False)
                    # Remove body_file from task_data to avoid confusion
                    del task_data['body_file']
                
                task = RequestTask.from_dict(task_data)
                tasks.append(task)
            except Exception as e:
                if self.on_error:
                    # Create a dummy task for error reporting
                    dummy_task = RequestTask(
                        config_name=task_data.get('config_name', 'unknown'),
                        method=task_data.get('method', 'GET'),
                        path=task_data.get('path', '/')
                    )
                    self.on_error(dummy_task, f"Failed to parse task: {e}")
        
        return tasks
    
    def add_task(self, task: RequestTask):
        """Add a single task to the queue."""
        self.tasks.append(task)
    
    def add_tasks(self, tasks: List[RequestTask]):
        """Add multiple tasks to the queue."""
        self.tasks.extend(tasks)
    
    def clear_tasks(self):
        """Clear all tasks."""
        self.tasks.clear()
        self.results.clear()
    
    def _substitute_variables(self, value: Any) -> Any:
        """
        Substitute variables in a value.
        Supports {{variable_name}} syntax and JSON path extraction {{task_index.response.json.path}}.
        
        Args:
            value: Value to substitute (can be string, dict, list, etc.)
            
        Returns:
            Value with variables substituted
        """
        if not self.enable_variable_substitution:
            return value
        
        if isinstance(value, str):
            # Find all variable references {{...}}
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, value)
            
            for match in matches:
                var_expr = match.strip()
                replacement = None
                
                # Handle JSON path extraction: {{task_index.response.json.path}}
                if '.' in var_expr:
                    parts = var_expr.split('.')
                    if len(parts) >= 3 and parts[1] == 'response':
                        try:
                            task_idx = int(parts[0])
                            if 0 <= task_idx < len(self.results):
                                result = self.results[task_idx]
                                if result.get('success') and 'response' in result:
                                    response = result['response']
                                    
                                    # Navigate through the path
                                    data = response
                                    for part in parts[2:]:
                                        if part == 'json' and 'json' in data:
                                            data = data['json']
                                        elif part == 'body' and 'body' in data:
                                            data = data['body']
                                        elif isinstance(data, dict):
                                            data = data.get(part)
                                        elif isinstance(data, list):
                                            try:
                                                data = data[int(part)]
                                            except (ValueError, IndexError):
                                                data = None
                                        else:
                                            data = None
                                        
                                        if data is None:
                                            break
                                    
                                    replacement = str(data) if data is not None else ''
                        except (ValueError, IndexError):
                            pass
                
                # Handle simple variable: {{variable_name}}
                if replacement is None and var_expr in self.variables:
                    replacement = str(self.variables[var_expr])
                
                # Handle built-in variables
                if replacement is None:
                    if var_expr == 'timestamp':
                        replacement = datetime.now().isoformat()
                    elif var_expr == 'timestamp_unix':
                        replacement = str(int(time.time()))
                
                # Replace the variable
                if replacement is not None:
                    value = value.replace(f'{{{{{var_expr}}}}}', replacement)
                else:
                    # Variable not found, leave as is or replace with empty string
                    # Uncomment the next line to replace unknown variables with empty string
                    # value = value.replace(f'{{{{{var_expr}}}}}', '')
                    pass
            
            return value
        
        elif isinstance(value, dict):
            return {k: self._substitute_variables(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._substitute_variables(item) for item in value]
        
        else:
            return value
    
    def set_variable(self, name: str, value: Any):
        """Set a variable for substitution."""
        self.variables[name] = value
    
    def get_variable(self, name: str) -> Optional[Any]:
        """Get a variable value."""
        return self.variables.get(name)
    
    def clear_variables(self):
        """Clear all variables."""
        self.variables.clear()
    
    def execute_task(self, task: RequestTask) -> Dict[str, Any]:
        """
        Execute a single task with variable substitution.
        
        Args:
            task: RequestTask to execute
            
        Returns:
            Dictionary with task result information
        """
        config = self.config_manager.get_config(task.config_name)
        if not config:
            error_msg = f"Configuration '{task.config_name}' not found"
            task.error = error_msg
            if self.on_error:
                self.on_error(task, error_msg)
            return {'success': False, 'error': error_msg}
        
        if not config.api_client:
            error_msg = f"API client not initialized for '{task.config_name}'"
            task.error = error_msg
            if self.on_error:
                self.on_error(task, error_msg)
            return {'success': False, 'error': error_msg}
        
        try:
            # Delay before request
            if task.delay_before > 0:
                time.sleep(task.delay_before)
            
            # Substitute variables in task properties
            substituted_path = self._substitute_variables(task.path)
            substituted_params = self._substitute_variables(task.params) if task.params else None
            substituted_headers = self._substitute_variables(task.headers) if task.headers else None
            substituted_body = self._substitute_variables(task.body) if task.body else None
            
            # Make request
            response = config.api_client.make_request(
                method=task.method,
                path=substituted_path,
                params=substituted_params,
                headers=substituted_headers,
                body=substituted_body
            )
            
            task.result = response
            task.executed_at = datetime.now()
            
            # Extract response data for variable storage (if task has extract_vars)
            # This allows storing response data for use in subsequent tasks
            if hasattr(task, 'extract_vars') and task.extract_vars:
                for var_name, json_path in task.extract_vars.items():
                    try:
                        # Navigate JSON path
                        data = response.get('json', {})
                        for part in json_path.split('.'):
                            if isinstance(data, dict):
                                data = data.get(part)
                            elif isinstance(data, list):
                                try:
                                    data = data[int(part)]
                                except (ValueError, IndexError):
                                    data = None
                            else:
                                data = None
                            
                            if data is None:
                                break
                        
                        if data is not None:
                            self.set_variable(var_name, data)
                    except Exception:
                        pass
            
            # Delay after request
            if task.delay_after > 0:
                time.sleep(task.delay_after)
            
            result = {
                'success': True,
                'task': task,
                'response': response,
                'executed_at': task.executed_at.isoformat()
            }
            
            self.results.append(result)
            
            # Call task complete callback for streaming results
            if self.on_task_complete:
                self.on_task_complete(task, result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            task.error = error_msg
            task.executed_at = datetime.now()
            
            if self.on_error:
                self.on_error(task, error_msg)
            
            result = {
                'success': False,
                'task': task,
                'error': error_msg,
                'executed_at': task.executed_at.isoformat()
            }
            
            self.results.append(result)
            
            # Call task complete callback for streaming results
            if self.on_task_complete:
                self.on_task_complete(task, result)
            
            return result
    
    def execute_all(self, stop_on_error: bool = False):
        """
        Execute all tasks in sequence.
        
        Args:
            stop_on_error: If True, stop execution on first error
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.results.clear()
        
        total = len(self.tasks)
        
        for idx, task in enumerate(self.tasks, 1):
            if not self.is_running:
                break
            
            if self.on_progress:
                self.on_progress(f"Executing task {idx}/{total}: {task.method} {task.path} ({task.config_name})")
            
            result = self.execute_task(task)
            
            if not result['success'] and stop_on_error:
                if self.on_progress:
                    self.on_progress(f"Stopped due to error: {result.get('error', 'Unknown error')}")
                break
        
        self.is_running = False
        
        if self.on_complete:
            self.on_complete(self.tasks)
        
        if self.on_progress:
            self.on_progress(f"Completed {len(self.results)} task(s)")
    
    def stop(self):
        """Stop execution."""
        self.is_running = False
    
    def save_results(self, file_path: str):
        """
        Save execution results to a JSON file.
        
        Args:
            file_path: Path to save results
        """
        results_data = {
            'executed_at': datetime.now().isoformat(),
            'total_tasks': len(self.tasks),
            'results': []
        }
        
        for result in self.results:
            task = result['task']
            result_data = {
                'config_name': task.config_name,
                'method': task.method,
                'path': task.path,
                'executed_at': result.get('executed_at'),
                'success': result['success']
            }
            
            if result['success']:
                response = result['response']
                result_data['status_code'] = response.get('status_code')
                result_data['response_size'] = len(response.get('body', ''))
            else:
                result_data['error'] = result.get('error')
            
            results_data['results'].append(result_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

