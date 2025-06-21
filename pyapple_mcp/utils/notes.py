"""
Apple Notes integration

Provides functionality to search, list, and create notes in the macOS Notes app.
"""

import logging
from typing import Dict, List, Any
from .applescript import applescript

logger = logging.getLogger(__name__)

class NotesHandler:
    """Handler for Apple Notes app integration."""
    
    def __init__(self):
        """Initialize the notes handler."""
        self.app_name = "Notes"
    
    def search_notes(self, search_text: str) -> List[Dict[str, str]]:
        """
        Search for notes containing the specified text.
        
        Args:
            search_text: Text to search for in notes
            
        Returns:
            List of dictionaries containing note information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Notes app")
            return []
        
        script = f'''
        tell application "Notes"
            set foundNotes to {{}}
            set searchText to "{search_text}"
            
            try
                repeat with anAccount in accounts
                    repeat with aFolder in folders of anAccount
                        repeat with aNote in notes of aFolder
                            set noteContent to body of aNote
                            set noteTitle to name of aNote
                            
                            if (noteContent contains searchText) or (noteTitle contains searchText) then
                                set end of foundNotes to (noteTitle & "|" & noteContent)
                            end if
                        end repeat
                    end repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to foundNotes as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            notes_data = result['result']
            if notes_data.startswith("Error:"):
                logger.error(f"Notes error: {notes_data}")
                return []
            
            # Parse the notes data
            notes_list = []
            if notes_data:
                for note_entry in notes_data.split(";"):
                    if "|" in note_entry:
                        title, content = note_entry.split("|", 1)
                        notes_list.append({
                            "title": title,
                            "content": content
                        })
                        
            return notes_list
        else:
            logger.error(f"Failed to search notes: {result.get('error')}")
            return []
    
    def list_notes(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        List all notes (limited to prevent overwhelming output).
        
        Args:
            limit: Maximum number of notes to return
            
        Returns:
            List of dictionaries containing note information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Notes app")
            return []
        
        script = f'''
        tell application "Notes"
            set allNotes to {{}}
            set noteCount to 0
            set maxNotes to {limit}
            
            try
                repeat with anAccount in accounts
                    repeat with aFolder in folders of anAccount
                        repeat with aNote in notes of aFolder
                            if noteCount >= maxNotes then exit repeat
                            
                            set noteContent to body of aNote
                            set noteTitle to name of aNote
                            set end of allNotes to (noteTitle & "|" & noteContent)
                            set noteCount to noteCount + 1
                        end repeat
                        if noteCount >= maxNotes then exit repeat
                    end repeat
                    if noteCount >= maxNotes then exit repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to allNotes as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            notes_data = result['result']
            if notes_data.startswith("Error:"):
                logger.error(f"Notes error: {notes_data}")
                return []
            
            # Parse the notes data
            notes_list = []
            if notes_data:
                for note_entry in notes_data.split(";"):
                    if "|" in note_entry:
                        title, content = note_entry.split("|", 1)
                        notes_list.append({
                            "title": title,
                            "content": content
                        })
                        
            return notes_list
        else:
            logger.error(f"Failed to list notes: {result.get('error')}")
            return []
    
    def create_note(self, title: str, body: str, folder_name: str = "Claude") -> Dict[str, Any]:
        """
        Create a new note in the specified folder.
        
        Args:
            title: Title of the note
            body: Content of the note
            folder_name: Name of the folder to create the note in
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Notes app")
            return {"success": False, "message": "Cannot access Notes app"}
        
        # Escape quotes in the content
        safe_title = title.replace('"', '\\"')
        safe_body = body.replace('"', '\\"')
        safe_folder = folder_name.replace('"', '\\"')
        
        script = f'''
        tell application "Notes"
            try
                -- Try to find the folder, create it if it doesn't exist
                set targetFolder to null
                set targetAccount to account 1
                
                try
                    set targetFolder to folder "{safe_folder}" of targetAccount
                on error
                    -- Folder doesn't exist, create it
                    set targetFolder to make new folder with properties {{name:"{safe_folder}"}} at targetAccount
                end try
                
                -- Create the note
                set newNote to make new note at targetFolder
                set name of newNote to "{safe_title}"
                set body of newNote to "{safe_body}"
                
                return "Success: Note created"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": "Note created successfully"}
            else:
                logger.error(f"Notes creation error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to create note: {result.get('error')}")
            return {"success": False, "message": f"Failed to create note: {result.get('error')}"} 