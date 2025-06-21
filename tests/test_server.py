"""
Tests for the PyApple MCP server

Basic tests to verify the server can be imported and initialized.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock

# Only run tests on macOS
pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="PyApple MCP requires macOS")

def test_server_import():
    """Test that the server module can be imported."""
    try:
        from pyapple_mcp import server
        assert server is not None
    except ImportError as e:
        pytest.fail(f"Failed to import server module: {e}")

@patch('pyapple_mcp.utils.applescript.applescript.check_app_access')
def test_contacts_handler_init(mock_check_access):
    """Test that ContactsHandler can be initialized."""
    mock_check_access.return_value = True
    
    from pyapple_mcp.utils.contacts import ContactsHandler
    handler = ContactsHandler()
    assert handler.app_name == "Contacts"

@patch('pyapple_mcp.utils.applescript.applescript.check_app_access')
def test_notes_handler_init(mock_check_access):
    """Test that NotesHandler can be initialized."""
    mock_check_access.return_value = True
    
    from pyapple_mcp.utils.notes import NotesHandler
    handler = NotesHandler()
    assert handler.app_name == "Notes"

@patch('pyapple_mcp.utils.applescript.applescript.check_app_access')
def test_messages_handler_init(mock_check_access):
    """Test that MessagesHandler can be initialized.""" 
    mock_check_access.return_value = True
    
    from pyapple_mcp.utils.messages import MessagesHandler
    handler = MessagesHandler()
    assert handler.app_name == "Messages"

def test_websearch_handler_init():
    """Test that WebSearchHandler can be initialized."""
    from pyapple_mcp.utils.websearch import WebSearchHandler
    handler = WebSearchHandler()
    assert handler.base_url == "https://duckduckgo.com"

def test_applescript_runner_init():
    """Test that AppleScriptRunner can be initialized."""
    from pyapple_mcp.utils.applescript import AppleScriptRunner
    runner = AppleScriptRunner()
    assert runner.timeout == 30

@patch('subprocess.run')
def test_applescript_runner_basic_script(mock_run):
    """Test basic AppleScript execution."""
    # Mock successful subprocess execution
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "test result"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    
    from pyapple_mcp.utils.applescript import AppleScriptRunner
    runner = AppleScriptRunner()
    
    result = runner.run_script('return "hello"')
    assert result['success'] is True
    assert result['result'] == "test result"
    assert result['error'] is None

@patch('subprocess.run')
def test_applescript_runner_error_handling(mock_run):
    """Test AppleScript error handling."""
    # Mock failed subprocess execution
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "execution error"
    mock_run.return_value = mock_result
    
    from pyapple_mcp.utils.applescript import AppleScriptRunner
    runner = AppleScriptRunner()
    
    result = runner.run_script('invalid script')
    assert result['success'] is False
    assert result['result'] is None
    assert "execution error" in result['error'] 