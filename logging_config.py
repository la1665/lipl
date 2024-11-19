import logging
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class LevelFilter(logging.Filter):
    """A custom logging filter that only allows a specific log level."""
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno == self.level

def setup_logging():
    # Create the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to the lowest level to capture all messages

    # Remove any existing handlers
    logger.handlers = []

    # Define log message format with date and time
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Create a handler for each log level with a filter to capture only that level
    info_handler = logging.FileHandler("logs/info.log")
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(LevelFilter(logging.INFO))

    debug_handler = logging.FileHandler("logs/debug.log")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    debug_handler.addFilter(LevelFilter(logging.DEBUG))

    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(LevelFilter(logging.ERROR))

    critical_handler = logging.FileHandler("logs/critical.log")
    critical_handler.setLevel(logging.CRITICAL)
    critical_handler.setFormatter(formatter)
    critical_handler.addFilter(LevelFilter(logging.CRITICAL))

    # Add handlers to the root logger
    logger.addHandler(info_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)
    logger.addHandler(critical_handler)

# Initialize logging at the start of the application
setup_logging()
