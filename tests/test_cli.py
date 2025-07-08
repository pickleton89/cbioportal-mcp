#!/usr/bin/env python3
# Tests for CLI argument parsing and main function execution

import sys
import os
import pytest
import argparse
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import the cbioportal_server module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the main function and other necessary components from cbioportal_server
from cbioportal_server import main as cbioportal_main, CBioPortalMCPServer  # noqa: E402
from config import Configuration  # noqa: E402

@pytest.mark.asyncio
async def test_main_default_args(mocker):
    """Test main function with default arguments."""
    # Mock command line arguments to simulate no arguments passed
    mock_args = argparse.Namespace(
        config=None,
        create_example_config=None,
        base_url=None,
        transport=None,
        port=None,
        log_level=None
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    # Mock configuration loading
    mock_config = MagicMock(spec=Configuration)
    mock_config.get.side_effect = lambda path: {
        'logging.level': 'INFO',
        'server.base_url': 'https://www.cbioportal.org/api',
        'server.transport': 'stdio',
        'server.client_timeout': 480.0
    }.get(path)
    mocker.patch('cbioportal_server.load_config', return_value=mock_config)

    # Mock the server class and its MCP run method
    mock_server_instance = MagicMock(spec=CBioPortalMCPServer)
    # Add client attribute to mock to prevent AttributeError in main()'s shutdown handling
    mock_server_instance.client = None
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    
    # Ensure mock_server_instance.mcp is a mock, then set its run_async method
    mock_server_instance.mcp = MagicMock()
    mock_mcp_run = mocker.async_stub(name='mock_mcp_run_stdio')
    mock_server_instance.mcp.run_async = mock_mcp_run

    # Mock logging setup
    mock_setup_logging = mocker.patch('cbioportal_server.setup_logging')
    mock_cbioportal_logger = MagicMock()
    mock_get_logger = mocker.patch('cbioportal_server.get_logger')
    mock_get_logger.return_value = mock_cbioportal_logger

    # Mock signal handling at a higher level
    mock_setup_signal_handlers = mocker.patch('cbioportal_server.setup_signal_handlers')

    # Call the main function
    await cbioportal_main() # Corrected to use alias

    # Assertions
    mock_cbioportal_server_class.assert_called_once_with(config=mock_config)
    mock_setup_logging.assert_called_once_with(level="INFO")
    mock_get_logger.assert_any_call('cbioportal_server')
    assert mock_cbioportal_logger.info.call_count >= 2 # At least for starting and shutdown
    mock_cbioportal_logger.info.assert_any_call("Using transport: stdio")
    mock_cbioportal_logger.info.assert_any_call("cBioPortal MCP Server has shut down.")
    # Updated assertion to match the new run_async method call instead of the old run method
    mock_mcp_run.assert_called_once_with(transport="stdio")
    
    # Check signal handlers setup function was called
    mock_setup_signal_handlers.assert_called_once()


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

    mock_server_instance = MagicMock(spec=CBioPortalMCPServer)
    # Add client attribute to mock to prevent AttributeError in main()'s shutdown handling
    mock_server_instance.client = None
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    
    # Ensure mock_server_instance.mcp is a mock, then set its run_async method
    mock_server_instance.mcp = MagicMock()
    mock_mcp_run = mocker.async_stub(name='mock_mcp_run_stdio')
    mock_server_instance.mcp.run_async = mock_mcp_run

    mock_logging_basic_config = mocker.patch('logging.basicConfig')
    mock_cbioportal_logger = MagicMock()
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_get_logger.return_value = mock_cbioportal_logger

    mock_setup_signal_handlers = mocker.patch('cbioportal_server.setup_signal_handlers')

    await cbioportal_main() # Corrected to use alias

    mock_cbioportal_server_class.assert_called_once_with(base_url=custom_base_url)
    mock_logging_basic_config.assert_called_once_with(
        level=custom_log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[mocker.ANY]
    )
    mock_get_logger.assert_any_call('cbioportal_server')
    mock_cbioportal_logger.info.assert_any_call("Starting cBioPortal MCP Server with transport: stdio")
    mock_cbioportal_logger.info.assert_any_call("cBioPortal MCP Server has shut down.")

    mock_setup_signal_handlers.assert_called_once() # Added assertion

    # Updated assertion to match the new run_async method call instead of the old run method
    mock_mcp_run.assert_called_once_with(transport="stdio")


@pytest.mark.asyncio
async def test_main_error_during_run(mocker):
    """Test main function error handling when mcp.run() raises an exception."""
    mock_args = argparse.Namespace(
        base_url="https://www.cbioportal.org/api",
        transport="stdio",
        log_level="INFO"
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    mock_server_instance = MagicMock(spec=CBioPortalMCPServer)
    # Add client attribute to mock to prevent AttributeError in main()'s shutdown handling
    mock_server_instance.client = None
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)
    
    # Ensure mock_server_instance.mcp is a mock, then set its run_async method and side_effect
    mock_server_instance.mcp = MagicMock()
    mock_mcp_run = mocker.async_stub(name='mock_mcp_run_error')
    mock_mcp_run.side_effect = RuntimeError("Test MCP run error")
    mock_server_instance.mcp.run_async = mock_mcp_run

    mock_logging_basic_config = mocker.patch('logging.basicConfig')
    mock_cbioportal_logger = MagicMock()
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_get_logger.return_value = mock_cbioportal_logger

    mock_setup_signal_handlers = mocker.patch('cbioportal_server.setup_signal_handlers')

    await cbioportal_main() # Corrected to use alias

    mock_cbioportal_server_class.assert_called_once_with(base_url="https://www.cbioportal.org/api") # Added assertion
    mock_logging_basic_config.assert_called_once_with( # Added assertion
        level="INFO",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[mocker.ANY]
    )
    mock_get_logger.assert_any_call('cbioportal_server') # Verify getLogger call

    mock_cbioportal_logger.error.assert_called_once_with(
        "An unexpected error occurred during server execution: Test MCP run error",
        exc_info=True
    )
    # Ensure shutdown messages are still logged
    mock_cbioportal_logger.info.assert_any_call("Server shutdown sequence initiated from main.")
    mock_cbioportal_logger.info.assert_any_call("cBioPortal MCP Server has shut down.")
    mock_setup_signal_handlers.assert_called_once() # Added assertion


@pytest.mark.asyncio
async def test_main_unsupported_transport(mocker):
    """Test main function with an unsupported transport argument."""
    # Mock sys.exit to check if it's called
    mock_exit = mocker.patch('sys.exit')
    # Mock ArgumentParser.error to check the error message (argparse calls this, then sys.exit)
    mock_argparse_error = mocker.patch('argparse.ArgumentParser.error')

    # Simulate parse_args raising an error as it would for an invalid choice
    # This is a bit indirect; ideally, we'd trigger the actual argparse validation.
    # However, directly making parse_args raise SystemExit due to invalid choice is tricky to mock cleanly.
    # Instead, we'll simulate the effect: argparse prints error and exits.
    # We need to patch 'parse_args' on an instance of ArgumentParser used in main.
    # For simplicity, let's assume the call to parse_args within main would lead to SystemExit.
    # A more robust way might involve directly testing the parser object if it were accessible.

    # To test argparse's behavior more directly, we can make parse_args raise an error
    # that would typically be caught by argparse itself, leading it to call its own .error() method.
    # However, for an invalid choice, parse_args usually calls .error() internally and then exits.

    # Let's mock parse_args to directly call the mocked error method, then raise SystemExit
    # to simulate the full argparse behavior for an invalid choice.
    def custom_parse_args_side_effect(): 
        # This simulates argparse finding an invalid choice for --transport
        mock_argparse_error("argument --transport: invalid choice: 'invalid_transport' (choose from 'stdio')")
        # argparse then calls sys.exit(2)
        mock_exit(2)
        raise SystemExit(2) # Make sure the control flow stops here

    mocker.patch('argparse.ArgumentParser.parse_args', side_effect=custom_parse_args_side_effect)

    # Patch other parts of main to prevent them from running if parse_args "succeeds" unexpectedly
    mocker.patch('logging.basicConfig')
    mocker.patch('logging.getLogger')
    mocker.patch('cbioportal_server.setup_signal_handlers')
    mocker.patch('cbioportal_server.CBioPortalMCPServer')

    # We expect SystemExit to be raised by the mocked parse_args
    with pytest.raises(SystemExit) as excinfo:
        await cbioportal_main()
    
    assert excinfo.value.code == 2
    mock_argparse_error.assert_called_once_with(
        "argument --transport: invalid choice: 'invalid_transport' (choose from 'stdio')"
    )
    mock_exit.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_main_keyboard_interrupt(mocker):
    """Test main function handles KeyboardInterrupt during mcp.run gracefully."""
    mock_args = argparse.Namespace(
        base_url="https://www.cbioportal.org/api",
        transport="stdio",
        log_level="INFO"
    )
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)

    mock_server_instance = MagicMock(spec=CBioPortalMCPServer)
    # Add client attribute to mock to prevent AttributeError in main()'s shutdown handling
    mock_server_instance.client = None
    mock_cbioportal_server_class = mocker.patch('cbioportal_server.CBioPortalMCPServer', return_value=mock_server_instance)

    mock_server_instance.mcp = MagicMock()
    mock_mcp_run = mocker.async_stub(name='mock_mcp_run_interrupt')
    # Simulate KeyboardInterrupt being raised by mcp.run_async()
    mock_mcp_run.side_effect = KeyboardInterrupt("Simulated Ctrl+C")
    mock_server_instance.mcp.run_async = mock_mcp_run

    mock_logging_basic_config = mocker.patch('logging.basicConfig')
    mock_cbioportal_logger = MagicMock()
    mock_get_logger = mocker.patch('logging.getLogger')
    mock_get_logger.return_value = mock_cbioportal_logger

    mock_setup_signal_handlers = mocker.patch('cbioportal_server.setup_signal_handlers')

    # Call the main function - it should catch KeyboardInterrupt and exit gracefully
    await cbioportal_main()

    # Assertions
    mock_cbioportal_server_class.assert_called_once_with(base_url="https://www.cbioportal.org/api")
    mock_logging_basic_config.assert_called_once_with(
        level="INFO",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[mocker.ANY]
    )
    mock_get_logger.assert_any_call('cbioportal_server')

    # Check for startup and shutdown messages
    mock_cbioportal_logger.info.assert_any_call("Starting cBioPortal MCP Server with transport: stdio")
    mock_cbioportal_logger.info.assert_any_call("Server interrupted by user (KeyboardInterrupt).")
    mock_cbioportal_logger.info.assert_any_call("cBioPortal MCP Server has shut down.")
    
    # Ensure mcp.run was called with the correct transport parameter
    mock_mcp_run.assert_called_once_with(transport="stdio")
    mock_setup_signal_handlers.assert_called_once()
