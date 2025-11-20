# Simulation Environment

A complete testing environment for the AWS Data Loader project. This simulation includes a mock REST API server, sample OpenAPI specifications, test task files, and automated test scripts.

## Overview

The simulation environment provides:
- **Mock REST API Server**: A Flask-based server that simulates a real REST API
- **OpenAPI Specification**: Complete OpenAPI 3.1 spec for the mock API
- **Test Tasks**: Sample task files for testing autonomous loading
- **Test Scripts**: Automated tests for all components
- **Configuration Files**: Ready-to-use API configurations

## Quick Start

### 1. Install Dependencies

```bash
cd Simulation
pip install -r requirements.txt
```

### 2. Start the Mock Server

```bash
python mock_server.py
```

The server will start on `http://localhost:8000`. You should see:
```
============================================================
Mock REST API Server
============================================================
Server starting on http://localhost:8000
...
```

### 3. Run Tests

In a new terminal window:

```bash
cd Simulation
python test_requests.py
```

## Mock API Endpoints

The mock server provides the following endpoints:

### Health
- `GET /api/health` - Health check endpoint

### Users
- `GET /api/users` - Get all users (supports `limit`, `offset`, `search` query params)
- `GET /api/users/{id}` - Get user by ID
- `POST /api/users` - Create a new user
- `PUT /api/users/{id}` - Update a user
- `DELETE /api/users/{id}` - Delete a user

### Posts
- `GET /api/posts` - Get all posts (supports `author_id`, `limit`, `offset` query params)
- `GET /api/posts/{id}` - Get post by ID
- `POST /api/posts` - Create a new post

### Testing Utilities
- `POST /api/data` - Generic data endpoint for testing POST requests
- `GET /api/slow?delay=<seconds>` - Slow endpoint for testing timeouts
- `GET /api/error/{status_code}` - Returns specific error codes (400, 401, 403, 404, 500, 503)
- `* /api/echo` - Echo endpoint that returns request details (supports all HTTP methods)

## Testing with Essentials (CLI)

### 1. Basic Request

```bash
cd ../Essentials
python cli.py request GET /api/health --base-url http://localhost:8000
```

### 2. Parse OpenAPI Spec

```bash
python cli.py parse-openapi ../Simulation/mock_openapi.yaml
```

### 3. Execute Tasks

First, make sure you have a configuration set up:

```bash
python cli.py config add --name "Mock API" --base-url http://localhost:8000 --spec-file ../Simulation/mock_openapi.yaml
python cli.py config set-active --name "Mock API"
```

Then execute tasks:

```bash
python cli.py execute-tasks ../Simulation/test_tasks.json
```

## Testing with GUI Applications

### Using Tkinter GUI

1. Start the mock server: `python mock_server.py`
2. Start the Tkinter GUI: `cd ../Tkinter && python main.py`
3. Load the OpenAPI spec and configure as above

## File Structure

```
Simulation/
├── mock_server.py          # Flask mock API server
├── mock_openapi.yaml       # OpenAPI 3.1 specification
├── test_tasks.json         # Sample task file for autonomous loading
├── test_config.json        # Sample API configuration
├── test_requests.py        # Automated test script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Test Scripts

### `test_requests.py`

Comprehensive test script that demonstrates:
- Basic API requests (GET, POST, PUT, DELETE)
- OpenAPI parsing
- Configuration management
- Autonomous task loading and execution

Run it with:
```bash
python test_requests.py
```

## Sample Data

The mock server starts with sample data:

**Users:**
- ID 1: John Doe (john@example.com, age 30)
- ID 2: Jane Smith (jane@example.com, age 25)
- ID 3: Bob Johnson (bob@example.com, age 35)

**Posts:**
- ID 1: "First Post" by author 1
- ID 2: "Second Post" by author 2

## Testing Scenarios

### 1. Basic CRUD Operations
Test creating, reading, updating, and deleting resources:
```bash
# Create
python cli.py request POST /api/users --base-url http://localhost:8000 --body '{"name":"Test","email":"test@example.com"}'

# Read
python cli.py request GET /api/users/1 --base-url http://localhost:8000

# Update
python cli.py request PUT /api/users/1 --base-url http://localhost:8000 --body '{"name":"Updated"}'

# Delete
python cli.py request DELETE /api/users/1 --base-url http://localhost:8000
```

### 2. Query Parameters
Test pagination and filtering:
```bash
python cli.py request GET /api/users --base-url http://localhost:8000 --params '{"limit":2,"offset":0}'
python cli.py request GET /api/users --base-url http://localhost:8000 --params '{"search":"John"}'
```

### 3. Error Handling
Test error responses:
```bash
python cli.py request GET /api/error/404 --base-url http://localhost:8000
python cli.py request GET /api/error/500 --base-url http://localhost:8000
```

### 4. Timeout Testing
Test slow endpoints:
```bash
python cli.py request GET /api/slow --base-url http://localhost:8000 --params '{"delay":3}'
```

### 5. Autonomous Loading
Test batch execution:
```bash
python cli.py execute-tasks test_tasks.json
```

## Configuration

### Using test_config.json

The `test_config.json` file is pre-configured for the mock API. To use it:

1. Copy it to the main directory or use it directly:
```bash
cp test_config.json ../api_configs.json
```

2. Or use the CLI to add the configuration:
```bash
cd ../Essentials
python cli.py config add --name "Mock API" --base-url http://localhost:8000 --spec-file ../Simulation/mock_openapi.yaml
```

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Make sure Flask is installed: `pip install flask flask-cors`
- Check Python version (3.7+ required)

### Connection refused
- Make sure the mock server is running
- Verify the server is on `http://localhost:8000`
- Check firewall settings

### Import errors in test scripts
- Make sure you're running from the Simulation directory
- Verify the Essentials directory exists at `../Essentials`
- Check that all required packages are installed

### Tasks fail to execute
- Ensure the mock server is running
- Verify the configuration name matches in `test_tasks.json`
- Check that the base URL is correct

## Customization

### Adding New Endpoints

Edit `mock_server.py` to add new endpoints. Follow the existing pattern:

```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({"message": "Custom endpoint"}), 200
```

### Modifying Sample Data

Edit the initial data in `mock_server.py`:
```python
users_db = [
    # Your custom users here
]
```

### Creating Custom Test Tasks

Edit `test_tasks.json` to add your own test scenarios. Follow the format:
```json
{
  "tasks": [
    {
      "config_name": "Mock API",
      "method": "GET",
      "path": "/api/your-endpoint",
      "params": {},
      "delay_before": 0.5,
      "delay_after": 0.5
    }
  ]
}
```

## Notes

- The mock server uses in-memory storage. Data resets when the server restarts.
- All endpoints support CORS for browser-based testing.
- The server runs in debug mode by default for easier development.
- Error endpoints are useful for testing retry logic and error handling.

## License

This simulation environment is part of the AWS Data Loader project and is provided as-is for testing purposes.

