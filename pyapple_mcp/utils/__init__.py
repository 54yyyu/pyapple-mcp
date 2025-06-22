"""
Utility modules for PyApple MCP

This package contains utility classes for interacting with various macOS applications
through AppleScript and PyObjC frameworks.
"""

from .applescript import AppleScriptRunner

__all__ = ["AppleScriptRunner"]