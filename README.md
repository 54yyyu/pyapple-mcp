# PyApple MCP Tools

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

A Python implementation of Apple-native tools for the [Model Context Protocol (MCP)](https://modelcontextprotocol.com/docs/mcp-protocol), providing seamless integration with macOS applications.

## Features

- **Messages**: Send and read messages using the Apple Messages app
- **Notes**: List, search, create, and delete notes in Apple Notes app  
- **Contacts**: Search contacts from Apple Contacts
- **Emails**: Send emails, search messages, and manage mail with Apple Mail
- **Reminders**: List, search, and create reminders in Apple Reminders app
- **Calendar**: Search events, create calendar entries, and manage your schedule
- **Web Search**: Search the web using DuckDuckGo
- **Maps**: Search locations, get directions, and manage guides with Apple Maps

## Quick Installation

### Automated Setup (Recommended)

```bash
# Install pyapple-mcp
pip install pyapple-mcp

# Run the setup helper to configure Claude Desktop
pyapple-mcp-setup
```

The setup helper will:
- Find your pyapple-mcp installation
- Locate your Claude Desktop config file
- Automatically add the configuration
- Display helpful setup information

### Manual Installation

1. **Install pyapple-mcp**:
   ```bash
   pip install pyapple-mcp
   ```

2. **Configure Claude Desktop** by editing `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "pyapple": {
         "command": "pyapple-mcp"
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the new configuration.

## Usage Examples

### Basic Commands

```
Can you send a message to John Doe saying "Hello from Claude!"?
```

```
Find all notes about "AI research" and summarize them
```

```
Create a reminder to "Buy groceries" for tomorrow at 5pm
```

```
Search my calendar for events this week containing "meeting"
```

```
Get directions from "Apple Park" to "San Francisco Airport"
```

### Advanced Workflows

You can chain commands together for complex workflows:

```
"Read my note about the conference attendees, find their contact information, and send them a thank you email"
```

## Development

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pyapple-mcp/pyapple-mcp.git
   cd pyapple-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run the development server**:
   ```bash
   python -m pyapple_mcp.server
   ```

### Testing with MCP Inspector

```bash
# Test the server
mcp dev pyapple_mcp/server.py

# Test with dependencies
mcp dev pyapple_mcp/server.py --with httpx --with beautifulsoup4
```

## Requirements

- **macOS 10.15+** (Catalina or later)
- **Python 3.10+**
- **Appropriate permissions** for accessing:
  - Contacts
  - Calendar
  - Messages
  - Mail
  - Notes
  - Reminders
  - Automation (for controlling apps)

## Permissions Setup

On first use, macOS will prompt for various permissions. Grant access to:

1. **Contacts** - for contact search functionality
2. **Calendar** - for calendar event management
3. **Messages** - for sending/reading messages  
4. **Mail** - for email operations
5. **Notes** - for notes access
6. **Reminders** - for reminder management
7. **Automation** - for controlling applications via AppleScript

## Troubleshooting

### Common Issues

**Permission Denied Errors**:
- Go to **System Settings > Privacy & Security**
- Grant access to the required applications
- Restart Claude Desktop

**Module Import Errors**:
- Ensure you're running on macOS
- Install PyObjC frameworks: `pip install pyobjc`

**AppleScript Execution Errors**:
- Check that the target applications are installed
- Verify automation permissions in System Settings

**Setup Issues**:
- Run `pyapple-mcp-setup --help` for setup options
- Check that pyapple-mcp is in your PATH: `which pyapple-mcp`
- Use `pyapple-mcp-setup --config-path /path/to/config` for custom config locations

### Debug Mode

Run with debug logging:
```bash
PYAPPLE_DEBUG=1 python -m pyapple_mcp.server
```

## Architecture

```
pyapple-mcp/
├── pyapple_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── setup_helper.py    # Setup and configuration helper
│   └── utils/
│       ├── __init__.py
│       ├── applescript.py # AppleScript execution
│       ├── calendar.py    # Calendar integration
│       ├── contacts.py    # Contacts integration
│       ├── mail.py        # Mail integration
│       ├── maps.py        # Maps integration
│       ├── messages.py    # Messages integration
│       ├── notes.py       # Notes integration
│       ├── reminders.py   # Reminders integration
│       └── websearch.py   # Web search functionality
├── tests/
├── requirements.txt
├── README.md
├── LICENSE
└── pyproject.toml
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original [apple-mcp](https://github.com/dhravya/apple-mcp) TypeScript implementation
- Built with the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses PyObjC for macOS system integration 
