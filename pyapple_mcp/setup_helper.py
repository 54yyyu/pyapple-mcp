#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup helper for pyapple-mcp.

This script provides utilities to automatically configure pyapple-mcp
by finding the installed executable and updating Claude Desktop's config.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def print_ascii_art():
    """Print the PyApple-MCP ASCII art logo."""
    print(
        """

  _____              ,--./,-.     __   __  _____ ____
 |  __ \           / #       \   |  \/  |/ ____|  __ \\
 | |__) |  _   _   |          |  | \  / | |    | |__) |
 |  ___/  | | | |  \  #    #  /  | |\/| | |    |  __ /
 | |      | |_| |   \        /   | |  | | |____| |
 |_|       \__, |     '--.-'     |_|  |_ \_____|_|
           __/ /
          |___/

PyApple-MCP Setup Helper
========================
Apple App Integration for Claude AI (macOS Only)
"""
    )




def find_executable():
    """Find the full path to the pyapple-mcp executable on macOS."""
    exe_name = "pyapple-mcp"
    
    exe_path = shutil.which(exe_name)
    if exe_path:
        print(f"Found pyapple-mcp in PATH at: {exe_path}")
        return exe_path
    
    # If not found in PATH, try to find it in common macOS installation directories
    potential_paths = []
    
    # Python framework locations (common on macOS)
    import glob

    framework_bins = glob.glob(
        "/Library/Frameworks/Python.framework/Versions/*/bin"
    )
    for bin_path in framework_bins:
        potential_paths.append(Path(bin_path) / exe_name)
    
    # Homebrew locations
    potential_paths.append(Path("/usr/local/bin") / exe_name)
    potential_paths.append(Path("/opt/homebrew/bin") / exe_name)
    
    # User's home directory
    potential_paths.append(Path.home() / ".local" / "bin" / exe_name)
    
    # Virtual environment
    if "VIRTUAL_ENV" in os.environ:
        potential_paths.append(Path(os.environ["VIRTUAL_ENV"]) / "bin" / exe_name)
    
    # uv paths
    potential_paths.append(Path.home() / ".astral" / "uv" / "bin" / exe_name)
    potential_paths.append(Path.home() / ".uv" / "bin" / exe_name)
    
    # Python user bin directories
    python_user_bins = glob.glob(
        str(Path.home() / "Library" / "Python" / "*" / "bin")
    )
    for bin_path in python_user_bins:
        potential_paths.append(Path(bin_path) / exe_name)
    
    # User site-packages
    import site
    try:
        for site_path in site.getsitepackages():
            potential_paths.append(Path(site_path) / "bin" / exe_name)
    except:
        pass
    
    for path in potential_paths:
        if path.exists() and os.access(path, os.X_OK):
            print(f"Found pyapple-mcp at: {path}")
            return str(path)
    
    # If still not found, search using find command
    print("Searching for pyapple-mcp in common locations...")
    try:
        import subprocess

        result = subprocess.run(
            [
                "find",
                os.path.expanduser("~"),
                "/usr/local",
                "/opt",
                "/Library",
                "-name",
                "pyapple-mcp",
                "-type",
                "f",
                "-executable",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        paths = result.stdout.strip().split("\n")
        if paths and paths[0]:
            print(f"Found pyapple-mcp at {paths[0]}")
            return paths[0]
    except Exception as e:
        print(f"Error searching for pyapple-mcp: {e}")
    
    print("Warning: Could not find pyapple-mcp executable.")
    print("Make sure pyapple-mcp is installed and in your PATH.")
    return None


def find_claude_config():
    """Find Claude Desktop config file path on macOS."""
    config_paths = [
        # Try both old and new paths
        (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude Desktop"
            / "claude_desktop_config.json"
        ),
        (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        ),
    ]
    
    # Check all possible locations
    for path in config_paths:
        if path.exists():
            print(f"Found Claude Desktop config at: {path}")
            return path
    
    # Return the default path (newer "Claude Desktop" path)
    default_path = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Claude Desktop"
        / "claude_desktop_config.json"
    )
    print(f"Claude Desktop config not found. Using default path: {default_path}")
    return default_path


def update_claude_config(config_path, pyapple_mcp_path):
    """Update Claude Desktop config to add pyapple-mcp."""
    # Create directory if it doesn't exist
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"Loaded existing config from: {config_path}")
        except json.JSONDecodeError:
            print(
                f"Error: Config file at {config_path} is not valid JSON. "
                "Creating new config."
            )
            config = {}
    else:
        print(f"Creating new config file at: {config_path}")
        config = {}
    
    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Add or update pyapple config
    # Always use the full path to ensure it works regardless of PATH
    config["mcpServers"]["pyapple"] = {"command": pyapple_mcp_path}
    
    # Write updated config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nSuccessfully wrote config to: {config_path}")
    except Exception as e:
        print(f"Error writing config file: {str(e)}")
        return False
    
    return config_path


