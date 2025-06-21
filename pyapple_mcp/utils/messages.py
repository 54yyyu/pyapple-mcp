"""
Apple Messages integration

Provides functionality to send and read messages using the macOS Messages app.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from .applescript import applescript

logger = logging.getLogger(__name__)

class MessagesHandler:
    """Handler for Apple Messages app integration."""
    
    def __init__(self):
        """Initialize the messages handler."""
        self.app_name = "Messages"
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send a message to the specified phone number.
        
        Args:
            phone_number: Phone number to send message to
            message: Message content to send
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Messages app")
            return {"success": False, "message": "Cannot access Messages app"}
        
        # Escape quotes in the message
        safe_message = message.replace('"', '\\"')
        safe_phone = phone_number.replace('"', '\\"')
        
        script = f'''
        tell application "Messages"
            try
                set targetBuddy to buddy "{safe_phone}"
                send "{safe_message}" to targetBuddy
                return "Success: Message sent"
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": "Message sent successfully"}
            else:
                logger.error(f"Messages send error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to send message: {result.get('error')}")
            return {"success": False, "message": f"Failed to send message: {result.get('error')}"}
    
    def read_messages(self, phone_number: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Read recent messages from a conversation.
        
        Args:
            phone_number: Phone number to read messages from
            limit: Number of recent messages to retrieve
            
        Returns:
            List of dictionaries containing message information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Messages app")
            return []
        
        script = f'''
        tell application "Messages"
            set messagesList to {{}}
            set targetNumber to "{phone_number}"
            set messageLimit to {limit}
            
            try
                set targetChat to null
                
                -- Find the chat for this phone number
                repeat with aChat in chats
                    repeat with aBuddy in participants of aChat
                        if id of aBuddy contains targetNumber then
                            set targetChat to aChat
                            exit repeat
                        end if
                    end repeat
                    if targetChat is not null then exit repeat
                end repeat
                
                if targetChat is not null then
                    set recentMessages to (items 1 thru (count of texts of targetChat)) of texts of targetChat
                    if (count of recentMessages) > messageLimit then
                        set recentMessages to items 1 thru messageLimit of recentMessages
                    end if
                    
                    repeat with aMessage in recentMessages
                        set messageText to text of aMessage
                        set messageDate to time sent of aMessage
                        set messageSender to handle of sender of aMessage
                        
                        set messageInfo to (messageSender & "|" & messageText & "|" & (messageDate as string))
                        set end of messagesList to messageInfo
                    end repeat
                end if
                
                set AppleScript's text item delimiters to ";"
                set resultString to messagesList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            messages_data = result['result']
            if messages_data.startswith("Error:"):
                logger.error(f"Messages read error: {messages_data}")
                return []
            
            # Parse the messages data
            messages_list = []
            if messages_data:
                for message_entry in messages_data.split(";"):
                    if "|" in message_entry:
                        parts = message_entry.split("|", 2)
                        if len(parts) >= 3:
                            sender, content, time_str = parts
                            messages_list.append({
                                "sender": sender,
                                "content": content,
                                "time": time_str
                            })
                        
            return messages_list
        else:
            logger.error(f"Failed to read messages: {result.get('error')}")
            return []
    
    def schedule_message(self, phone_number: str, message: str, scheduled_time: str) -> Dict[str, Any]:
        """
        Schedule a message to be sent at a specific time.
        Note: This is a placeholder implementation as Messages doesn't natively support scheduling.
        
        Args:
            phone_number: Phone number to send message to
            message: Message content to send
            scheduled_time: ISO format time string for when to send
            
        Returns:
            Dictionary with success status and message
        """
        # For now, we'll just indicate that scheduling isn't supported natively
        return {
            "success": False, 
            "message": "Message scheduling is not natively supported by Apple Messages. Consider using a third-party automation tool."
        }
    
    def get_unread_count(self) -> int:
        """
        Get the count of unread messages across all conversations.
        
        Returns:
            Number of unread messages
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Messages app")
            return 0
        
        script = '''
        tell application "Messages"
            set unreadCount to 0
            
            try
                repeat with aChat in chats
                    set unreadCount to unreadCount + (unread count of aChat)
                end repeat
                
                return unreadCount as string
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            count_data = result['result']
            if count_data.startswith("Error:"):
                logger.error(f"Messages unread count error: {count_data}")
                return 0
            
            try:
                return int(count_data)
            except ValueError:
                logger.error(f"Invalid unread count: {count_data}")
                return 0
        else:
            logger.error(f"Failed to get unread count: {result.get('error')}")
            return 0 