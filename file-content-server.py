#!/usr/bin/env python3
"""
File Content Server for Dashboard
Provides file content for project drilldown functionality
"""

import os
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard

# Base path for projects
BASE_PATH = Path(__file__).parent.parent

@app.route('/', methods=['GET'])
def index():
    """Root endpoint to verify server is running"""
    return jsonify({
        'status': 'running',
        'service': 'File Content Server',
        'endpoints': [
            '/api/project/<project_id>/files - Get list of project files',
            '/api/project/<project_id>/file - Get file content (POST)',
            '/api/projects - Get all projects'
        ],
        'base_path': str(BASE_PATH)
    })

@app.route('/api/project/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """Get list of important files for a project"""
    try:
        # Find project path
        project_path = find_project_path(project_id)
        if not project_path:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get important files
        important_files = [
            'CLAUDE.md', 'TODO.md', 'README.md', 
            'package.json', 'requirements.txt',
            '.env.example', 'SECURITY.md'
        ]
        
        files = []
        for filename in important_files:
            filepath = project_path / filename
            if filepath.exists():
                stat = filepath.stat()
                files.append({
                    'name': filename,
                    'path': str(filepath.relative_to(BASE_PATH)),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type': get_file_type(filename),
                    'icon': get_file_icon(filename)
                })
        
        # Also add Python and JS files (limit to 10)
        for pattern in ['*.py', '*.js']:
            for filepath in list(project_path.glob(pattern))[:5]:
                if filepath.is_file():
                    stat = filepath.stat()
                    files.append({
                        'name': filepath.name,
                        'path': str(filepath.relative_to(BASE_PATH)),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'type': 'code',
                        'icon': '📝'
                    })
        
        return jsonify({'files': files})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project/<project_id>/file', methods=['POST'])
def get_file_content(project_id):
    """Get content of a specific file"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        # Find project path
        project_path = find_project_path(project_id)
        if not project_path:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get file path
        filepath = project_path / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is too large (limit to 1MB)
        if filepath.stat().st_size > 1024 * 1024:
            return jsonify({'error': 'File too large'}), 413
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return jsonify({'error': 'Binary file cannot be displayed'}), 415
        
        # Get file info
        stat = filepath.stat()
        mime_type, _ = mimetypes.guess_type(str(filepath))
        
        return jsonify({
            'filename': filename,
            'content': content,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'mime_type': mime_type or 'text/plain',
            'language': get_language(filename)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_all_projects():
    """Get list of all projects"""
    try:
        registry_file = BASE_PATH / 'project-registry.json'
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                registry = json.load(f)
                return jsonify(registry.get('projects', {}))
        return jsonify({})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def find_project_path(project_id):
    """Find the actual path for a project"""
    # Check in active, staging, and archive directories
    for base_dir in ['active', 'staging', 'archive']:
        project_path = BASE_PATH / base_dir / project_id
        if project_path.exists():
            return project_path
    
    # Check if it's a special project (like Project Management with space)
    if project_id == 'Project_Management':
        project_path = BASE_PATH / 'active' / 'Project Management'
        if project_path.exists():
            return project_path
    
    return None

def get_file_type(filename):
    """Determine file type from filename"""
    if filename.endswith('.md'):
        if 'CLAUDE' in filename:
            return 'context'
        elif 'TODO' in filename:
            return 'tasks'
        elif 'README' in filename:
            return 'documentation'
        return 'markdown'
    elif filename.endswith('.json'):
        return 'config'
    elif filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
        return 'code'
    elif filename.endswith(('.txt', '.log')):
        return 'text'
    return 'unknown'

def get_file_icon(filename):
    """Get emoji icon for file type"""
    if 'CLAUDE' in filename:
        return '🤖'
    elif 'TODO' in filename:
        return '📋'
    elif 'README' in filename:
        return '📖'
    elif 'SECURITY' in filename:
        return '🔒'
    elif filename.endswith('.json'):
        return '⚙️'
    elif filename.endswith('.py'):
        return '🐍'
    elif filename.endswith(('.js', '.ts', '.jsx', '.tsx')):
        return '📜'
    elif filename.endswith('.env'):
        return '🔐'
    return '📄'

def get_language(filename):
    """Get language for syntax highlighting"""
    ext = Path(filename).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.json': 'json',
        '.md': 'markdown',
        '.html': 'html',
        '.css': 'css',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.sh': 'bash',
        '.env': 'ini'
    }
    return language_map.get(ext, 'plaintext')

if __name__ == '__main__':
    print("🚀 File Content Server starting on http://localhost:5001")
    print("📁 Serving files from:", BASE_PATH)
    app.run(port=5001, debug=True)