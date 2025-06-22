"""
Apple Contacts integration

Provides functionality to search and retrieve contacts from the macOS Contacts app.
"""

import logging
from typing import Any, Dict, List
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
        if result["success"] and result["result"]:
            # Parse the returned phone numbers
            phone_data = result["result"]
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
    
    def add_contact(
        self,
        first_name: str,
        last_name: str = "",
        phone: str = "",
        email: str = "",
    ) -> Dict[str, Any]:
        """
        Add a new contact to the Contacts app.
        
        Args:
            first_name: First name of the contact (required)
            last_name: Last name of the contact (optional)
            phone: Phone number (optional)
            email: Email address (optional)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Contacts app")
            return {"success": False, "message": "Cannot access Contacts app"}
        
        if not first_name.strip():
            return {"success": False, "message": "First name is required"}
        
        # Build the contact creation script
        script_parts = [
            'tell application "Contacts"',
            '    try',
            f'        set newPerson to make new person with properties {{first name:"{first_name.strip()}"'
        ]
        
        if last_name.strip():
            script_parts[-1] += f', last name:"{last_name.strip()}"'
        
        script_parts[-1] += '}'
        
        # Add phone number if provided
        if phone.strip():
            script_parts.extend([
                f'        make new phone at end of phones of newPerson with properties '
                f'{{label:"mobile", value:"{phone.strip()}"}}'
            ])
        
        # Add email if provided
        if email.strip():
            script_parts.extend([
                f'        make new email at end of emails of newPerson with properties '
                f'{{label:"home", value:"{email.strip()}"}}'
            ])
        
        script_parts.extend([
            '        save',
            f'        return "Success: Added contact " & first name of newPerson '
            f'& " " & last name of newPerson',
            '    on error errMsg',
            '        return "Error: " & errMsg',
            '    end try',
            'end tell'
        ])
        
        script = '\n'.join(script_parts)
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                logger.info(f"Contact added successfully: {first_name} {last_name}")
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Failed to add contact: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to add contact: {result.get('error')}")
            return {"success": False, "message": f"Failed to add contact: {result.get('error')}"}
    
    def delete_contact(self, name: str) -> Dict[str, Any]:
        """
        Delete a contact from the Contacts app.
        
        Args:
            name: Name of the contact to delete (can be partial)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Contacts app")
            return {"success": False, "message": "Cannot access Contacts app"}
        
        if not name.strip():
            return {"success": False, "message": "Contact name is required"}
        
        script = f'''
        tell application "Contacts"
            try
                set foundPeople to (every person whose name contains "{name.strip()}")
                
                if length of foundPeople = 0 then
                    return "Error: No contacts found matching '{name.strip()}'"
                else if length of foundPeople > 1 then
                    set nameList to {{}}
                    repeat with aPerson in foundPeople
                        set end of nameList to name of aPerson
                    end repeat
                    set AppleScript's text item delimiters to ", "
                    set nameString to nameList as string
                    set AppleScript's text item delimiters to ""
                    return "Error: Multiple contacts found: " & nameString & ". Please be more specific."
                else
                    set targetPerson to item 1 of foundPeople
                    set personName to name of targetPerson
                    delete targetPerson
                    save
                    return "Success: Deleted contact " & personName
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
                logger.info(f"Contact deleted successfully: {name}")
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Failed to delete contact: {result_msg}")
                return {"success": False, "message": result_msg.replace("Error: ", "")}
        else:
            logger.error(f"Failed to delete contact: {result.get('error')}")
            return {"success": False, "message": f"Failed to delete contact: {result.get('error')}"}
 