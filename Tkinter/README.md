# REST Data Loader - Tkinter (Basic GUI)

A basic Tkinter-based GUI for the REST Data Loader. This provides a simple, functional interface for interacting with REST APIs using OpenAPI specifications.

## Features

- **Basic Tkinter GUI**: Simple, functional interface
- **Multiple API Configurations**: Manage multiple OpenAPI specifications
- **Dynamic Endpoint Generation**: Automatically creates forms from OpenAPI specs
- **Request/Response Viewer**: View formatted JSON responses
- **Autonomous Data Loading**: Execute batch requests from task files
- **Search Functionality**: Quick search for endpoints

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
   - For POST/PUT requests, enter JSON body or load from file
   - Click "Send Request"

4. **View Responses**:
   - Responses appear in the right panel
   - Status codes are color-coded
   - JSON is automatically formatted
   - Use "Copy Response" to copy to clipboard

### Managing Configurations

- **Add Configuration**: `File > Manage API Configurations > Add`
- **Remove Configuration**: `File > Manage API Configurations > Remove`
- **Switch Configuration**: Use the dropdown in the API Configuration panel

### Autonomous Data Loading

1. Go to `Tools > Autonomous Data Loader`
2. Select a task configuration file (JSON)
3. Click "Execute Tasks"
4. Monitor progress in the progress window
5. Save results when complete

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

