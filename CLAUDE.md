# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Development Setup
```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run the MCP server directly
python -m pyapple_mcp.server

# Test with MCP Inspector
mcp dev pyapple_mcp/server.py
mcp dev pyapple_mcp/server.py --with httpx --with beautifulsoup4
```

### Code Quality Tools
```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Type checking with mypy
mypy .

# Run tests
pytest
```

### Building and Distribution
```bash
# Build package
python -m build

# Install locally
pip install .
```

## Architecture Overview

This is a Python MCP (Model Context Protocol) server that provides Apple-native integrations for macOS. The server uses FastMCP and implements handlers for various Apple applications.

### Core Components

- **`server.py`**: Main MCP server using FastMCP framework with tool registration
- **`setup_helper.py`**: Automated configuration helper for Claude Desktop integration
- **`utils/`**: Individual handler modules for each Apple application

### Handler Architecture

Each Apple application integration follows a consistent pattern:
- **Handler Class**: Implements the core functionality (e.g., `ContactsHandler`, `NotesHandler`)
- **AppleScript Integration**: Uses `applescript.py` for macOS system calls
- **MCP Tools**: Registered as FastMCP tools with proper schemas and error handling

### Key Handlers

- **Messages** (`messages.py`): Send/read messages via Apple Messages
- **Notes** (`notes.py`): List, search, create notes in Apple Notes
- **Contacts** (`contacts.py`): Search Apple Contacts database
- **Mail** (`mail.py`): Email operations with Apple Mail, includes optimized local database search
- **Calendar** (`calendar.py`): Event management with Apple Calendar
- **Reminders** (`reminders.py`): Task management with Apple Reminders
- **Maps** (`maps.py`): Location search and directions via Apple Maps
- **Web Search** (`websearch.py`): DuckDuckGo web search functionality

### Configuration and Permissions

The server requires macOS-specific permissions for:
- Contacts, Calendar, Messages, Mail, Notes, Reminders access
- Automation permissions for AppleScript execution
- Application-specific privacy settings

### Entry Points

- `pyapple-mcp`: Main server executable
- `pyapple-mcp-setup`: Configuration helper for Claude Desktop

## Development Notes

- All handlers use PyObjC frameworks for native macOS integration
- AppleScript is the primary method for application automation
- Error handling includes permission checks and graceful fallbacks
- The codebase uses type hints throughout (mypy configured)
- Mail handler implements optimized local database search for performance