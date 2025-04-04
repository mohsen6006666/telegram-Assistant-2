#!/usr/bin/env python3
"""
Simple run script for the Flask health check server
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
    """
    Custom run script that starts Gunicorn on port 5000
    """
    logger.info("Starting Flask server for health checks...")
    
    try:
        # Run Gunicorn with our app
        subprocess.run(
            ["gunicorn", "--bind", "0.0.0.0:5000", "--config", "gunicorn_config.py", "app:app"],
            check=True
        )
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()