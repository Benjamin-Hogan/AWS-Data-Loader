"""
Mock REST API Server for Testing
A simple Flask-based mock server that simulates a REST API for testing the data loader.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
from datetime import datetime
from typing import Dict, Any

app = Flask(__name__)
CORS(app)  # Enable CORS for testing

# In-memory data store
users_db = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
    {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35},
]

posts_db = [
    {"id": 1, "title": "First Post", "content": "This is the first post", "author_id": 1},
    {"id": 2, "title": "Second Post", "content": "This is the second post", "author_id": 2},
]

next_user_id = 4
next_post_id = 3


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mock-api-server"
    }), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with optional pagination."""
    limit = request.args.get('limit', type=int, default=10)
    offset = request.args.get('offset', type=int, default=0)
    search = request.args.get('search', type=str)
    
    filtered_users = users_db.copy()
    
    # Apply search filter if provided
    if search:
        filtered_users = [
            u for u in filtered_users
            if search.lower() in u.get('name', '').lower() or 
               search.lower() in u.get('email', '').lower()
        ]
    
    # Apply pagination
    paginated_users = filtered_users[offset:offset + limit]
    
    return jsonify({
        "data": paginated_users,
        "total": len(filtered_users),
        "limit": limit,
        "offset": offset,
        "count": len(paginated_users)
    }), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID."""
    user = next((u for u in users_db if u['id'] == user_id), None)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"data": user}), 200


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user."""
    global next_user_id
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        if 'name' not in data or 'email' not in data:
            return jsonify({"error": "Name and email are required"}), 400
        
        # Create new user
        new_user = {
            "id": next_user_id,
            "name": data.get('name'),
            "email": data.get('email'),
            "age": data.get('age'),
        }
        
        users_db.append(new_user)
        next_user_id += 1
        
        return jsonify({"data": new_user}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user."""
    user = next((u for u in users_db if u['id'] == user_id), None)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Update user fields
        user.update({k: v for k, v in data.items() if k != 'id'})
        
        return jsonify({"data": user}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    global users_db
    
    user = next((u for u in users_db if u['id'] == user_id), None)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    users_db = [u for u in users_db if u['id'] != user_id]
    
    return jsonify({"message": "User deleted successfully"}), 200


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get all posts with optional filtering."""
    author_id = request.args.get('author_id', type=int)
    limit = request.args.get('limit', type=int, default=10)
    offset = request.args.get('offset', type=int, default=0)
    
    filtered_posts = posts_db.copy()
    
    # Filter by author if provided
    if author_id:
        filtered_posts = [p for p in filtered_posts if p['author_id'] == author_id]
    
    # Apply pagination
    paginated_posts = filtered_posts[offset:offset + limit]
    
    return jsonify({
        "data": paginated_posts,
        "total": len(filtered_posts),
        "limit": limit,
        "offset": offset,
        "count": len(paginated_posts)
    }), 200


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post by ID."""
    post = next((p for p in posts_db if p['id'] == post_id), None)
    
    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    return jsonify({"data": post}), 200


@app.route('/api/posts', methods=['POST'])
def create_post():
    """Create a new post."""
    global next_post_id
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate required fields
        if 'title' not in data or 'content' not in data:
            return jsonify({"error": "Title and content are required"}), 400
        
        # Create new post
        new_post = {
            "id": next_post_id,
            "title": data.get('title'),
            "content": data.get('content'),
            "author_id": data.get('author_id', 1),
        }
        
        posts_db.append(new_post)
        next_post_id += 1
        
        return jsonify({"data": new_post}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/data', methods=['POST'])
def receive_data():
    """Generic data endpoint for testing POST requests."""
    try:
        data = request.get_json()
        
        return jsonify({
            "message": "Data received successfully",
            "received": data,
            "timestamp": datetime.now().isoformat()
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/slow', methods=['GET'])
def slow_endpoint():
    """Slow endpoint for testing timeouts and delays."""
    delay = request.args.get('delay', type=float, default=2.0)
    time.sleep(delay)
    
    return jsonify({
        "message": f"Response delayed by {delay} seconds",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/error/<int:status_code>', methods=['GET'])
def error_endpoint(status_code):
    """Endpoint that returns specific error status codes for testing."""
    error_messages = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    
    message = error_messages.get(status_code, "Unknown Error")
    
    return jsonify({
        "error": message,
        "status_code": status_code
    }), status_code


@app.route('/api/echo', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def echo():
    """Echo endpoint that returns request details."""
    return jsonify({
        "method": request.method,
        "headers": dict(request.headers),
        "args": dict(request.args),
        "json": request.get_json(),
        "form": dict(request.form),
        "timestamp": datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Mock REST API Server")
    print("=" * 60)
    print("Server starting on http://localhost:8000")
    print("\nAvailable endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/users")
    print("  GET  /api/users/<id>")
    print("  POST /api/users")
    print("  PUT  /api/users/<id>")
    print("  DELETE /api/users/<id>")
    print("  GET  /api/posts")
    print("  GET  /api/posts/<id>")
    print("  POST /api/posts")
    print("  POST /api/data")
    print("  GET  /api/slow?delay=<seconds>")
    print("  GET  /api/error/<status_code>")
    print("  *    /api/echo")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)

