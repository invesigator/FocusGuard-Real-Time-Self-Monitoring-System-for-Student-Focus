# utils/logging_setup.py
import logging
import sys

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('drowsiness_detection.log'),
            logging.StreamHandler(sys.stdout)
          ]
    )