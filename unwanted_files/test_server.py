#!/usr/bin/env python3
"""
Simple test server to verify external connectivity
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return f"Test server running on Replit domain: {os.environ.get('REPLIT_DOMAINS', 'Not found')}"

@app.route('/health')
def health():
    return {'status': 'ok', 'domain': os.environ.get('REPLIT_DOMAINS')}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)