"""
Apple Contacts integration

Provides functionality to search and retrieve contacts from the macOS Contacts app.
"""

import logging
from typing import Dict, List
from .applescript import applescript

logger = logging.getLogger(__name__)

class ContactsHandler:
    """Handler for Apple Contacts app integration."""
    
    def __init__(self):
        """Initialize the contacts handler."""
        self.app_name = "Contacts"
    
    def find_number(self, name: str) -> List[str]:
        """
        Find phone numbers for a contact by name.
        
        Args:
            name: Name to search for (can be partial)
            
        Returns:
            List of phone numbers for the contact
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Contacts app")
            return []
        
        script = f'''
        tell application "Contacts"
            set foundNumbers to {{}}
            set searchName to "{name}"
            
            try
                set foundPeople to (every person whose name contains searchName)
                
                repeat with aPerson in foundPeople
                    set personName to name of aPerson
                    set phoneNumbers to value of every phone of aPerson
                    
                    repeat with aPhone in phoneNumbers
                        set end of foundNumbers to (personName & ": " & aPhone)
                    end repeat
                end repeat
                
                if length of foundNumbers > 0 then
                    set AppleScript's text item delimiters to ", "
                    set resultString to foundNumbers as string
                    set AppleScript's text item delimiters to ""
                    return resultString
                else
                    return ""
                end if
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            # Parse the returned phone numbers
            phone_data = result['result']
            if phone_data.startswith("Error:"):
                logger.error(f"Contacts error: {phone_data}")
                return []
            
            # Extract just the phone numbers (remove names)
            numbers = []
            if phone_data:
                for item in phone_data.split(", "):
                    if ": " in item:
                        numbers.append(item.split(": ", 1)[1])
                    
            return numbers
        else:
            logger.error(f"Failed to search contacts: {result.get('error')}")
            return []
    
    def get_all_numbers(self) -> Dict[str, List[str]]:
        """
        Get all contacts with their phone numbers.
        
        Returns:
            Dictionary mapping contact names to lists of phone numbers
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Contacts app")
            return {}
        
        script = '''
        tell application "Contacts"
            set contactsList to {}
            
            try
                set allPeople to every person
                
                repeat with aPerson in allPeople
                    set personName to name of aPerson
                    set phoneNumbers to value of every phone of aPerson
                    
                    if length of phoneNumbers > 0 then
                        set phoneList to {}
                        repeat with aPhone in phoneNumbers
                            set end of phoneList to aPhone
                        end repeat
                        
                        set AppleScript's text item delimiters to "|"
                        set phoneString to phoneList as string
                        set AppleScript's text item delimiters to ""
                        
                        set end of contactsList to (personName & ":" & phoneString)
                    end if
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to contactsList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            contacts_data = result['result']
            if contacts_data.startswith("Error:"):
                logger.error(f"Contacts error: {contacts_data}")
                return {}
            
            # Parse the contacts data
            contacts_dict = {}
            if contacts_data:
                for contact_entry in contacts_data.split(";"):
                    if ":" in contact_entry:
                        name, phones = contact_entry.split(":", 1)
                        phone_list = phones.split("|") if phones else []
                        contacts_dict[name] = phone_list
                        
            return contacts_dict
        else:
            logger.error(f"Failed to get all contacts: {result.get('error')}")
            return {} 