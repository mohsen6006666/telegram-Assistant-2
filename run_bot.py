#!/usr/bin/env python3
"""
Simple launcher script for the standalone bot
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting standalone Telegram bot...")
    
    # Kill any existing Python processes first
    try:
        os.system("pkill -f 'python.*bot' || true")
        logger.info("Killed any existing bot processes")
    except Exception as e:
        logger.error(f"Error killing existing processes: {str(e)}")
    
    # Execute the standalone bot directly
    try:
        subprocess.run(
            [sys.executable, "standalone_bot.py"],
            check=True
        )
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()