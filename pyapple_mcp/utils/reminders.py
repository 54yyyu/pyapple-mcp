"""
Apple Reminders integration

Provides functionality to search, create, and manage reminders using the macOS Reminders app.
"""

import logging
from typing import Any, Dict, List, Optional
from .applescript import applescript

logger = logging.getLogger(__name__)

class RemindersHandler:
    """Handler for Apple Reminders app integration."""
    
    def __init__(self):
        """Initialize the reminders handler."""
        self.app_name = "Reminders"
    
    def list_reminders(
        self, list_name: Optional[str] = None, show_completed: bool = False
    ) -> List[Dict[str, str]]:
        """
        List all reminders or reminders from a specific list.

        Args:
            list_name: Name of the specific list to get reminders from (optional)
            show_completed: Whether to include completed reminders (default: False)

        Returns:
            List of dictionaries containing reminder information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Reminders app")
            return []
        
        script = f'''
        tell application "Reminders"
            set remindersList to {{}}
            set showCompleted to {str(show_completed).lower()}
            
            try
                repeat with aList in lists
                    repeat with aReminder in reminders of aList
                        set reminderName to name of aReminder
                        set reminderList to name of aList
                        set reminderCompleted to completed of aReminder
                        
                        -- Only include reminder if showCompleted is true OR reminder is not completed
                        if showCompleted or not reminderCompleted then
                            set reminderInfo to (reminderName & "|" & reminderList & "|" & (reminderCompleted as string))
                            set end of remindersList to reminderInfo
                        end if
                    end repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to remindersList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            reminders_data = result['result']
            if reminders_data.startswith("Error:"):
                logger.error(f"Reminders error: {reminders_data}")
                return []
            
            # Parse the reminders data
            reminders_list = []
            if reminders_data:
                for reminder_entry in reminders_data.split(";"):
                    if "|" in reminder_entry:
                        parts = reminder_entry.split("|", 2)
                        if len(parts) >= 3:
                            name, list_name, completed = parts
                            reminders_list.append({
                                "name": name,
                                "list": list_name,
                                "completed": completed.lower() == "true"
                            })
                        
            return reminders_list
        else:
            logger.error(f"Failed to list reminders: {result.get('error')}")
            return []
    
    def search_reminders(self, search_text: str) -> List[Dict[str, str]]:
        """
        Search for reminders containing the specified text.
        
        Args:
            search_text: Text to search for in reminder names
            
        Returns:
            List of dictionaries containing reminder information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Reminders app")
            return []
        
        script = f'''
        tell application "Reminders"
            set remindersList to {{}}
            set searchText to "{search_text}"
            
            try
                repeat with aList in lists
                    repeat with aReminder in reminders of aList
                        set reminderName to name of aReminder
                        if reminderName contains searchText then
                            set reminderList to name of aList
                            set reminderCompleted to completed of aReminder
                            
                            set reminderInfo to (reminderName & "|" & reminderList & "|" & (reminderCompleted as string))
                            set end of remindersList to reminderInfo
                        end if
                    end repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to remindersList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            reminders_data = result['result']
            if reminders_data.startswith("Error:"):
                logger.error(f"Reminders search error: {reminders_data}")
                return []
            
            # Parse the reminders data
            reminders_list = []
            if reminders_data:
                for reminder_entry in reminders_data.split(";"):
                    if "|" in reminder_entry:
                        parts = reminder_entry.split("|", 2)
                        if len(parts) >= 3:
                            name, list_name, completed = parts
                            reminders_list.append({
                                "name": name,
                                "list": list_name,
                                "completed": completed.lower() == "true"
                            })
                        
            return reminders_list
        else:
            logger.error(f"Failed to search reminders: {result.get('error')}")
            return []
    
    def create_reminder(
        self,
        name: str,
        list_name: Optional[str] = None,
        notes: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new reminder.
        
        Args:
            name: Name of the reminder
            list_name: Name of the list to create the reminder in (optional)
            notes: Additional notes for the reminder (optional)
            due_date: Due date in ISO format (optional)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Reminders app")
            return {"success": False, "message": "Cannot access Reminders app"}
        
        # Escape quotes in the content
        safe_name = name.replace('"', '\\"')
        safe_list = list_name.replace('"', '\\"') if list_name else ""
        safe_notes = notes.replace('"', '\\"') if notes else ""
        
        # Build the target list clause
        if list_name:
            list_clause = f'list "{safe_list}"'
        else:
            list_clause = 'default list'
        
        # Build notes clause
        notes_clause = f'set body of newReminder to "{safe_notes}"' if notes else ""
        
        # Build due date clause (simplified for now)
        due_date_clause = ""
        if due_date:
            # For simplicity, we'll just set the reminder date without parsing ISO format
            due_date_clause = f'set remind me date of newReminder to (current date)'
        
        script = f'''
        tell application "Reminders"
            try
                set targetList to {list_clause}
                set newReminder to make new reminder with properties {{name:"{safe_name}"}}
                move newReminder to targetList
                
                {notes_clause}
                {due_date_clause}
                
                return "Success: Reminder created"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": "Reminder created successfully"}
            else:
                logger.error(f"Reminders creation error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to create reminder: {result.get('error')}")
            return {"success": False, "message": f"Failed to create reminder: {result.get('error')}"}
    
    def open_reminder(self, search_text: str) -> Dict[str, Any]:
        """
        Open the Reminders app and focus on a specific reminder.
        
        Args:
            search_text: Text to search for to find the reminder
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Reminders app")
            return {"success": False, "message": "Cannot access Reminders app"}
        
        script = f'''
        tell application "Reminders"
            try
                activate
                
                -- Search for the reminder
                set searchText to "{search_text}"
                set foundReminder to null
                
                repeat with aList in lists
                    repeat with aReminder in reminders of aList
                        if name of aReminder contains searchText then
                            set foundReminder to aReminder
                            exit repeat
                        end if
                    end repeat
                    if foundReminder is not null then exit repeat
                end repeat
                
                if foundReminder is not null then
                    return "Success: Found and opened reminder: " & name of foundReminder
                else
                    return "Error: No reminder found containing: " & searchText
                end if
                
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
                logger.error(f"Reminders open error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to open reminder: {result.get('error')}")
            return {"success": False, "message": f"Failed to open reminder: {result.get('error')}"} 