"""
Logging utilities for the cBioPortal MCP server.

This module provides centralized logging configuration and utilities.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        handler: Custom logging handler (defaults to stderr)
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
    
    logging.basicConfig(
        level=level.upper(),
        format=format_string,
        handlers=[handler],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_api_request(logger: logging.Logger, endpoint: str, method: str = "GET") -> None:
    """
    Log an API request in a standardized format.
    
    Args:
        logger: Logger instance to use
        endpoint: API endpoint being requested
        method: HTTP method
    """
    logger.debug(f"API Request: {method} {endpoint}")


def log_api_response(
    logger: logging.Logger,
    endpoint: str,
    status_code: Optional[int] = None,
    result_count: Optional[int] = None,
) -> None:
    """
    Log an API response in a standardized format.
    
    Args:
        logger: Logger instance to use
        endpoint: API endpoint that was requested
        status_code: HTTP status code (if available)
        result_count: Number of results returned (if applicable)
    """
    parts = [f"API Response: {endpoint}"]
    if status_code is not None:
        parts.append(f"status={status_code}")
    if result_count is not None:
        parts.append(f"results={result_count}")
    
    logger.debug(" ".join(parts))


def log_pagination_info(
    logger: logging.Logger,
    page: int,
    page_size: int,
    total_found: int,
    has_more: bool,
) -> None:
    """
    Log pagination information in a standardized format.
    
    Args:
        logger: Logger instance to use
        page: Current page number
        page_size: Number of items per page
        total_found: Total items found
        has_more: Whether there are more pages available
    """
    logger.debug(
        f"Pagination: page={page}, size={page_size}, found={total_found}, has_more={has_more}"
    )


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str,
    **kwargs,
) -> None:
    """
    Log an error with additional context information.
    
    Args:
        logger: Logger instance to use
        error: Exception that occurred
        context: Context description (e.g., "fetching studies")
        **kwargs: Additional context key-value pairs
    """
    context_parts = [f"{k}={v}" for k, v in kwargs.items()]
    context_str = f" ({', '.join(context_parts)})" if context_parts else ""
    
    logger.error(f"Error {context}{context_str}: {str(error)}", exc_info=True)
