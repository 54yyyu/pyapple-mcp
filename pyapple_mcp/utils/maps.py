"""
Apple Maps integration

Provides functionality to search locations, manage guides, save favorites, and get directions using Apple Maps.
"""

import logging
from typing import Any, Dict, List, Optional
from .applescript import applescript

logger = logging.getLogger(__name__)

class MapsHandler:
    """Handler for Apple Maps app integration."""
    
    def __init__(self):
        """Initialize the maps handler."""
        self.app_name = "Maps"
    
    def search_locations(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search for locations using Apple Maps.

        Args:
            query: Search query for locations
            limit: Maximum number of results to return

        Returns:
            Dictionary with success status, locations list, and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {
                "success": False,
                "locations": [],
                "message": "Cannot access Maps app",
            }
        
        # Escape quotes in the query
        safe_query = query.replace('"', '\\"')
        
        # Simplified script to test basic functionality
        script = f'''
        tell application "Maps"
            try
                activate
                delay 2
                
                -- Note: Maps has very limited AppleScript support
                -- We can activate the app but cannot access UI elements reliably
                return "Success: Maps activated and search attempted for {safe_query}"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {
                    "success": True,
                    "locations": [
                        {
                            "name": f"Search: {query}",
                            "address": "Please check Maps app for results",
                        }
                    ],
                    "message": (
                        f"Maps activated for search '{query}'. Apple Maps has "
                        "limited AppleScript support - please manually search "
                        "in the Maps app."
                    ),
                }
            else:
                logger.error(f"Maps search error: {result_msg}")
                return {"success": False, "locations": [], "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to search locations: {result.get('error')}")
            return {
                "success": False,
                "locations": [],
                "message": f"AppleScript error: {result.get('error')}",
            }
    
    def save_location(self, name: str, address: str) -> Dict[str, Any]:
        """
        Save a location to favorites in Apple Maps.
        
        Args:
            name: Name of the location
            address: Address of the location
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        # Escape quotes in the address
        safe_address = address.replace('"', '\\"')
        safe_name = name.replace('"', '\\"')
        
        script = f'''
        tell application "Maps"
            try
                activate
                delay 0.5
                
                -- Search for the location
                set searchField to text field 1 of window 1
                set value of searchField to "{safe_address}"
                key code 36 -- Enter key
                
                -- Wait for search to complete
                delay 3
                
                -- Try to add to favorites (this requires manual interaction in most cases)
                -- Apple Maps doesn't provide full AppleScript automation for favorites
                return (
                    "Success: Location '{safe_name}' searched in Maps. To save as favorite, "
                    "please manually click the 'Add to Favorites' option in the Maps app."
                )
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Maps save error: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to save location: {result.get('error')}")
            return {"success": False, "message": f"Failed to save location: {result.get('error')}"}
    
    def drop_pin(self, name: str, address: str) -> Dict[str, Any]:
        """
        Drop a pin at the specified location in Apple Maps.
        
        Args:
            name: Name of the location
            address: Address of the location
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        # Escape quotes in the address
        safe_address = address.replace('"', '\\"')
        safe_name = name.replace('"', '\\"')
        
        script = f'''
        tell application "Maps"
            try
                activate
                delay 0.5
                
                -- Search for the location to effectively "drop a pin"
                set searchField to text field 1 of window 1
                set value of searchField to "{safe_address}"
                key code 36 -- Enter key
                
                -- Wait for search to complete and pin to appear
                delay 3
                
                return (
                    "Success: Pin location searched for '{safe_name}' at '{safe_address}'. "
                    "Pin should be visible in Maps app."
                )
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Maps pin error: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to drop pin: {result.get('error')}")
            return {"success": False, "message": f"Failed to drop pin: {result.get('error')}"}
    
    def get_directions(
        self,
        from_address: str,
        to_address: str,
        transport_type: str = "driving",
    ) -> Dict[str, Any]:
        """
        Get directions between two locations in Apple Maps.
        
        Args:
            from_address: Starting address
            to_address: Destination address
            transport_type: Type of transport (driving, walking, transit)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        # Escape quotes in addresses
        safe_from = from_address.replace('"', '\\"')
        safe_to = to_address.replace('"', '\\"')
        
        # Simplified directions script
        script = f'''
        tell application "Maps"
            try
                activate
                delay 2
                
                -- Apple Maps has very limited AppleScript automation
                -- We can open the app but UI automation is unreliable
                return "Success: Maps opened for directions from {safe_from} to {safe_to}"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {
                    "success": True,
                    "message": (
                        f"Maps opened for directions from '{from_address}' to '{to_address}'. "
                        "Due to Apple Maps' limited AppleScript support, please manually search "
                        f"for directions in the Maps app. Suggested search: '{from_address} to {to_address}'"
                    ),
                }
            else:
                logger.error(f"Maps directions error: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to get directions: {result.get('error')}")
            return {"success": False, "message": f"AppleScript error: {result.get('error')}"}
    
    def list_guides(self) -> Dict[str, Any]:
        """
        List available guides in Apple Maps.
        Note: Limited functionality due to AppleScript constraints.
        
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        script = '''
        tell application "Maps"
            try
                activate
                delay 0.5
                
                -- Try to access guides/collections
                -- Note: This is very limited as Maps doesn't expose guide data via AppleScript
                return "Success: Please check the Maps app directly for your guides and collections. AppleScript cannot access detailed guide information."
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            return {"success": False, "message": f"Failed to access Maps: {result.get('error')}"}
    
    def create_guide(self, guide_name: str) -> Dict[str, Any]:
        """
        Create a new guide in Apple Maps.
        Note: Limited functionality due to AppleScript constraints.
        
        Args:
            guide_name: Name of the guide to create
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        # Escape quotes in the guide name
        safe_name = guide_name.replace('"', '\\"')
        
        script = f'''
        tell application "Maps"
            try
                activate
                delay 0.5
                
                -- Apple Maps doesn't provide AppleScript access to create guides programmatically
                -- This opens Maps and provides instructions for manual creation
                return "Success: Maps app opened. To create a guide named '{safe_name}', please manually: 1) Go to Collections in Maps, 2) Click '+' to create new guide, 3) Name it '{safe_name}'"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            return {"success": False, "message": f"Failed to access Maps: {result.get('error')}"}
    
    def add_to_guide(self, address: str, guide_name: str) -> Dict[str, Any]:
        """
        Add a location to an existing guide in Apple Maps.
        Note: Limited functionality due to AppleScript constraints.
        
        Args:
            address: Address to add to the guide
            guide_name: Name of the guide to add to
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Maps app")
            return {"success": False, "message": "Cannot access Maps app"}
        
        # Escape quotes
        safe_address = address.replace('"', '\\"')
        safe_guide = guide_name.replace('"', '\\"')
        
        script = f'''
        tell application "Maps"
            try
                activate
                delay 0.5
                
                -- Search for the location first
                set searchField to text field 1 of window 1
                set value of searchField to "{safe_address}"
                key code 36 -- Enter key
                delay 2
                
                return "Success: Location '{safe_address}' searched in Maps. To add to guide '{safe_guide}', please manually click on the location pin and select 'Add to Guide' or 'Save to Collection'."
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            return {"success": False, "message": f"Failed to access Maps: {result.get('error')}"}
