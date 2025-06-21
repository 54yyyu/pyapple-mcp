#!/usr/bin/env python3
"""
PyApple MCP Installation Test Script

This script tests the installation and basic functionality of PyApple MCP.
"""

import sys
import subprocess
import json
import os
from pathlib import Path

def print_status(message, status="INFO"):
    """Print a formatted status message."""
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "WARNING": "⚠️",
        "ERROR": "❌",
        "TEST": "🧪"
    }
    print(f"{symbols.get(status, '•')} {message}")

def test_python_version():
    """Test if Python version is compatible."""
    print_status("Testing Python version...", "TEST")
    
    if sys.version_info < (3, 9):
        print_status(f"Python {sys.version} is too old. Requires Python 3.9+", "ERROR")
        return False
    
    print_status(f"Python {sys.version.split()[0]} - Compatible", "SUCCESS")
    return True

def test_macos():
    """Test if running on macOS."""
    print_status("Testing operating system...", "TEST")
    
    if sys.platform != "darwin":
        print_status(f"Running on {sys.platform}. PyApple MCP requires macOS", "ERROR")
        return False
    
    print_status("Running on macOS - Compatible", "SUCCESS")
    return True

def test_package_import():
    """Test if PyApple MCP can be imported."""
    print_status("Testing package import...", "TEST")
    
    try:
        import pyapple_mcp
        print_status(f"PyApple MCP v{pyapple_mcp.__version__} imported successfully", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"Failed to import PyApple MCP: {e}", "ERROR")
        return False

def test_dependencies():
    """Test if all dependencies are available."""
    print_status("Testing dependencies...", "TEST")
    
    required_packages = [
        "mcp",
        "httpx", 
        "beautifulsoup4",
    ]
    
    optional_packages = [
        "objc",  # PyObjC
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print_status(f"Missing required dependencies: {', '.join(missing_required)}", "ERROR")
        return False
    
    if missing_optional:
        print_status(f"Missing optional dependencies: {', '.join(missing_optional)}", "WARNING")
        print_status("Install with: pip install pyobjc", "INFO")
    
    print_status("All required dependencies available", "SUCCESS")
    return True

def test_applescript():
    """Test if AppleScript can be executed."""
    print_status("Testing AppleScript execution...", "TEST")
    
    try:
        from pyapple_mcp.utils.applescript import AppleScriptRunner
        runner = AppleScriptRunner()
        
        # Simple test script
        result = runner.run_script('return "test"')
        
        if result['success'] and result['result'] == "test":
            print_status("AppleScript execution working", "SUCCESS")
            return True
        else:
            print_status(f"AppleScript test failed: {result.get('error', 'Unknown error')}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"AppleScript test error: {e}", "ERROR")
        return False

def test_claude_config():
    """Test if Claude Desktop is configured."""
    print_status("Testing Claude Desktop configuration...", "TEST")
    
    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    
    if not config_path.exists():
        print_status("Claude Desktop config not found", "WARNING")
        print_status(f"Expected location: {config_path}", "INFO")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'mcpServers' in config and 'pyapple-mcp' in config['mcpServers']:
            print_status("PyApple MCP configured in Claude Desktop", "SUCCESS")
            return True
        else:
            print_status("PyApple MCP not found in Claude Desktop config", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"Error reading Claude config: {e}", "ERROR")
        return False

def test_server_startup():
    """Test if the MCP server can start."""
    print_status("Testing server startup...", "TEST")
    
    try:
        # Try to import and initialize the server
        from pyapple_mcp.server import app
        print_status("Server can be initialized", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Server startup failed: {e}", "ERROR")
        return False

def main():
    """Run all tests."""
    print("🍎 PyApple MCP Installation Test")
    print("=" * 35)
    print()
    
    tests = [
        ("Python Version", test_python_version),
        ("macOS Check", test_macos),
        ("Package Import", test_package_import),
        ("Dependencies", test_dependencies),
        ("AppleScript", test_applescript),
        ("Claude Config", test_claude_config),
        ("Server Startup", test_server_startup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * (len(test_name) + 4))
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("📊 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("All tests passed! PyApple MCP is ready to use.", "SUCCESS")
        print_status("You can now use PyApple MCP with Claude Desktop.", "INFO")
        return 0
    else:
        print_status(f"{total - passed} tests failed. Please check the issues above.", "ERROR")
        print_status("Refer to the README for troubleshooting help.", "INFO")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 