"""
Test script for making requests to the mock API server.
This script demonstrates how to use the Essentials API client.
"""

import sys
import os
import json
from pathlib import Path

# Add the Essentials directory to the path
essentials_path = Path(__file__).parent.parent / "Essentials"
sys.path.insert(0, str(essentials_path))

from api_client import APIClient
from openapi_parser import OpenAPIParser
from api_config_manager import APIConfigManager
from autonomous_loader import AutonomousLoader


def test_basic_requests():
    """Test basic API requests."""
    print("=" * 60)
    print("Testing Basic API Requests")
    print("=" * 60)
    
    client = APIClient("http://localhost:8000")
    
    # Test health check
    print("\n1. Health Check:")
    response = client.get("/api/health")
    print(f"   Status: {response['status_code']}")
    print(f"   Response: {json.dumps(response['json'], indent=2)}")
    
    # Test GET users
    print("\n2. Get Users:")
    response = client.get("/api/users", params={"limit": 5})
    print(f"   Status: {response['status_code']}")
    print(f"   Users found: {len(response['json'].get('data', []))}")
    
    # Test GET user by ID
    print("\n3. Get User by ID:")
    response = client.get("/api/users/1")
    print(f"   Status: {response['status_code']}")
    if response['status_code'] == 200:
        print(f"   User: {response['json']['data']['name']}")
    
    # Test POST user
    print("\n4. Create User:")
    new_user = {
        "name": "Python Test User",
        "email": "python@test.com",
        "age": 25
    }
    response = client.post("/api/users", body=json.dumps(new_user))
    print(f"   Status: {response['status_code']}")
    if response['status_code'] == 201:
        print(f"   Created user ID: {response['json']['data']['id']}")
    
    # Test PUT user
    print("\n5. Update User:")
    update_data = {
        "name": "Updated Test User",
        "age": 26
    }
    response = client.put("/api/users/1", body=json.dumps(update_data))
    print(f"   Status: {response['status_code']}")
    if response['status_code'] == 200:
        print(f"   Updated user: {response['json']['data']['name']}")
    
    # Test GET posts
    print("\n6. Get Posts:")
    response = client.get("/api/posts")
    print(f"   Status: {response['status_code']}")
    print(f"   Posts found: {len(response['json'].get('data', []))}")
    
    print("\n" + "=" * 60)
    print("Basic Requests Test Complete!")
    print("=" * 60)


def test_openapi_parser():
    """Test OpenAPI parser."""
    print("\n" + "=" * 60)
    print("Testing OpenAPI Parser")
    print("=" * 60)
    
    spec_path = Path(__file__).parent / "mock_openapi.yaml"
    
    parser = OpenAPIParser()
    spec = parser.parse(str(spec_path))
    endpoints = parser.get_endpoints()
    
    print(f"\nParsed OpenAPI spec: {spec_path}")
    print(f"OpenAPI version: {spec.get('openapi', 'N/A')}")
    print(f"API title: {spec.get('info', {}).get('title', 'N/A')}")
    print(f"\nFound {len(endpoints)} endpoints:")
    
    for path, methods in endpoints.items():
        print(f"  {path}: {list(methods.keys())}")
    
    print("\n" + "=" * 60)
    print("OpenAPI Parser Test Complete!")
    print("=" * 60)


def test_config_manager():
    """Test API configuration manager."""
    print("\n" + "=" * 60)
    print("Testing API Configuration Manager")
    print("=" * 60)
    
    config_path = Path(__file__).parent / "test_config.json"
    spec_path = Path(__file__).parent / "mock_openapi.yaml"
    
    manager = APIConfigManager(config_file=str(config_path))
    
    # Add or update mock API config
    print("\n1. Adding Mock API configuration...")
    config = manager.add_config(
        name="Mock API",
        base_url="http://localhost:8000",
        openapi_spec_path=str(spec_path),
        auth_token=None
    )
    print(f"   Configuration added: {config.name}")
    
    # List all configs
    print("\n2. Listing all configurations:")
    configs = manager.list_configs()
    for cfg in configs:
        print(f"   - {cfg.name}: {cfg.base_url}")
    
    # Get active config
    print("\n3. Getting active configuration:")
    active = manager.get_active_config()
    if active:
        print(f"   Active: {active.name}")
    
    # Make request using config
    print("\n4. Making request using config:")
    response = active.api_client.get("/api/health")
    print(f"   Status: {response['status_code']}")
    
    print("\n" + "=" * 60)
    print("Config Manager Test Complete!")
    print("=" * 60)


def test_autonomous_loader():
    """Test autonomous loader."""
    print("\n" + "=" * 60)
    print("Testing Autonomous Loader")
    print("=" * 60)
    
    config_path = Path(__file__).parent / "test_config.json"
    tasks_path = Path(__file__).parent / "test_tasks.json"
    spec_path = Path(__file__).parent / "mock_openapi.yaml"
    
    # Setup config manager
    manager = APIConfigManager(config_file=str(config_path))
    manager.add_config(
        name="Mock API",
        base_url="http://localhost:8000",
        openapi_spec_path=str(spec_path),
        auth_token=None
    )
    
    # Setup loader with callbacks
    def on_progress(msg):
        print(f"   Progress: {msg}")
    
    def on_complete(tasks):
        print(f"\n   Completed {len(tasks)} tasks")
        successful = sum(1 for t in tasks if t.get('status_code', 0) < 400)
        print(f"   Successful: {successful}/{len(tasks)}")
    
    def on_error(task, error):
        print(f"   Error in task {task.get('path', 'unknown')}: {error}")
    
    loader = AutonomousLoader(
        config_manager=manager,
        on_progress=on_progress,
        on_complete=on_complete,
        on_error=on_error
    )
    
    # Load and execute tasks
    print("\n1. Loading tasks from file...")
    tasks = loader.load_tasks_from_file(str(tasks_path))
    print(f"   Loaded {len(tasks)} tasks")
    
    print("\n2. Executing tasks...")
    loader.add_tasks(tasks)
    loader.execute_all()
    
    print("\n" + "=" * 60)
    print("Autonomous Loader Test Complete!")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AWS Data Loader - Simulation Environment Tests")
    print("=" * 60)
    print("\nMake sure the mock server is running on http://localhost:8000")
    print("Start it with: python mock_server.py")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    try:
        # Test basic requests
        test_basic_requests()
        
        # Test OpenAPI parser
        test_openapi_parser()
        
        # Test config manager
        test_config_manager()
        
        # Test autonomous loader
        test_autonomous_loader()
        
        print("\n" + "=" * 60)
        print("All Tests Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

