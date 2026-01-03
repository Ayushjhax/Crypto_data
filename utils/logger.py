"""
Logging utility for the crypto data pipeline.

INTERVIEW EXPLANATION:
Why use logging instead of print()?
1. Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Control verbosity in production
   - Filter logs by severity
   
2. Structured Output: Timestamps, log levels, module names
   - Easier debugging
   - Better for production monitoring
   
3. Multiple Handlers: Console, file, external services
   - Can send logs to monitoring tools
   - Persistent log files for auditing
   
4. Performance: Can disable debug logs in production
   - print() always executes
   - logging can be filtered at runtime
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    INTERVIEW EXPLANATION:
    This is a factory function pattern - creates and configures loggers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional file path for file logging
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate logs if logger already configured
    if logger.handlers:
        return logger
    
    # Console handler - shows logs in terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format: [TIMESTAMP] [LEVEL] [MODULE] - MESSAGE
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler - saves logs to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a default logger for the project
default_logger = setup_logger(
    "DonutAI",
    log_file="logs/donutai.log"
)