def check_macos_requirements():
    """Check if we're on macOS and warn about permissions."""
    if sys.platform != "darwin":
        print("\n❌ ERROR: PyApple-MCP requires macOS!")
        print("   This tool integrates with Apple's native applications and frameworks")
        print("   which are only available on macOS.")
        if sys.platform == "win32":
            print("   Detected: Windows")
        elif sys.platform.startswith("linux"):
            print("   Detected: Linux")
        else:
            print(f"   Detected: {sys.platform}")
        print("\n   PyApple-MCP cannot function on this system.")
        return False
    
    print("\n✅ macOS detected - compatible system!")
    return True


def print_permissions_info():
    """Print information about macOS permissions."""
    print("\n🔐 macOS Permissions Setup")
    print("=" * 30)
    print("\nPyApple-MCP requires various macOS permissions to access Apple applications:")
    print("\n• Accessibility Access - for controlling applications")
    print("• Full Disk Access - for accessing application data")
    print("• Contacts - for reading/writing contact information")
    print("• Calendars - for accessing calendar events")
    print("• Reminders - for managing reminders")
    print("\nWhen you first run PyApple-MCP, macOS will prompt you to grant these permissions.")
    print("You may also need to manually enable permissions in:")
    print("System Preferences → Security & Privacy → Privacy")


def print_usage_info():
    """Print information about available tools."""
    print("\n🛠️  Available Tools")
    print("=" * 20)
    print("\nPyApple-MCP provides 8 tools for Apple app integration:")
    print("\n📧 mail        - Read, search, and send emails")
    print("📝 notes       - Create, search, and manage notes")
    print("👥 contacts    - Search and retrieve contact information")
    print("📅 calendar    - Manage calendar events and scheduling")
    print("✅ reminders   - Create and manage reminders")
    print("💬 messages    - Send and read text messages")
    print("🗺️ maps        - Search locations and get directions")
    print("🔍 web_search  - Search the web with DuckDuckGo")


def print_path_instructions(exe_path):
    """Print instructions for adding executable to PATH if needed."""
    exe_dir = os.path.dirname(exe_path)
    
    # Check if the directory is already in PATH
    current_path = os.environ.get('PATH', '')
    if exe_dir in current_path.split(os.pathsep):
        return  # Already in PATH
    
    print(f"\n💡 Optional: Add to PATH")
    print("=" * 25)
    print(f"\nTo run pyapple-mcp-setup from anywhere, add this to your shell profile:")
    print(f"export PATH=\"{exe_dir}:$PATH\"")
    print("\nAdd this line to:")
    print("• ~/.bashrc (for Bash)")
    print("• ~/.zshrc (for Zsh)")
    print("• ~/.bash_profile (for macOS Terminal)")
    print("\nThen restart your terminal or run: source ~/.zshrc")


def main(cli_args=None):
    """Main function to run the setup helper."""
    parser = argparse.ArgumentParser(
        description="Configure pyapple-mcp for Claude Desktop on macOS"
    )
    parser.add_argument("--config-path", help="Path to Claude Desktop config file")
    parser.add_argument("--skip-checks", action="store_true", help="Skip macOS compatibility checks")
    
    # If this is being called from CLI with existing args
    if cli_args is not None and hasattr(cli_args, 'config_path'):
        args = cli_args
        print("Using arguments passed from command line")
    else:
        # Otherwise parse from command line
        args = parser.parse_args()
        print("Parsed arguments from command line")
    
    # Print ASCII art
    print_ascii_art()
    
    # Check macOS requirements
    if not args.skip_checks:
        if not check_macos_requirements():
            print("\nSetup cannot continue on non-macOS systems.")
            print("PyApple-MCP requires macOS to integrate with Apple applications.")
            return 1
    
    # Find pyapple-mcp executable
    exe_path = find_executable()
    if not exe_path:
        print("Error: Could not find pyapple-mcp executable.")
        print("\nTry installing pyapple-mcp first:")
        print("  pip install pyapple-mcp")
        print("  # or")
        print("  uv pip install pyapple-mcp")
        return 1
    print(f"Using pyapple-mcp at: {exe_path}")
    
    # Find Claude Desktop config
    config_path = args.config_path
    if not config_path:
        config_path = find_claude_config()
    else:
        print(f"Using specified config path: {config_path}")
        config_path = Path(config_path)
    
    if not config_path:
        print("Error: Could not determine Claude Desktop config path.")
        return 1
    
    # Update config
    try:
        updated_config_path = update_claude_config(config_path, exe_path)
        
        if updated_config_path:
            print("\n🎉 Setup complete!")
            print("\nTo use PyApple-MCP in Claude Desktop:")
            print("1. Restart Claude Desktop if it's running")
            print("2. In Claude, you should see PyApple-MCP tools available")
            
            # Print additional info
            print_permissions_info()
            print_usage_info()
            print_path_instructions(exe_path)
            
            print("\n📖 Next Steps:")
            print("1. Grant macOS permissions when prompted")
            print("2. Restart Claude Desktop")
            print("3. Start using Apple app integration in Claude!")
            
            return 0
        else:
            print("\nSetup failed. See errors above.")
            return 1
    except Exception as e:
        print(f"\nSetup failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
