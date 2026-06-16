"""
Centralized logging configuration for the campaign engine.

All modules should use the logger from this module to ensure consistent logging.
"""

import logging
import sys
from typing import Optional


# Global logger instance
_logger: Optional[logging.Logger] = None


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Configure the global logger.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
        log_file: Optional file path to log to (in addition to console)
        format_string: Optional custom log format string
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Create logger
    _logger = logging.getLogger("warfare_simulation")
    _logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)
    
    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the campaign engine logger.
    
    Args:
        name: Optional name for the logger (e.g., __name__)
               If provided, returns a child logger
    
    Returns:
        Logger instance for use in modules
    
    Example:
        from warfare_simulation.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Kingdom initialized")
    """
    global _logger
    
    # Configure on first use
    if _logger is None:
        configure_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger
