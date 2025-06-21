"""
PyApple MCP - Apple-native tools for the Model Context Protocol

A Python implementation providing seamless integration with macOS applications
including Messages, Notes, Contacts, Mail, Calendar, Reminders, Maps, and Web Search.
"""

__version__ = "1.0.0"
__author__ = "PyApple MCP Contributors"
__email__ = "pyapple-mcp@example.com"
__description__ = "Python implementation of Apple MCP tools for macOS"

from .server import app

__all__ = ["app", "__version__"] 