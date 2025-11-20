"""
Flask backend server for the Web-based Advanced GUI.
Provides REST API endpoints that use the Essentials components.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path
import json
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename

# Add parent directory to path to import Essentials
sys.path.insert(0, str(Path(__file__).parent.parent / 'Essentials'))

from api_config_manager import APIConfigManager, APIConfig
from api_client import APIClient
from openapi_parser import OpenAPIParser
from autonomous_loader import AutonomousLoader, RequestTask

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for local development

# Global config manager
config_manager = APIConfigManager()


# ==================== File Upload ====================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file and return its path."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = Path(__file__).parent / 'uploads'
        uploads_dir.mkdir(exist_ok=True)
        
        # Save file with secure filename
        filename = secure_filename(file.filename)
        file_path = uploads_dir / filename
        
        # Handle duplicate filenames
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = uploads_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        file.save(str(file_path))
        
        # Return absolute path
        return jsonify({
            'success': True,
            'file_path': str(file_path.absolute()),
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Static File Serving ====================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


# ==================== Configuration Endpoints ====================

@app.route('/api/configs', methods=['GET'])
def get_configs():
    """Get all configurations."""
    try:
        configs = []
        for name in config_manager.get_config_names():
            try:
                config = config_manager.get_config(name)
                if config:
                    configs.append({
                        'name': config.name,
                        'base_url': config.base_url,
                        'openapi_spec_path': config.openapi_spec_path,
                        'has_auth_token': bool(config.auth_token)
                    })
            except Exception as e:
                print(f"Error loading config {name}: {e}")
                # Continue with other configs
                continue
        
        return jsonify({
            'configs': configs,
            'active_config': config_manager.active_config
        })
    except Exception as e:
        return jsonify({
            'configs': [],
            'active_config': None,
            'error': str(e)
        }), 500


@app.route('/api/configs', methods=['POST'])
def add_config():
    """Add a new configuration."""
    data = request.json
    try:
        config = config_manager.add_config(
            name=data['name'],
            base_url=data['base_url'],
            openapi_spec_path=data.get('openapi_spec_path'),
            auth_token=data.get('auth_token')
        )
        return jsonify({
            'success': True,
            'config': {
                'name': config.name,
                'base_url': config.base_url,
                'openapi_spec_path': config.openapi_spec_path
            }
        }), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/configs/<name>', methods=['DELETE'])
def remove_config(name):
    """Remove a configuration."""
    success = config_manager.remove_config(name)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Configuration not found'}), 404


@app.route('/api/configs/<name>/active', methods=['POST'])
def set_active_config(name):
    """Set active configuration."""
    config_manager.set_active_config(name)
    return jsonify({'success': True, 'active_config': name})


@app.route('/api/configs/<name>', methods=['GET'])
def get_config(name):
    """Get a specific configuration."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    return jsonify({
        'success': True,
        'name': config.name,
        'base_url': config.base_url,
        'openapi_spec_path': config.openapi_spec_path,
        'has_auth_token': bool(config.auth_token),
        'has_openapi_spec': config.openapi_spec is not None,
        'endpoint_count': len(config.endpoints) if config.endpoints else 0
    })


@app.route('/api/configs/<name>/auth', methods=['PUT'])
def update_auth_token(name):
    """Update authentication token for a configuration."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    data = request.json
    token = data.get('auth_token')
    config.set_auth_token(token)
    config_manager.save_configs()
    
    return jsonify({'success': True})


@app.route('/api/configs/<name>/url', methods=['PUT'])
def update_base_url(name):
    """Update base URL for a configuration."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    data = request.json
    base_url = data.get('base_url')
    config.base_url = base_url.rstrip('/')
    config._init_client()
    config_manager.save_configs()
    
    return jsonify({'success': True, 'base_url': config.base_url})


# ==================== OpenAPI Endpoints ====================

