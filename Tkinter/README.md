# REST Data Loader - Tkinter (Basic GUI)

A basic Tkinter-based GUI for the REST Data Loader. This provides a simple, functional interface for interacting with REST APIs using OpenAPI specifications.

## Features

- **Tabbed Interface**: Streamlined interface with tabs for different features
- **API Testing Tab**: Main interface for testing endpoints
  - Support for JSON, multipart/form-data, and form-urlencoded requests
  - Dynamic forms based on OpenAPI specifications
  - File upload support for multipart requests
- **Config Management Tab**: Manage multiple API configurations in-app
- **Autonomous Loader Tab**: 
  - Execute batch requests with real-time result streaming
  - Task editor for creating and managing configurations
  - Support for multipart form data and file uploads
  - Response variable extraction for chaining requests
  - Export results in JSON or text format
- **Multiple API Configurations**: Manage multiple OpenAPI specifications
- **Dynamic Endpoint Generation**: Automatically creates forms from OpenAPI specs
- **Request/Response Viewer**: View formatted JSON responses
- **Autonomous Data Loading**: Execute batch requests from task files
- **Search Functionality**: Quick search for endpoints
- **Response Variable Extraction**: Extract values from responses for use in subsequent requests

## Installation

```bash
pip install -r requirements.txt
```

**Note**: Tkinter is usually included with Python. If not available, install it:
- **Ubuntu/Debian**: `sudo apt-get install python3-tk`
- **macOS**: Tkinter comes with Python
- **Windows**: Tkinter comes with Python

## Usage

### Starting the Application

```bash
python main.py
```

### Basic Workflow

1. **Load OpenAPI Specification**:
   - Go to `File > Load OpenAPI Spec`
   - Select your OpenAPI specification file (YAML or JSON)
   - Enter a configuration name and base URL when prompted

2. **Configure API**:
   - Enter the base URL in the Configuration panel
   - Click "Update URL"
   - Optionally set an authentication token

3. **Make Requests**:
   - Select an endpoint from the list
   - Choose HTTP method (GET, POST, etc.)
   - Fill in parameters if needed
   - For POST/PUT requests:
     - **JSON requests**: Enter JSON body or load from file
     - **Multipart/form-data**: Use the "Add Field" and "Add File" buttons to add form fields and files
     - **Form-urlencoded**: Use the "Add Field" button to add key-value pairs
   - Click "Send Request"

4. **View Responses**:
   - Responses appear in the right panel
   - Status codes are color-coded
   - JSON is automatically formatted
   - Use "Copy Response" to copy to clipboard

### Managing Configurations

- **Access Config Management**: Click the "Config Management" tab or go to `File > Manage API Configurations`
- **Add Configuration**: Click "Add" button in the Config Management tab
- **Remove Configuration**: Select a configuration and click "Remove Selected"
- **Refresh OpenAPI Spec**: 
  - In Config Management tab: Select a configuration and click "Refresh OpenAPI Spec" to reload the spec from the file
  - In API Testing tab: Click "Refresh Spec" button next to the config selector to refresh the current configuration's spec
  - Useful when OpenAPI spec files are updated in a git repository
- **Switch Configuration**: Use the dropdown in the API Configuration panel on the API Testing tab

### Autonomous Data Loading

The Autonomous Loader tab includes two sub-tabs:

#### Task Editor Tab

1. **Create/Edit Task Configurations**:
   - Click "New Config" to create a new task configuration
   - Use the config dropdown to switch between different configurations
   - Add tasks using the "Add Task" button
   - Edit tasks by selecting them from the list
   - Reorder tasks using "Move Up" and "Move Down" buttons
   - Remove tasks with "Remove Task"

2. **Task Editor**:
   - Select an API configuration from the dropdown
   - Choose HTTP method (GET, POST, PUT, PATCH, DELETE)
   - Enter the endpoint path
   - Add query parameters (JSON format)
   - Add headers (JSON format)
   - Enter request body (JSON format) or load from file using "Load File" button
   - **Multipart Data** (optional): Add form fields for multipart/form-data requests (JSON format)
   - **Multipart Files** (optional): Add file uploads for multipart requests (JSON format)
     - Format: `{"file1": "path/to/file.pdf"}` or `{"file1": ["path/to/file.jpg", "image/jpeg"]}`
   - **Extract Vars** (optional): Define variables to extract from responses (JSON format)
     - Format: `{"token": "json.access_token", "user_id": "json.user.id"}`
     - Path formats: `json.field`, `body`, `headers.header_name`, `status_code`
   - Configure delays (before/after request)

3. **Save/Load Configurations**:
   - Click "Save Config" to save the current configuration to a JSON file
   - Click "Load Config" to load a task configuration from a file
   - Configurations are managed in-memory and can be switched between easily

#### Execute Tasks Tab

1. **Choose Task Source**:
   - Select "Use Editor Config" to execute tasks from the editor
   - Select "Load from File" to execute tasks from a JSON file
   - Choose the configuration or file to use

2. **Execution Options**:
   - Enable "Stop on Error" to halt execution on first error
   - Monitor progress in real-time with streaming results

3. **Execute**:
   - Click "Execute Tasks" to start execution
   - View progress and results streamed in real-time to the progress window
   - Each task result is displayed immediately with:
     - Success/failure indicator (✓/✗)
     - Status code and response preview
     - Execution timestamp
     - Error details (if failed)

4. **Export Results**:
   - **Export Results**: Export execution results in JSON or text format
     - JSON format: Structured data with all response details
     - Text format: Human-readable formatted report with full response bodies
   - **Export Log**: Export the entire progress log as a text file

**Note**: All features are now integrated into tabs within the main window - no more pop-up dialogs!

## Dependencies

This component uses the **Essentials** package (located in `../Essentials/`). Make sure the Essentials directory is accessible.

## Requirements

- Python 3.7+
- Tkinter (usually included with Python)
- requests >= 2.31.0
- pyyaml >= 6.0.1
- urllib3 >= 2.0.0

## Components

### `main.py`
Main application class that orchestrates the GUI and handles user interactions.

### `gui_components.py`
Custom Tkinter widgets:
- **ConfigFrame**: URL and authentication configuration
- **EndpointFrame**: Dynamic endpoint forms with parameter inputs
- **ResponseFrame**: Response viewer with formatting

## Limitations

- Basic Tkinter styling (no modern themes)
- Standard Tkinter widgets only
- No dark mode support
- Limited customization options

## License

This project is provided as-is for use in REST API testing and data loading scenarios.

