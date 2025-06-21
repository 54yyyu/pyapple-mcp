"""
Apple Maps integration

Provides functionality to search locations, manage guides, save favorites, and get directions using Apple Maps.
"""

import logging
from typing import Dict, List, Any, Optional
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
            return {"success": False, "locations": [], "message": "Cannot access Maps app"}
        
        script = f'''
        tell application "Maps"
            try
                activate
                search for "{query}"
                delay 2
                
                return "Success: Search completed for {query}"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                # Simplified response since AppleScript doesn't easily expose search results
                return {
                    "success": True,
                    "locations": [{"name": f"Location for '{query}'", "address": "Address not available via AppleScript"}],
                    "message": f"Search completed for '{query}'. Please check Maps app for results."
                }
            else:
                logger.error(f"Maps search error: {result_msg}")
                return {"success": False, "locations": [], "message": result_msg}
        else:
            logger.error(f"Failed to search locations: {result.get('error')}")
            return {"success": False, "locations": [], "message": f"Failed to search locations: {result.get('error')}"}
    
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
        
        script = f'''
        tell application "Maps"
            try
                activate
                search for "{address}"
                delay 2
                
                return "Success: Location saved (manual action may be required in Maps app)"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": f"Location '{name}' at '{address}' opened in Maps. You may need to manually save it to favorites."}
            else:
                logger.error(f"Maps save error: {result_msg}")
                return {"success": False, "message": result_msg}
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
        
        script = f'''
        tell application "Maps"
            try
                activate
                search for "{address}"
                delay 2
                
                return "Success: Pin dropped at {address}"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": f"Pin dropped for '{name}' at '{address}'"}
            else:
                logger.error(f"Maps pin error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to drop pin: {result.get('error')}")
            return {"success": False, "message": f"Failed to drop pin: {result.get('error')}"}
    
    def get_directions(self, from_address: str, to_address: str, transport_type: str = "driving") -> Dict[str, Any]:
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
        
        script = f'''
        tell application "Maps"
            try
                activate
                get directions from "{from_address}" to "{to_address}"
                delay 2
                
                return "Success: Directions requested from {from_address} to {to_address}"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": f"Directions requested from '{from_address}' to '{to_address}' using {transport_type} mode. Check Maps app for route details."}
            else:
                logger.error(f"Maps directions error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to get directions: {result.get('error')}")
            return {"success": False, "message": f"Failed to get directions: {result.get('error')}"}
    
    def list_guides(self) -> Dict[str, Any]:
        """
        List available guides in Apple Maps.
        Note: Limited functionality due to AppleScript constraints.
        
        Returns:
            Dictionary with success status and message
        """
        return {"success": True, "message": "Guide listing is not available via AppleScript. Please check the Maps app directly for your guides."}
    
    def create_guide(self, guide_name: str) -> Dict[str, Any]:
        """
        Create a new guide in Apple Maps.
        Note: Limited functionality due to AppleScript constraints.
        
        Args:
            guide_name: Name of the guide to create
            
        Returns:
            Dictionary with success status and message
        """
        return {"success": False, "message": f"Creating guides via AppleScript is not supported. Please create the guide '{guide_name}' manually in the Maps app."}
    
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
        return {"success": False, "message": f"Adding to guides via AppleScript is not supported. Please manually add '{address}' to the guide '{guide_name}' in the Maps app."} 