#!/bin/bash
# PyApple-MCP Installation Script
# https://github.com/54yyyu/pyapple-mcp
# Usage: curl -LsSf https://raw.githubusercontent.com/54yyyu/pyapple-mcp/main/scripts/install.sh | sh

set -e

# Text colors
BOLD="$(tput bold 2>/dev/null || echo '')"
BLUE="$(tput setaf 4 2>/dev/null || echo '')"
GREEN="$(tput setaf 2 2>/dev/null || echo '')"
YELLOW="$(tput setaf 3 2>/dev/null || echo '')"
RED="$(tput setaf 1 2>/dev/null || echo '')"
NC="$(tput sgr0 2>/dev/null || echo '')" # No Color

# Functions for log messages
info() {
  echo -e "${BOLD}${BLUE}INFO${NC}: $1"
}

success() {
  echo -e "${BOLD}${GREEN}SUCCESS${NC}: $1"
}

warn() {
  echo -e "${BOLD}${YELLOW}WARNING${NC}: $1"
}

error() {
  echo -e "${BOLD}${RED}ERROR${NC}: $1"
  exit 1
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Print logo and header
echo -e "${BLUE}"
echo "  _____              ,--./,-.      __   __  _____ _____  "
echo " |  __ \\          / #       \\   |  \\/  |/ ____|  __ \\ "
echo " | |__) |  _   _   |          |   | \\  / | |    | |__) |"
echo " |  ___/  | | |    \\  #    # /   | |\\/| | |    |  __ / "
echo " | |      | |_| |   \\       /    | |   | | |____| |     "
echo " |_|      \\__, |     '--.-'      |_|   |_\\_____|_|     "
echo "           __/ |                                     "
echo "          |___/                                      "
echo -e "${NC}"
echo "PyApple-MCP Installation Script"
echo "================================"
echo "Apple App Integration for Claude AI (macOS Only)"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Darwin)
    OS="macos"
    success "macOS detected - compatible system!"
    ;;
  Linux)
    error "Linux detected - PyApple-MCP requires macOS to integrate with Apple applications"
    ;;
  MINGW* | MSYS* | CYGWIN* | Windows_NT)
    error "Windows detected - PyApple-MCP requires macOS to integrate with Apple applications"
    ;;
  *)
    error "Unsupported operating system: $OS - PyApple-MCP requires macOS"
    ;;
esac

