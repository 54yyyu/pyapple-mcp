"""
Apple Notes integration

Provides functionality to search, list, and create notes in the macOS Notes app.
"""

import logging
from typing import Any, Dict, List
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
    
    def create_note(
        self, title: str, body: str, folder_name: str = "Claude"
    ) -> Dict[str, Any]:
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
        
        # Escape quotes and newlines in the content
        safe_title = title.replace('"', '\\"').replace('\n', '\\n')
        safe_body = body.replace('"', '\\"').replace('\n', '\\n')
        safe_folder = folder_name.replace('"', '\\"')
        
        script = f'''
        tell application "Notes"
            try
                -- Try to find the folder, create it if it doesn't exist
                set targetFolder to missing value
                set targetAccount to account 1
                
                try
                    set targetFolder to folder "{safe_folder}" of targetAccount
                on error
                    -- Folder doesn't exist, create it
                    set targetFolder to make new folder with properties \
                        {{name:"{safe_folder}"}} at targetAccount
                end try
                
                -- Create the note first, then set properties
                set newNote to make new note at targetFolder
                set body of newNote to "{safe_body}"
                set name of newNote to "{safe_title}"
                
                return (
                    "Success: Note '" & "{safe_title}" & "' created in folder '" 
                    & "{safe_folder}" & "'"
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
                logger.error(f"Notes creation error: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to create note: {result.get('error')}")
            return {"success": False, "message": f"Failed to create note: {result.get('error')}"}
    
    def delete_note(self, search_text: str) -> Dict[str, Any]:
        """
        Delete a note by searching for its title or content.
        
        Args:
            search_text: Text to search for in note titles or content
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Notes app")
            return {"success": False, "message": "Cannot access Notes app"}
        
        if not search_text.strip():
            return {"success": False, "message": "Search text is required for delete operation"}
        
        safe_search = search_text.replace('"', '\\"')
        
        script = f'''
        tell application "Notes"
            try
                set searchText to "{safe_search}"
                set matchingNotes to {{}}
                
                -- Get all notes and check each one
                set allNotes to notes
                repeat with aNote in allNotes
                    try
                        set noteTitle to name of aNote
                        set noteContent to body of aNote
                        if (noteTitle contains searchText) or (noteContent contains searchText) then
                            set end of matchingNotes to aNote
                        end if
                    on error
                        -- Skip any problematic notes
                    end try
                end repeat
                
                set noteCount to length of matchingNotes
                
                if noteCount = 0 then
                    return "Error: No notes found matching '" & searchText & "'"
                else if noteCount > 1 then
                    return "Error: Multiple notes found matching '" & searchText & "'. Please be more specific."
                else
                    set targetNote to item 1 of matchingNotes
                    set noteTitle to name of targetNote
                    delete targetNote
                    return "Success: Deleted note '" & noteTitle & "'"
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
                logger.info(f"Note deleted successfully: {search_text}")
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Failed to delete note: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to delete note: {result.get('error')}")
            return {"success": False, "message": f"Failed to delete note: {result.get('error')}"} 