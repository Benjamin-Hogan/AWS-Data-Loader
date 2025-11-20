# REST Data Loader

A comprehensive Python-based data loader for REST applications with support for OpenAPI specifications. The project is organized into components to suit different needs and preferences.

## Project Structure

The project is divided into separate components:

### 1. **Essentials** - Core Non-GUI Components
All essential scripts to work without any GUI. Perfect for:
- Command-line usage
- Scripting and automation
- Integration into other applications
- Server-side operations

**Location**: `Essentials/`

**Features**:
- REST API Client with retry logic
- OpenAPI Parser (3.0, 3.1, Swagger 2.0)
- API Configuration Manager
- Autonomous Data Loader
- Command-Line Interface (CLI)

### 2. **Tkinter** - Basic GUI
A simple, functional Tkinter-based GUI. Perfect for:
- Basic GUI needs
- Systems without CustomTkinter
- Simple, lightweight interface

**Location**: `Tkinter/`

**Features**:
- Basic Tkinter interface
- All Essentials functionality
- Simple, functional design
- No additional dependencies beyond Essentials

### 3. **Web** - Advanced Web GUI
A modern, beautiful web-based GUI built with HTML/CSS/JavaScript. Perfect for:
- Modern, professional appearance
- No Python GUI dependencies
- Cross-platform compatibility
- Easy customization
- Remote access capability

**Location**: `Web/`

**Features**:
- Modern web interface with dark theme
- Real-time API testing
- OpenAPI specification integration
- Configuration management
- Autonomous data loading
- Request/response viewer with JSON formatting

### 4. **Simulation** - Testing Environment
A complete testing environment with a mock REST API server. Perfect for:
- Testing all components without external APIs
- Learning and experimentation
- Development and debugging
- Automated testing

**Location**: `Simulation/`

**Features**:
- Flask-based mock REST API server
- Complete OpenAPI 3.1 specification
- Sample test tasks and configurations
- Automated test scripts
- Comprehensive documentation

## Quick Start

### Essentials (CLI)

```bash
cd Essentials
pip install -r requirements.txt
python cli.py request GET /api/users --base-url http://localhost:8000
```

### Tkinter (Basic GUI)

```bash
cd Tkinter
pip install -r requirements.txt
python main.py
```

### Web (Advanced Web GUI)

```bash
cd Web
pip install -r requirements.txt
python app.py
```

Then open your browser and navigate to: `http://localhost:5000`

### Simulation (Testing Environment)

```bash
cd Simulation
pip install -r requirements.txt
python mock_server.py
```

Then in another terminal, run tests:
```bash
cd Simulation
python test_requests.py
```

## Component Comparison

| Feature | Essentials | Tkinter | Web |
|---------|-----------|---------|-----|
| GUI | ❌ CLI only | ✅ Basic | ✅ Modern Web |
| Dependencies | Minimal | Minimal | Flask + Browser |
| Use Case | Scripting/CLI | Basic GUI | Advanced Web GUI |
| Appearance | Terminal | Standard | Modern Web UI |
| Technology | Python | Python + Tkinter | Python + Web |

## Common Features (All Components)

- **Multiple API Configurations**: Manage multiple OpenAPI specifications
- **OpenAPI Support**: Parse OpenAPI 3.0, 3.1, and Swagger 2.0
- **Dynamic Endpoints**: Auto-generate forms from OpenAPI specs
- **Authentication**: Bearer token support
- **Autonomous Loading**: Execute batch requests from task files
- **Request/Response Handling**: Full HTTP method support

## Requirements

### Essentials
- Python 3.7+
- requests >= 2.31.0
- pyyaml >= 6.0.1
- urllib3 >= 2.0.0

### Tkinter
- All Essentials requirements
- Tkinter (usually included with Python)

### Web
- All Essentials requirements
- Flask >= 2.3.0
- Flask-CORS >= 4.0.0
- Modern web browser

## Installation

### Install All Components

```bash
# Essentials
cd Essentials && pip install -r requirements.txt && cd ..

# Tkinter
cd Tkinter && pip install -r requirements.txt && cd ..

# Web
cd Web && pip install -r requirements.txt && cd ..
```

### Install Individual Component

Navigate to the component directory and install its requirements:

```bash
cd Essentials  # or Tkinter or Web
pip install -r requirements.txt
```

## Usage Examples

### Essentials - CLI

```bash
# Make a request
python cli.py request GET /api/users --base-url http://localhost:8000

# Parse OpenAPI spec
python cli.py parse-openapi spec.yaml

# Execute tasks
python cli.py execute-tasks tasks.json
```

### Tkinter - GUI

1. Start the application: `python main.py`
2. Load OpenAPI specification: `File > Load OpenAPI Spec`
3. Configure base URL and authentication
4. Select endpoint and make requests
5. View responses in the response panel

## File Structure

```
AWS-Data-Loader/
├── Essentials/          # Core non-GUI components
│   ├── api_client.py
│   ├── openapi_parser.py
│   ├── api_config_manager.py
│   ├── autonomous_loader.py
│   ├── cli.py
│   ├── requirements.txt
│   └── README.md
├── Tkinter/             # Basic GUI
│   ├── main.py
│   ├── gui_components.py
│   ├── requirements.txt
│   └── README.md
├── Web/                 # Advanced Web GUI
│   ├── app.py
│   ├── static/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   ├── requirements.txt
│   └── README.md
├── Simulation/          # Testing environment
│   ├── mock_server.py
│   ├── mock_openapi.yaml
│   ├── test_tasks.json
│   ├── test_config.json
│   ├── test_requests.py
│   ├── requirements.txt
│   └── README.md
└── README.md            # This file
```

## Documentation

Each component has its own detailed README:
- [Essentials README](Essentials/README.md)
- [Tkinter README](Tkinter/README.md)
- [Web README](Web/README.md)
- [Simulation README](Simulation/README.md)

## Choosing the Right Component

- **Use Essentials if**:
  - You need CLI/scripting capabilities
  - You're integrating into other applications
  - You want minimal dependencies
  - You're running on servers without GUI

- **Use Tkinter if**:
  - You want a simple GUI
  - You prefer standard Tkinter widgets
  - You want a lightweight interface
  - You need a reliable, stable GUI solution

- **Use Web if**:
  - You want a modern, beautiful web interface
  - You don't want Python GUI dependencies
  - You need cross-platform compatibility
  - You want easy customization with HTML/CSS/JavaScript
  - You prefer web-based applications

- **Use Simulation if**:
  - You want to test the data loader without external APIs
  - You're learning how to use the components
  - You need a controlled testing environment
  - You want to experiment with different scenarios

## License

This project is provided as-is for use in REST API testing and data loading scenarios.

## Contributing

Feel free to submit issues or pull requests for improvements and bug fixes.
