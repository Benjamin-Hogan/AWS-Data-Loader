# REST Data Loader - Essentials

Core non-GUI components for the REST Data Loader. This package provides all essential functionality for interacting with REST APIs, parsing OpenAPI specifications, managing API configurations, and executing autonomous data loading tasks.

## Features

- **REST API Client**: Make HTTP requests with retry logic, authentication, and timeout handling
- **OpenAPI Parser**: Parse OpenAPI 3.0, 3.1, and Swagger 2.0 specifications (JSON/YAML)
- **API Configuration Manager**: Manage multiple API configurations with different endpoints and ports
- **Autonomous Loader**: Execute batch API requests from task configuration files
- **Command-Line Interface**: Simple CLI for all operations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Interface

#### Make an API Request

```bash
# GET request
python cli.py request GET /api/users --base-url http://localhost:8000

# POST request with JSON body
python cli.py request POST /api/users --base-url http://localhost:8000 --body '{"name":"John","email":"john@example.com"}'

# With authentication token
python cli.py request GET /api/users --base-url http://localhost:8000 --token your-token-here

# With query parameters
python cli.py request GET /api/users --base-url http://localhost:8000 --params '{"limit":10,"offset":0}'
```

#### Parse OpenAPI Specification

```bash
# Parse and display endpoints
python cli.py parse-openapi spec.yaml

# Save parsed data to file
python cli.py parse-openapi spec.yaml --output parsed.json
```

#### Execute Autonomous Tasks

```bash
# Execute tasks from JSON file
python cli.py execute-tasks tasks.json

# Save results to file
python cli.py execute-tasks tasks.json --output results.json

# Stop on first error
python cli.py execute-tasks tasks.json --stop-on-error
```

#### Manage API Configurations

```bash
# List all configurations
python cli.py config list

# Add a new configuration
python cli.py config add --name api1 --base-url http://localhost:8000 --spec-file spec.yaml

# Remove a configuration
python cli.py config remove --name api1

# Set active configuration
python cli.py config set-active --name api1
```

### Python API

#### Using APIClient

```python
from api_client import APIClient

# Create client
client = APIClient("http://localhost:8000")

# Set authentication
client.set_auth_token("your-token")

# Make requests
response = client.get("/api/users")
print(response['status_code'])
print(response['json'])

# POST request
response = client.post(
    "/api/users",
    body='{"name": "John", "email": "john@example.com"}'
)
```

#### Using OpenAPIParser

```python
from openapi_parser import OpenAPIParser

parser = OpenAPIParser()
spec = parser.parse("spec.yaml")
endpoints = parser.get_endpoints()

for path, methods in endpoints.items():
    print(f"{path}: {list(methods.keys())}")
```

#### Using APIConfigManager

```python
from api_config_manager import APIConfigManager

manager = APIConfigManager()

# Add configuration
config = manager.add_config(
    name="api1",
    base_url="http://localhost:8000",
    openapi_spec_path="spec.yaml",
    auth_token="token123"
)

# Get configuration
config = manager.get_config("api1")
response = config.api_client.get("/api/users")
```

#### Using AutonomousLoader

```python
from api_config_manager import APIConfigManager
from autonomous_loader import AutonomousLoader

config_manager = APIConfigManager()
loader = AutonomousLoader(
    config_manager=config_manager,
    on_progress=lambda msg: print(msg),
    on_complete=lambda tasks: print(f"Completed {len(tasks)} tasks"),
    on_error=lambda task, error: print(f"Error: {error}")
)

# Load and execute tasks
tasks = loader.load_tasks_from_file("tasks.json")
loader.add_tasks(tasks)
loader.execute_all()
```

## Components

### `api_client.py`
REST API client with:
- Automatic retry logic for transient failures
- Bearer token authentication
- Custom headers support
- JSON and raw body support
- Timeout handling

### `openapi_parser.py`
OpenAPI specification parser supporting:
- OpenAPI 3.0, 3.1, and Swagger 2.0
- JSON and YAML formats
- Endpoint extraction
- Parameter and request body schema extraction

### `api_config_manager.py`
Configuration management with:
- Multiple API configurations
- Persistent storage (JSON)
- Active configuration tracking
- OpenAPI spec integration

### `autonomous_loader.py`
Autonomous task execution with:
- Batch request execution
- Task delays (before/after)
- Progress callbacks
- Error handling
- Result saving
- Variable substitution ({{variable_name}})
- Response data extraction from previous tasks
- Built-in variables (timestamp, timestamp_unix)

### `cli.py`
Command-line interface for all operations.

## Task Configuration Format

Tasks are defined in JSON format:

```json
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
      "config_name": "api1",
      "method": "POST",
      "path": "/api/users",
      "body": "{\"name\": \"John\", \"timestamp\": \"{{timestamp}}\"}",
      "headers": {"Content-Type": "application/json"}
    },
    {
      "config_name": "api1",
      "method": "POST",
      "path": "/api/users",
      "body_file": "example_request.json",
      "headers": {"Content-Type": "application/json"}
    },
    {
      "config_name": "api1",
      "method": "GET",
      "path": "/api/users/{{0.response.json.id}}",
      "extract_vars": {
        "user_id": "id",
        "user_name": "name"
      }
    }
  ]
}
```

### Task Fields

- `config_name` (required): Name of the API configuration to use
- `method` (required): HTTP method (GET, POST, PUT, DELETE, etc.)
- `path` (required): API endpoint path (supports variable substitution)
- `params` (optional): Query parameters as a dictionary (supports variable substitution)
- `headers` (optional): Additional headers as a dictionary (supports variable substitution)
- `body` (optional): Request body as a JSON string (use this for inline JSON, supports variable substitution)
- `body_file` (optional): Path to a JSON file containing the request body (resolved relative to the task file)
- `delay_before` (optional): Delay in seconds before making the request (default: 0.0)
- `delay_after` (optional): Delay in seconds after making the request (default: 0.0)
- `extract_vars` (optional): Dictionary mapping variable names to JSON paths for extracting data from response

**Note**: If both `body` and `body_file` are specified, `body_file` takes precedence. The `body_file` path is resolved relative to the task file's directory.

### Variable Substitution

The autonomous loader supports variable substitution using `{{variable_name}}` syntax:

- **Simple variables**: `{{variable_name}}` - References a variable set via `set_variable()` or extracted from previous responses
- **Response data**: `{{task_index.response.json.path}}` - Extracts data from a previous task's response
  - Example: `{{0.response.json.id}}` gets the `id` field from the JSON response of the first task (index 0)
  - Example: `{{1.response.json.data.items.0.name}}` navigates nested JSON structures
- **Built-in variables**:
  - `{{timestamp}}` - Current ISO timestamp
  - `{{timestamp_unix}}` - Current Unix timestamp

### Response Data Extraction

Use the `extract_vars` field to automatically extract data from responses for use in subsequent tasks:

```json
{
  "config_name": "api1",
  "method": "POST",
  "path": "/api/users",
  "body": "{\"name\": \"John\"}",
  "extract_vars": {
    "user_id": "id",
    "user_email": "email",
    "created_at": "created_at"
  }
}
```

This extracts `id`, `email`, and `created_at` from the response JSON and makes them available as variables for subsequent tasks.

## Requirements

- Python 3.7+
- requests >= 2.31.0
- pyyaml >= 6.0.1
- urllib3 >= 2.0.0

## License

This project is provided as-is for use in REST API testing and data loading scenarios.

