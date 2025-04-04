"""
Custom workflow script for Replit
This script is used to start both the Flask server on port 8080 and the Telegram bot
"""

import os
import sys
import time
import signal
import subprocess
from threading import Thread

# Global process handles
flask_process = None
bot_process = None

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up processes"""
    print("Shutting down all processes...")
    
    if flask_process:
        flask_process.terminate()
        flask_process.wait()
    
    if bot_process:
        bot_process.terminate()
        bot_process.wait()
    
    sys.exit(0)

def start_flask_server():
    """Start the Flask server on port 8080 using Gunicorn"""
    global flask_process
    
    # Command to start Gunicorn on port 8080
    cmd = [
        "gunicorn",
        "-b", "0.0.0.0:8080",
        "-w", "1",
        "--reload",
        "main:app"
    ]
    
    # Start the process
    flask_process = subprocess.Popen(cmd)
    print("Flask server started on port 8080")
    
    # Wait for process to terminate (which it shouldn't unless there's an error)
    return_code = flask_process.wait()
    print(f"Flask server process terminated with code {return_code}")

def start_telegram_bot():
    """Start the Telegram bot directly using Python"""
    global bot_process
    
    # Command to start the Telegram bot
    cmd = ["python", "main.py"]
    
    # Start the process
    bot_process = subprocess.Popen(cmd)
    print("Telegram bot started")
    
    # Wait for process to terminate (which it shouldn't unless there's an error)
    return_code = bot_process.wait()
    print(f"Telegram bot process terminated with code {return_code}")

def main():
    """Main entry point for the workflow script"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask server in a separate thread
    flask_thread = Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Allow time for the Flask server to start
    time.sleep(2)
    
    # Start Telegram bot in the main thread
    start_telegram_bot()

if __name__ == "__main__":
    main()