# Install uv if not present
install_uv() {
  info "Installing uv package manager..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Update PATH for current session
  if [[ -z "${UV_BIN_PATH}" ]]; then
    export PATH="${HOME}/.astral/uv/bin:${PATH}"
  fi
  
  # Check if shell config files exist and add uv to PATH
  if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "astral/uv/bin" "$HOME/.bashrc"; then
      echo 'export PATH="${HOME}/.astral/uv/bin:${PATH}"' >> "$HOME/.bashrc"
      info "Added uv to PATH in .bashrc"
    fi
  elif [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "astral/uv/bin" "$HOME/.zshrc"; then
      echo 'export PATH="${HOME}/.astral/uv/bin:${PATH}"' >> "$HOME/.zshrc"
      info "Added uv to PATH in .zshrc"
    fi
  else
    warn "Please add the following to your shell profile:"
    echo 'export PATH="${HOME}/.astral/uv/bin:${PATH}"'
  fi
  
  # Verify uv installation
  if command_exists uv; then
    success "uv installed successfully!"
  else
    warn "uv installation complete but command not found in PATH"
    warn "You may need to restart your terminal or manually set PATH"
  fi
}

# Check if Python is installed
info "Checking for Python..."
if command_exists python3; then
  PYTHON_CMD="python3"
elif command_exists python; then
  # Check if Python is version 3
  if python --version 2>&1 | grep -q "Python 3"; then
    PYTHON_CMD="python"
  else
    error "Python 3 is required (Python 2 detected)"
  fi
else
  error "Python 3 not found. Please install Python 3.9 or newer."
fi

# Verify Python version
PY_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
  error "Python 3.9 or newer is required (detected $PY_VERSION)"
fi

success "Python $PY_VERSION detected"

# Check if uv is installed, install if not
if ! command_exists uv; then
  warn "uv package manager not found"
  echo -n "Would you like to install uv for better dependency management? (y/N) "
  read -r REPLY
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_uv
  else
    warn "Skipping uv installation, will use pip if available"
  fi
fi

# Function to add directory to PATH in shell config
add_to_path() {
  local dir="$1"
  local config_file="$2"
  
  # Skip if the file doesn't exist
  if [ ! -f "$config_file" ]; then
    return
  fi
  
  # Check if the directory is already in the config file
  if grep -q "export PATH=.*$dir" "$config_file"; then
    info "PATH already contains $dir in $config_file"
    return
  fi

  # Add to PATH
  echo "" >> "$config_file"
  echo "# Added by pyapple-mcp installer" >> "$config_file"
  echo "export PATH=\"$dir:\$PATH\"" >> "$config_file"
  info "Added $dir to PATH in $config_file"
}

# Install pyapple-mcp
info "Installing pyapple-mcp..."

if command_exists uv; then
  info "Using uv package manager"
  uv pip install git+https://github.com/54yyyu/pyapple-mcp.git
elif command_exists pip3; then
  warn "Using pip3 instead of uv"
  pip3 install git+https://github.com/54yyyu/pyapple-mcp.git
elif command_exists pip; then
  warn "Using pip instead of uv"
  pip install git+https://github.com/54yyyu/pyapple-mcp.git
else
  error "Neither uv nor pip found. Please install pip or uv and try again."
fi

# Attempt to add common Python bin directories to PATH
PYTHON_DIRS=(
  "$HOME/.local/bin"
  "$HOME/Library/Python/"*"/bin"
  "$HOME/.astral/uv/venvs/"*"/bin"
  "/usr/local/bin"
  "$HOME/.uv/bin"
  "$HOME/.uv/venvs/"*"/bin"
  "$HOME/.astral/uv/bin"
  "/opt/homebrew/bin"
)

for DIR_PATTERN in "${PYTHON_DIRS[@]}"; do
  for DIR in $DIR_PATTERN; do
    if [ -d "$DIR" ]; then
      # Add to shell config files
      add_to_path "$DIR" "$HOME/.bashrc"
      add_to_path "$DIR" "$HOME/.zshrc"
      add_to_path "$DIR" "$HOME/.bash_profile"
      add_to_path "$DIR" "$HOME/.profile"
      
      # Add to current session
      export PATH="$DIR:$PATH"
    fi
  done
done

# Find the script path
find_script_path() {
  # Try to find where pyapple-mcp was installed
  for DIR in "$HOME/.local/bin" "$HOME/Library/Python/"*"/bin" "$HOME/.astral/uv/venvs/"*"/bin" "/usr/local/bin" "$HOME/.uv/bin" "$HOME/.uv/venvs/"*"/bin" "$HOME/.astral/uv/bin" "/opt/homebrew/bin"; do
    # Expand glob patterns
    for GLOB in $DIR; do
      if [ -f "$GLOB/pyapple-mcp" ]; then
        echo "$GLOB"
        return 0
      fi
    done
  done
  
  # Check Python's script directory
  PYTHON_BIN_DIR=$($PYTHON_CMD -c "import sys, os; print(os.path.join(sys.prefix, 'bin'))" 2>/dev/null)
  if [ -n "$PYTHON_BIN_DIR" ] && [ -f "$PYTHON_BIN_DIR/pyapple-mcp" ]; then
    echo "$PYTHON_BIN_DIR"
    return 0
  fi
  
  # Last resort - try to find it anywhere in standard locations
  find_result=$(find /usr/local /opt/homebrew $HOME/.local $HOME/Library $HOME/.uv $HOME/.astral -name pyapple-mcp -type f 2>/dev/null | head -n 1)
  if [ -n "$find_result" ]; then
    dirname "$find_result"
    return 0
  fi
  
  return 1
}

# Verify installation
if command_exists pyapple-mcp; then
  VERSION=$(pyapple-mcp --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "Unknown")
  success "Installation successful! PyApple-MCP version $VERSION"
else
  # Try to find the script and add it to PATH
  SCRIPT_PATH=$(find_script_path)
  
  if [ -n "$SCRIPT_PATH" ]; then
    info "Found pyapple-mcp at $SCRIPT_PATH"
    
    # Create a symlink in /usr/local/bin if possible (requires sudo)
    if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
      ln -sf "$SCRIPT_PATH/pyapple-mcp" "/usr/local/bin/pyapple-mcp"
      info "Created symlink in /usr/local/bin"
      
      if command_exists pyapple-mcp; then
        VERSION=$(pyapple-mcp --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "Unknown")
        success "Installation successful! PyApple-MCP version $VERSION"
        return
      fi
    fi
    
    # Add to PATH for current session
    export PATH="$SCRIPT_PATH:$PATH"
    
    # Update shell config files
    if [ -f "$HOME/.bashrc" ]; then
      if ! grep -q "$SCRIPT_PATH" "$HOME/.bashrc"; then
        echo "export PATH=\"$SCRIPT_PATH:\$PATH\"" >> "$HOME/.bashrc"
        info "Added $SCRIPT_PATH to PATH in .bashrc"
      fi
    fi
    
    if [ -f "$HOME/.zshrc" ]; then
      if ! grep -q "$SCRIPT_PATH" "$HOME/.zshrc"; then
        echo "export PATH=\"$SCRIPT_PATH:\$PATH\"" >> "$HOME/.zshrc"
        info "Added $SCRIPT_PATH to PATH in .zshrc"
      fi
    fi
    
    # Also try .bash_profile and .profile for macOS
    if [ -f "$HOME/.bash_profile" ]; then
      if ! grep -q "$SCRIPT_PATH" "$HOME/.bash_profile"; then
        echo "export PATH=\"$SCRIPT_PATH:\$PATH\"" >> "$HOME/.bash_profile"
        info "Added $SCRIPT_PATH to PATH in .bash_profile"
      fi
    fi
    
    if [ -f "$HOME/.profile" ]; then
      if ! grep -q "$SCRIPT_PATH" "$HOME/.profile"; then
        echo "export PATH=\"$SCRIPT_PATH:\$PATH\"" >> "$HOME/.profile"
        info "Added $SCRIPT_PATH to PATH in .profile"
      fi
    fi
    
    warn "Please restart your terminal or run 'source ~/.zshrc' (or your shell config) to update your PATH"
    
    # Print the full path for manual use
    echo ""
    echo "To use pyapple-mcp immediately without restarting your terminal, you can:"
    echo ""
    echo "  1. Run with the full path:"
    echo "     $SCRIPT_PATH/pyapple-mcp"
    echo ""
    echo "  2. Or update your current session's PATH:"
    echo "     export PATH=\"$SCRIPT_PATH:\$PATH\""
    echo ""
    
    # Try one more check after updating PATH in the current session
    if command_exists pyapple-mcp; then
      VERSION=$(pyapple-mcp --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "Unknown")
      success "Installation successful! PyApple-MCP is now available in this terminal session."
    else
      warn "The installation succeeded, but you'll need to update your PATH to use pyapple-mcp."
    fi
  else
    # Last attempt - try to get the directory directly from pip
    PIP_SCRIPT_PATH=$($PYTHON_CMD -m pip show pyapple-mcp 2>/dev/null | grep "^Location:" | cut -d " " -f 2)
    if [ -n "$PIP_SCRIPT_PATH" ]; then
      SITE_BIN_DIR="$PIP_SCRIPT_PATH/../../../bin"
      if [ -f "$SITE_BIN_DIR/pyapple-mcp" ]; then
        SCRIPT_PATH="$SITE_BIN_DIR"
        info "Found pyapple-mcp at $SCRIPT_PATH"
        echo ""
        echo "To use pyapple-mcp, add this directory to your PATH:"
        echo "export PATH=\"$SCRIPT_PATH:\$PATH\""
        echo ""
        echo "You can add this line to your shell configuration file (.bashrc, .zshrc, etc.)"
      else
        warn "Found package at $PIP_SCRIPT_PATH but could not locate the executable."
      fi
    else
      error "Installation failed. Try installing manually: pip install git+https://github.com/54yyyu/pyapple-mcp.git"
    fi
  fi
fi

# Check macOS permissions
echo ""
echo -e "${BLUE}=== macOS Permissions Setup ===${NC}"
echo ""
warn "PyApple-MCP requires various macOS permissions to access Apple applications:"
echo ""
echo "• Accessibility Access - for controlling applications"
echo "• Full Disk Access - for accessing application data"
echo "• Contacts - for reading/writing contact information"
echo "• Calendars - for accessing calendar events"
echo "• Reminders - for managing reminders"
echo ""
echo "When you first run PyApple-MCP, macOS will prompt you to grant these permissions."
echo "You may also need to manually enable permissions in:"
echo "System Preferences → Security & Privacy → Privacy"

echo ""
echo -e "${BLUE}=== Claude Desktop Integration ===${NC}"
echo ""
echo "To set up Claude Desktop integration, add this to your claude_desktop_config.json:"
echo ""
echo "Location: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo -e "${BOLD}Configuration:${NC}"
echo '{'
echo '  "mcpServers": {'
echo '    "pyapple": {'
echo '      "command": "pyapple-mcp"'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "After adding the configuration:"
echo "1. Save the file"
echo "2. Restart Claude Desktop"
echo "3. You should see PyApple-MCP tools available in Claude"

echo ""
echo -e "${BLUE}=== Available Tools ===${NC}"
echo ""
echo "PyApple-MCP provides 8 tools for Apple app integration:"
echo ""
echo "📧 mail        - Read, search, and send emails"
echo "📝 notes       - Create, search, and manage notes"
echo "👥 contacts    - Search and retrieve contact information"  
echo "📅 calendar    - Manage calendar events and scheduling"
echo "✅ reminders   - Create and manage reminders"
echo "💬 messages    - Send and read text messages"
echo "🗺️  maps       - Search locations and get directions"
echo "🔍 web_search  - Search the web with DuckDuckGo"

echo ""
success "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure Claude Desktop (see above)"
echo "2. Grant macOS permissions when prompted"
echo "3. Restart Claude Desktop"
echo "4. Start using Apple app integration in Claude!" 