@app.route('/api/configs/<name>/openapi', methods=['POST'])
def load_openapi_spec(name):
    """Load OpenAPI specification for a configuration."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    data = request.json
    file_path = data.get('file_path')
    
    try:
        config.load_openapi_spec(file_path)
        config_manager.save_configs()
        
        return jsonify({
            'success': True,
            'endpoints': config.endpoints,
            'openapi_spec': config.openapi_spec
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/configs/<name>/endpoints', methods=['GET'])
def get_endpoints(name):
    """Get endpoints for a configuration."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    return jsonify({
        'success': True,
        'endpoints': config.endpoints,
        'openapi_spec': config.openapi_spec
    })


# ==================== API Request Endpoints ====================

@app.route('/api/configs/<name>/request', methods=['POST'])
def make_request(name):
    """Make an API request."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    if not config.api_client:
        return jsonify({'success': False, 'error': 'API client not initialized'}), 400
    
    data = request.json
    method = data.get('method', 'GET').upper()
    path = data.get('path', '')
    params = data.get('params', {})
    headers = data.get('headers', {})
    body = data.get('body')
    
    try:
        # Make the request
        if method == 'GET':
            response = config.api_client.get(path, params=params, headers=headers)
        elif method == 'POST':
            response = config.api_client.post(path, params=params, headers=headers, body=body)
        elif method == 'PUT':
            response = config.api_client.put(path, params=params, headers=headers, body=body)
        elif method == 'PATCH':
            response = config.api_client.patch(path, params=params, headers=headers, body=body)
        elif method == 'DELETE':
            response = config.api_client.delete(path, params=params, headers=headers)
        else:
            return jsonify({'success': False, 'error': f'Unsupported method: {method}'}), 400
        
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': None
        }), 500


# ==================== Autonomous Loader Endpoints ====================

@app.route('/api/configs/<name>/tasks', methods=['POST'])
def execute_tasks(name):
    """Execute autonomous tasks."""
    config = config_manager.get_config(name)
    if not config:
        return jsonify({'success': False, 'error': 'Configuration not found'}), 404
    
    data = request.json
    tasks_data = data.get('tasks', [])
    
    # Convert to RequestTask objects
    tasks = []
    for task_data in tasks_data:
        task = RequestTask(
            config_name=task_data.get('config_name', name),
            method=task_data.get('method', 'GET'),
            path=task_data.get('path', ''),
            params=task_data.get('params', {}),
            headers=task_data.get('headers', {}),
            body=task_data.get('body'),
            delay_before=task_data.get('delay_before', 0),
            delay_after=task_data.get('delay_after', 0)
        )
        tasks.append(task)
    
    # Execute tasks
    results = []
    for task in tasks:
        try:
            if task.config_name != name:
                task_config = config_manager.get_config(task.config_name)
                if not task_config:
                    results.append({
                        'task': task.to_dict(),
                        'success': False,
                        'error': f'Configuration {task.config_name} not found'
                    })
                    continue
                client = task_config.api_client
            else:
                client = config.api_client
            
            # Make request
            if task.method == 'GET':
                response = client.get(task.path, params=task.params, headers=task.headers)
            elif task.method == 'POST':
                response = client.post(task.path, params=task.params, headers=task.headers, body=task.body)
            elif task.method == 'PUT':
                response = client.put(task.path, params=task.params, headers=task.headers, body=task.body)
            elif task.method == 'PATCH':
                response = client.patch(task.path, params=task.params, headers=task.headers, body=task.body)
            elif task.method == 'DELETE':
                response = client.delete(task.path, params=task.params, headers=task.headers)
            else:
                results.append({
                    'task': task.to_dict(),
                    'success': False,
                    'error': f'Unsupported method: {task.method}'
                })
                continue
            
            results.append({
                'task': task.to_dict(),
                'success': response.get('status_code', 0) < 400,
                'response': response
            })
        except Exception as e:
            results.append({
                'task': task.to_dict(),
                'success': False,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'results': results,
        'total': len(results),
        'successful': sum(1 for r in results if r.get('success', False))
    })


if __name__ == '__main__':
    print("=" * 60)
    print("REST Data Loader - Web GUI Server")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("Open your browser and navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

