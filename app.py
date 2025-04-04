#!/usr/bin/env python3
"""
Simple Flask application for health checks
"""

from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    """Health check endpoint for UptimeRobot"""
    return jsonify({
        "status": "OK",
        "message": "Bot is running!"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)