"""
Command-line interface for the Essentials REST Data Loader.
Provides a simple CLI for making API requests and executing autonomous tasks.
"""

import argparse
import json
import sys
from pathlib import Path
from api_client import APIClient
from api_config_manager import APIConfigManager
from autonomous_loader import AutonomousLoader, RequestTask
from openapi_parser import OpenAPIParser


def print_response(response: dict):
    """Print formatted response."""
    print(f"\nStatus: {response.get('status_code')}")
    print(f"URL: {response.get('url')}")
    print(f"Method: {response.get('method')}")
    print("\nResponse Body:")
    if response.get('json'):
        print(json.dumps(response['json'], indent=2))
    else:
        print(response.get('body', ''))


def cmd_make_request(args):
    """Make a single API request."""
    client = APIClient(args.base_url, timeout=args.timeout)
    
    if args.token:
        client.set_auth_token(args.token)
    
    # Load body from file if provided
    body = None
    if args.body_file:
        with open(args.body_file, 'r', encoding='utf-8') as f:
            body = f.read()
    elif args.body:
        body = args.body
    
    try:
        response = client.make_request(
            method=args.method,
            path=args.path,
            params=json.loads(args.params) if args.params else None,
            headers=json.loads(args.headers) if args.headers else None,
            body=body
        )
        print_response(response)
        sys.exit(0 if 200 <= response['status_code'] < 300 else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_parse_openapi(args):
    """Parse and display OpenAPI specification."""
    parser = OpenAPIParser()
    try:
        spec = parser.parse(args.file)
        endpoints = parser.get_endpoints()
        
        print(f"\nOpenAPI Specification: {args.file}")
        print(f"Version: {spec.get('openapi') or spec.get('swagger', 'Unknown')}")
        print(f"Title: {spec.get('info', {}).get('title', 'N/A')}")
        print(f"Endpoints found: {len(endpoints)}\n")
        
        for path, methods in endpoints.items():
            print(f"  {path}")
            for method, details in methods.items():
                summary = details.get('summary', '')
                print(f"    {method:6} - {summary}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({
                    'spec': spec,
                    'endpoints': endpoints
                }, f, indent=2, ensure_ascii=False)
            print(f"\nOutput saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_execute_tasks(args):
    """Execute autonomous tasks from a file."""
    config_manager = APIConfigManager(args.config_file)
    
    def on_progress(message):
        print(message)
    
    def on_complete(tasks):
        success_count = sum(1 for t in tasks if t.result and not t.error)
        print(f"\n=== Execution Complete ===")
        print(f"Total tasks: {len(tasks)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(tasks) - success_count}")
    
    def on_error(task, error):
        print(f"ERROR: {task.config_name} - {task.method} {task.path}: {error}")
    
    loader = AutonomousLoader(
        config_manager=config_manager,
        on_progress=on_progress,
        on_complete=on_complete,
        on_error=on_error
    )
    
    try:
        tasks = loader.load_tasks_from_file(args.tasks_file)
        loader.add_tasks(tasks)
        print(f"Loaded {len(tasks)} task(s)\n")
        
        loader.execute_all(stop_on_error=args.stop_on_error)
        
        if args.output:
            loader.save_results(args.output)
            print(f"\nResults saved to: {args.output}")
        
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_manage_config(args):
    """Manage API configurations."""
    config_manager = APIConfigManager(args.config_file)
    
    if args.action == 'list':
        configs = config_manager.get_all_configs()
        if not configs:
            print("No configurations found.")
            return
        
        print("\nAPI Configurations:")
        for config in configs:
            active = " (active)" if config.name == config_manager.active_config else ""
            print(f"  {config.name}{active}")
            print(f"    URL: {config.base_url}")
            print(f"    Spec: {config.openapi_spec_path or 'None'}")
            print()
    
    elif args.action == 'add':
        try:
            config_manager.add_config(
                name=args.name,
                base_url=args.base_url,
                openapi_spec_path=args.spec_file,
                auth_token=args.token
            )
            print(f"Configuration '{args.name}' added successfully.")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == 'remove':
        if config_manager.remove_config(args.name):
            print(f"Configuration '{args.name}' removed successfully.")
        else:
            print(f"Configuration '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == 'set-active':
        if config_manager.set_active_config(args.name):
            print(f"Configuration '{args.name}' set as active.")
        else:
            print(f"Configuration '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='REST Data Loader - Essentials (CLI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Make a GET request
  python cli.py request GET /api/users --base-url http://localhost:8000

  # Make a POST request with JSON body
  python cli.py request POST /api/users --base-url http://localhost:8000 --body '{"name":"John"}'

  # Parse OpenAPI spec
  python cli.py parse-openapi spec.yaml

  # Execute tasks
  python cli.py execute-tasks tasks.json

  # Manage configurations
  python cli.py config list
  python cli.py config add --name api1 --base-url http://localhost:8000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Request command
    req_parser = subparsers.add_parser('request', help='Make an API request')
    req_parser.add_argument('method', choices=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], help='HTTP method')
    req_parser.add_argument('path', help='API endpoint path')
    req_parser.add_argument('--base-url', required=True, help='Base URL for the API')
    req_parser.add_argument('--token', help='Authentication token')
    req_parser.add_argument('--params', help='Query parameters as JSON string')
    req_parser.add_argument('--headers', help='Additional headers as JSON string')
    req_parser.add_argument('--body', help='Request body (JSON string)')
    req_parser.add_argument('--body-file', help='Path to file containing request body')
    req_parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    
    # Parse OpenAPI command
    parse_parser = subparsers.add_parser('parse-openapi', help='Parse OpenAPI specification')
    parse_parser.add_argument('file', help='Path to OpenAPI spec file')
    parse_parser.add_argument('--output', help='Output file for parsed data (JSON)')
    
    # Execute tasks command
    tasks_parser = subparsers.add_parser('execute-tasks', help='Execute autonomous tasks')
    tasks_parser.add_argument('tasks_file', help='Path to tasks JSON file')
    tasks_parser.add_argument('--config-file', default='api_configs.json', help='Path to config file')
    tasks_parser.add_argument('--output', help='Output file for results')
    tasks_parser.add_argument('--stop-on-error', action='store_true', help='Stop on first error')
    
    # Config management command
    config_parser = subparsers.add_parser('config', help='Manage API configurations')
    config_parser.add_argument('action', choices=['list', 'add', 'remove', 'set-active'], help='Action to perform')
    config_parser.add_argument('--name', help='Configuration name (required for add/remove/set-active)')
    config_parser.add_argument('--base-url', help='Base URL (required for add)')
    config_parser.add_argument('--spec-file', help='Path to OpenAPI spec file (optional for add)')
    config_parser.add_argument('--token', help='Authentication token (optional for add)')
    config_parser.add_argument('--config-file', default='api_configs.json', help='Path to config file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'request':
        cmd_make_request(args)
    elif args.command == 'parse-openapi':
        cmd_parse_openapi(args)
    elif args.command == 'execute-tasks':
        cmd_execute_tasks(args)
    elif args.command == 'config':
        cmd_manage_config(args)


if __name__ == '__main__':
    main()

