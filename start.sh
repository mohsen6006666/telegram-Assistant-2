#!/bin/bash

# Kill any existing Python processes
echo "Stopping any existing processes..."
pkill -f python || true
sleep 2

# Start the standalone bot
echo "Starting standalone Telegram Bot..."

# Run the standalone bot script
python standalone_bot.py
