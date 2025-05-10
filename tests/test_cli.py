#!/usr/bin/env python3
# Tests for CLI argument parsing and main function execution

import sys
import os
import pytest
import argparse
import signal
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import the cbioportal_server module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the main function and other necessary components from cbioportal_server
from cbioportal_server import main  # noqa: E402

@pytest.mark.asyncio
async def test_main_default_args(mocker):
    """Test main function with default arguments."""
    # Mock command line arguments to simulate no arguments passed
    mock_args = argparse.Namespace(
        base_url="https://www.cbioportal.org/api",
        transport="stdio",
        log_level="INFO"
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    # Mock the server class and its MCP run method
    mock_server_instance = MagicMock()
    mock_mcp_instance = MagicMock()
    mock_server_instance.mcp = mock_mcp_instance
    
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    mock_mcp_run = mocker.patch.object(mock_mcp_instance, 'run', new_callable=MagicMock) # Use new_callable for async mock if needed, but run isn't async itself
    mock_mcp_run.return_value = None # Simulate it runs and returns

    # Mock logging
    mock_logging_basic_config = mocker.patch('logging.basicConfig')
    mock_logger_info = mocker.patch('cbioportal_server.logger.info') # Patch logger instance used in cbioportal_server.py
    # We need to patch cbioportal_server.logger as it's reassigned after basicConfig

    # Mock signal handling
    mock_signal_signal = mocker.patch('signal.signal')

    # Call the main function
    await main()

    # Assertions
    mock_cbioportal_server_class.assert_called_once_with(base_url="https://www.cbioportal.org/api")
    mock_logging_basic_config.assert_called_once_with(
        level="INFO",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[mocker.ANY]  # Check for any StreamHandler instance
    )
    assert mock_logger_info.call_count >= 2 # At least for starting and shutdown
    mock_logger_info.assert_any_call("Starting cBioPortal MCP Server with transport: stdio")
    mock_logger_info.assert_any_call("cBioPortal MCP Server has shut down.")
    mock_mcp_run.assert_called_once_with(sys.stdin.buffer, sys.stdout.buffer)
    
    # Check signal handlers were set up
    assert mock_signal_signal.call_count == 2
    mock_signal_signal.assert_any_call(signal.SIGINT, mocker.ANY)
    mock_signal_signal.assert_any_call(signal.SIGTERM, mocker.ANY)


@pytest.mark.asyncio
async def test_main_custom_args(mocker):
    """Test main function with custom command-line arguments."""
    custom_base_url = "http://localhost:8888/api"
    custom_log_level = "DEBUG"

    mock_args = argparse.Namespace(
        base_url=custom_base_url,
        transport="stdio",  # Keep transport as stdio for now
        log_level=custom_log_level
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    mock_server_instance = MagicMock()
    mock_mcp_instance = MagicMock()
    mock_server_instance.mcp = mock_mcp_instance
    
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    mock_mcp_run = mocker.patch.object(mock_mcp_instance, 'run', new_callable=MagicMock)
    mock_mcp_run.return_value = None

    mock_logging_basic_config = mocker.patch('logging.basicConfig')
    mock_logger_info = mocker.patch('cbioportal_server.logger.info')

    mocker.patch('signal.signal') # No need to assert calls, just ensure it's patched

    await main()

    mock_cbioportal_server_class.assert_called_once_with(base_url=custom_base_url)
    mock_logging_basic_config.assert_called_once_with(
        level=custom_log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[mocker.ANY]
    )
    mock_logger_info.assert_any_call("Starting cBioPortal MCP Server with transport: stdio")
    mock_logger_info.assert_any_call("cBioPortal MCP Server has shut down.")
    # With DEBUG level, we might expect more .debug calls if any are present at startup
    # For now, we're not asserting specific debug calls, just that info is still called.

    mock_mcp_run.assert_called_once_with(sys.stdin.buffer, sys.stdout.buffer)


@pytest.mark.asyncio
async def test_main_error_during_run(mocker):
    """Test main function error handling when mcp.run() raises an exception."""
    mock_args = argparse.Namespace(
        base_url="https://www.cbioportal.org/api",
        transport="stdio",
        log_level="INFO"
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    mock_server_instance = MagicMock()
    mock_mcp_instance = MagicMock()
    mock_server_instance.mcp = mock_mcp_instance
    
    mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    
    # Simulate mcp.run() raising an exception
    _mock_mcp_run = mocker.patch.object(mock_mcp_instance, 'run', side_effect=RuntimeError("Test MCP run error"))

    mocker.patch('logging.basicConfig')
    mock_logger_info = mocker.patch('cbioportal_server.logger.info')
    mock_logger_error = mocker.patch('cbioportal_server.logger.error') # For checking ERROR level logs

    mocker.patch('signal.signal')

    await main()

    mock_logger_error.assert_called_once_with(
        "An unexpected error occurred during server execution: Test MCP run error",
        exc_info=True
    )
    # Ensure shutdown messages are still logged
    mock_logger_info.assert_any_call("Server shutdown sequence initiated from main.")
    mock_logger_info.assert_any_call("cBioPortal MCP Server has shut down.")


# # Basic test structure (to be expanded)
# # def test_example_cli():
# #     assert True
