#!/usr/bin/env python3
"""
Simple application runner that bypasses gunicorn dependency issues
and runs the Flask app directly with proper environment setup
"""
import os
import sys
import subprocess

def setup_environment():
    """Setup the Python environment and paths"""
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Try to activate virtual environment
    venv_python = os.path.join(current_dir, '.pythonlibs', 'bin', 'python')
    if os.path.exists(venv_python):
        print(f"Using virtual environment: {venv_python}")
        return venv_python
    else:
        print("Using system Python")
        return sys.executable

def run_app():
    """Run the Flask application"""
    python_exec = setup_environment()
    
    # Set environment variables for Flask
    env = os.environ.copy()
    env['FLASK_APP'] = 'main.py'
    env['FLASK_ENV'] = 'development'
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # Run the main application
    try:
        print("Starting Kotak Neo Trading Platform...")
        subprocess.run([python_exec, 'main.py'], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Application failed to start: {e}")
        return False
    except FileNotFoundError:
        print("Python executable not found")
        return False
    
    return True

if __name__ == '__main__':
    success = run_app()
    if not success:
        sys.exit(1)