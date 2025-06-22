"""
AppleScript execution utility

Provides a safe interface for executing AppleScript commands from Python
with proper error handling and timeout management.
"""

import subprocess
import logging
from typing import Any, Dict, Optional, Union
import json
import os

logger = logging.getLogger(__name__)

class AppleScriptRunner:
    """
    Utility class for executing AppleScript commands from Python.

    Provides methods for running AppleScript with proper error handling,
    timeout management, and result parsing.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the AppleScript runner.
        
        Args:
            timeout: Default timeout for script execution in seconds
        """
        self.timeout = timeout
        
    def run_script(self, script: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute an AppleScript and return the result.

        Args:
            script: The AppleScript code to execute
            timeout: Optional timeout override for this execution

        Returns:
            Dictionary with 'success', 'result', and 'error' keys
        """
        execution_timeout = timeout or self.timeout
        
        try:
            # Use osascript to execute the AppleScript
            process = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=execution_timeout,
                check=False,
            )
            
            if process.returncode == 0:
                result = process.stdout.strip()
                return {"success": True, "result": result, "error": None}
            else:
                error_msg = process.stderr.strip() or "Unknown AppleScript error"
                logger.error(f"AppleScript execution failed: {error_msg}")
                return {"success": False, "result": None, "error": error_msg}
                
        except subprocess.TimeoutExpired:
            error_msg = (
                f"AppleScript execution timed out after {execution_timeout} seconds"
            )
            logger.error(error_msg)
            return {"success": False, "result": None, "error": error_msg}
        except Exception as e:
            error_msg = f"Error executing AppleScript: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "result": None, "error": error_msg}
    
    def run_json_script(self, script: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute an AppleScript that returns JSON and parse the result.

        Args:
            script: The AppleScript code to execute (should return JSON)
            timeout: Optional timeout override for this execution

        Returns:
            Dictionary with 'success', 'result' (parsed JSON), and 'error' keys
        """
        execution_result = self.run_script(script, timeout)
        
        if not execution_result["success"]:
            return execution_result
            
        # Try to parse the result as JSON
        try:
            json_result = json.loads(execution_result["result"])
            return {"success": True, "result": json_result, "error": None}
        except (json.JSONDecodeError, TypeError) as e:
            # If JSON parsing fails, return the raw result
            logger.warning(f"Failed to parse AppleScript result as JSON: {e}")
            return execution_result
    
    def check_app_access(self, app_name: str) -> bool:
        """
        Check if we have access to a specific application.
        
        Args:
            app_name: Name of the application to check
            
        Returns:
            True if the application is accessible, False otherwise
        """
        script = f'''
        try
            tell application "{app_name}"
                get name
            end tell
            return "accessible"
        on error errMsg
            return "not accessible: " & errMsg
        end try
        '''
        
        result = self.run_script(script, timeout=5)
        if result['success'] and result['result'] == "accessible":
            return True
        else:
            logger.warning(f"Cannot access {app_name}: {result.get('result', result.get('error'))}")
            return False
    
    def ensure_app_running(self, app_name: str) -> bool:
        """
        Ensure an application is running, launching it if necessary.
        
        Args:
            app_name: Name of the application to launch
            
        Returns:
            True if the application is now running, False otherwise
        """
        script = f'''
        try
            tell application "{app_name}"
                if not running then
                    launch
                    delay 2
                end if
                return "running"
            end tell
        on error errMsg
            return "failed: " & errMsg
        end try
        '''
        
        result = self.run_script(script, timeout=10)
        if result['success'] and result['result'] == "running":
            return True
        else:
            logger.error(f"Failed to launch {app_name}: {result.get('result', result.get('error'))}")
            return False

# Global instance for convenience
applescript = AppleScriptRunner() 