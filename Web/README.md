# REST Data Loader - Web GUI (Advanced)

A modern, beautiful web-based GUI for the REST Data Loader. Built with HTML, CSS, and JavaScript, this provides a professional interface without Python GUI dependencies.

## Features

- **Modern Web Interface**: Beautiful, responsive design with dark theme
- **No Python GUI Dependencies**: Pure web technologies (HTML/CSS/JavaScript)
- **Real-time API Testing**: Make requests and view responses instantly
- **OpenAPI Integration**: Load and explore OpenAPI specifications
- **Configuration Management**: Manage multiple API configurations
- **Autonomous Loading**: Execute batch requests from task files
- **Request/Response Viewer**: Formatted JSON with syntax highlighting
- **Parameter Forms**: Auto-generated forms from OpenAPI specs
- **Requirements Display**: Clear indication of required vs optional parameters

## Installation

```bash
cd Web
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`. Open your browser and navigate to that URL.

### Basic Workflow

1. **Add Configuration**:
   - Click "Manage" → "Add Configuration"
   - Enter name, base URL, and optionally OpenAPI spec path and auth token
   - Click "Save"

2. **Load OpenAPI Specification**:
   - Select a configuration
   - Click "Load OpenAPI"
   - Enter the path to your OpenAPI specification file
   - Click "Load"

3. **Configure API**:
   - Enter the base URL in the Configuration panel
   - Click "Update"
   - Optionally set an authentication token

4. **Make Requests**:
   - Select an endpoint from the list
   - Choose HTTP method from the dropdown
   - Fill in parameters in the form
   - For POST/PUT requests, enter JSON body (or use "Generate Example")
   - Click "Send Request"

5. **View Responses**:
   - Responses appear in the right panel
   - Status codes are color-coded (green for success, red/orange for errors)
   - JSON is automatically formatted
   - Use "Copy Response" to copy to clipboard

## Architecture

### Backend (Flask)
- `app.py`: Flask server that provides REST API endpoints
- Uses Essentials components for all API operations
- Serves static files (HTML, CSS, JavaScript)

### Frontend (Web)
- `static/index.html`: Main HTML structure
- `static/styles.css`: Modern dark theme styling
- `static/app.js`: Frontend logic and API communication

## API Endpoints

The Flask server provides the following REST API endpoints:

- `GET /api/configs` - Get all configurations
- `POST /api/configs` - Add a new configuration
- `DELETE /api/configs/<name>` - Remove a configuration
- `GET /api/configs/<name>` - Get a specific configuration
- `POST /api/configs/<name>/openapi` - Load OpenAPI spec
- `GET /api/configs/<name>/endpoints` - Get endpoints
- `POST /api/configs/<name>/request` - Make an API request
- `POST /api/configs/<name>/tasks` - Execute autonomous tasks

## Advantages

- **No GUI Library Dependencies**: Uses standard web technologies
- **Cross-Platform**: Works on any platform with a web browser
- **Modern UI**: Beautiful, responsive design
- **Easy to Customize**: Standard HTML/CSS/JavaScript
- **Accessible**: Can be accessed remotely if needed
- **No Menu Limits**: Web-based, no Tkinter menu constraints

## Requirements

- Python 3.7+
- Flask >= 2.3.0
- Flask-CORS >= 4.0.0
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Customization

### Changing the Port

Edit `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

### Changing the Theme

Edit `static/styles.css` and modify the CSS variables in `:root`:
```css
:root {
    --bg-primary: #1a1a1a;
    --accent-primary: #4a9eff;
    /* ... */
}
```

### Adding Features

The frontend is standard JavaScript - you can easily add new features by:
1. Adding HTML elements in `index.html`
2. Styling them in `styles.css`
3. Adding logic in `app.js`
4. Creating new API endpoints in `app.py` if needed

## Troubleshooting

### Server won't start
- Check if port 5000 is already in use
- Make sure Flask is installed: `pip install flask flask-cors`
- Check Python version (3.7+ required)

### Can't connect to server
- Make sure the server is running
- Check the URL: `http://localhost:5000`
- Check browser console for errors

### Endpoints not loading
- Verify the OpenAPI spec path is correct
- Check server logs for errors
- Ensure the OpenAPI file is valid

## License

This component is part of the AWS Data Loader project and is provided as-is for use in REST API testing and data loading scenarios.

