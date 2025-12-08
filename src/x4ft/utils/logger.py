"""Centralized logging system for X4FT application.

Provides consistent logging across all modules with:
- Rotating log files (by size)
- Separate logs for different components
- Configurable log levels
- Consistent formatting
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class X4FTLogger:
    """Centralized logger for X4FT application."""

    # Singleton instance
    _instance: Optional['X4FTLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger system (only once)."""
        if self._initialized:
            return

        self._initialized = True
        self.logs_dir = Path.cwd() / 'logs'
        self.logs_dir.mkdir(exist_ok=True)

        # Configure root logger
        self.root_logger = logging.getLogger('x4ft')
        self.root_logger.setLevel(logging.DEBUG)
        self.root_logger.propagate = False

        # Remove existing handlers to avoid duplicates
        self.root_logger.handlers.clear()

        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup default handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup default log handlers."""
        # Main application log (rotating, max 10MB, keep 5 backups)
        main_log = self.logs_dir / 'x4ft.log'
        main_handler = RotatingFileHandler(
            main_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(self.detailed_formatter)
        self.root_logger.addHandler(main_handler)

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.simple_formatter)
        self.root_logger.addHandler(console_handler)

        # Error log (only errors and critical)
        error_log = self.logs_dir / 'errors.log'
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        self.root_logger.addHandler(error_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module.

        Args:
            name: Module name (e.g., 'extraction', 'parsers.ships', 'database')

        Returns:
            Logger instance for the module
        """
        # Ensure it's under x4ft namespace
        if not name.startswith('x4ft.'):
            name = f'x4ft.{name}'

        return logging.getLogger(name)

    def add_component_log(
        self,
        component: str,
        level: int = logging.DEBUG,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 3
    ) -> logging.Logger:
        """Add a separate log file for a specific component.

        Args:
            component: Component name (e.g., 'extraction', 'database', 'api')
            level: Minimum log level for this component
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep

        Returns:
            Logger instance for the component
        """
        logger_name = f'x4ft.{component}'
        logger = logging.getLogger(logger_name)

        # Check if handler already exists
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                return logger

        # Create component-specific log file
        log_file = self.logs_dir / f'{component}.log'
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(self.detailed_formatter)

        logger.addHandler(handler)
        logger.setLevel(level)

        return logger

    def set_console_level(self, level: int):
        """Change console output level.

        Args:
            level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(level)

    def cleanup_old_logs(self, days: int = 30):
        """Remove log files older than specified days.

        Args:
            days: Remove logs older than this many days
        """
        import time
        cutoff_time = time.time() - (days * 86400)

        for log_file in self.logs_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                self.root_logger.info(f"Removed old log file: {log_file.name}")


# Global instance
_logger_instance = X4FTLogger()


def get_logger(name: str = 'x4ft') -> logging.Logger:
    """Get a logger instance.

    Convenience function for getting loggers throughout the application.

    Args:
        name: Module/component name

    Returns:
        Logger instance

    Example:
        >>> from x4ft.utils.logger import get_logger
        >>> logger = get_logger('extraction.ships')
        >>> logger.info("Processing ship data...")
    """
    return _logger_instance.get_logger(name)


def setup_component_log(component: str, **kwargs) -> logging.Logger:
    """Setup a component-specific log file.

    Args:
        component: Component name
        **kwargs: Additional arguments for add_component_log

    Returns:
        Logger instance for the component
    """
    return _logger_instance.add_component_log(component, **kwargs)


def set_console_level(level: int):
    """Set console logging level.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    _logger_instance.set_console_level(level)


def cleanup_old_logs(days: int = 30):
    """Cleanup old log files.

    Args:
        days: Remove logs older than this many days
    """
    _logger_instance.cleanup_old_logs(days)
