"""
Apple Messages integration

Provides functionality to send and read messages using the macOS Messages app.
Uses direct database access for reading and AppleScript for sending.
Based on working iMessage script implementation.
"""

import logging
import sqlite3
import os
import re
from typing import Any, Dict, List
from datetime import datetime
from .applescript import applescript

logger = logging.getLogger(__name__)

class MessagesHandler:
    """Handler for Apple Messages app integration."""
    
    def __init__(self):
        """Initialize the messages handler."""
        self.app_name = "Messages"
        self.messages_db_path = os.path.expanduser(
            "~/Library/Messages/chat.db"
        )
    
    def check_database_access(self) -> bool:
        """Check if we can access the Messages database"""
        try:
            if not os.path.exists(self.messages_db_path):
                print("❌ Messages database not found at:", self.messages_db_path)
                logger.error(f"Messages database not found at: {self.messages_db_path}")
                return False
            
            # Try to open and query the database
            conn = sqlite3.connect(self.messages_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"""
❌ Error: Cannot access Messages database.
To fix this, please grant Full Disk Access to Terminal/iTerm2:
1. Open System Preferences/Settings
2. Go to Security & Privacy > Privacy (or Privacy & Security)
3. Select "Full Disk Access" from the left sidebar  
4. Click the lock icon to make changes
5. Add Terminal.app or iTerm.app to the list
6. Restart your terminal and try again

Error details: {e}
""")
            logger.error(f"Cannot access Messages database. Full Disk Access may be required: {e}")
            return False
    
    def normalize_contact(self, contact: str) -> List[str]:
        """
        Normalize contact (phone/email) to multiple possible formats
        Returns list of possible formats to try
        """
        # If it's an email, add it as-is and return
        if '@' in contact:
            return [contact]
        
        # Phone number normalization
        # Remove all non-numeric characters except +
        cleaned = re.sub(r'[^0-9+]', '', contact)
        
        formats = set()
        
        # If it's already in the correct format (+1XXXXXXXXXX)
        if re.match(r'^\+1\d{10}$', cleaned):
            formats.add(cleaned)
        
        # If it starts with 1 and has 11 digits total
        elif re.match(r'^1\d{10}$', cleaned):
            formats.add(f"+{cleaned}")
        
        # If it's 10 digits
        elif re.match(r'^\d{10}$', cleaned):
            formats.add(f"+1{cleaned}")
        
        # Try additional formats
        if cleaned.startswith('+1'):
            formats.add(cleaned)
        elif cleaned.startswith('1'):
            formats.add(f"+{cleaned}")
        else:
            formats.add(f"+1{cleaned}")
        
        # Also try the original format
        formats.add(contact)
        
        return list(formats)
    
    def decode_attributed_body(self, hex_string: str) -> Dict[str, Any]:
        """
        Decode attributedBody hex data to extract text and URLs
        """
        try:
            # Convert hex to bytes then to string
            bytes_data = bytes.fromhex(hex_string)
            content = bytes_data.decode('utf-8', errors='ignore')
            
            # Patterns to extract text content
            patterns = [
                r'NSString">([^<]+)',           # Basic NSString pattern  
                r'NSString">([^<]+)</.*?',      # NSString with closing
                r'NSNumber">\d+<.*?NSString">([^<]+)',  # NSNumber followed by NSString
                r'NSArray">.*?NSString">([^<]+)',       # NSString within NSArray
                r'"string":\s*"([^"]+)"',       # JSON-style string
                r'text[^>]*>([^<]+)',          # Generic XML-style text
                r'message>([^<]+)'             # Generic message content
            ]
            
            text = ''
            for pattern in patterns:
                match = re.search(pattern, content)
                if match and len(match.group(1)) > 5:
                    text = match.group(1)
                    break
            
            # Look for URLs
            url_patterns = [
                r'(https?://[^\s<"]+)',           # Standard URLs
                r'NSString">(https?://[^\s<"]+)', # URLs in NSString  
                r'"url":\s*"(https?://[^"]+)"',   # URLs in JSON format
                r'link[^>]*>(https?://[^<]+)'     # URLs in XML-style tags
            ]
            
            url = None
            for pattern in url_patterns:
                match = re.search(pattern, content)
                if match:
                    url = match.group(1)
                    break
            
            if not text and not url:
                # Try to extract any readable text
                readable = re.sub(r'streamtyped.*?NSString', '', content)
                readable = re.sub(r'NSAttributedString.*?NSString', '', readable)
                readable = re.sub(r'NSDictionary.*?$', '', readable)
                readable = re.sub(r'\+[A-Za-z]+\s', '', readable)
                readable = re.sub(r'NSNumber.*?NSValue.*?\*', '', readable)
                readable = re.sub(r'[^\x20-\x7E]', ' ', readable)  # Replace non-printable
                readable = re.sub(r'\s+', ' ', readable).strip()
                
                if len(readable) > 5:
                    text = readable
                else:
                    text = '[Message content not readable]'
            
            # Clean up text
            if text:
                text = re.sub(r'^[+\s]+', '', text)  # Remove leading + and spaces
                text = re.sub(r'\s*iI\s*[A-Z]\s*$', '', text)  # Remove iI K pattern
                text = re.sub(r'\s+', ' ', text).strip()
            
            return {'text': text or url or '', 'url': url}
            
        except Exception as e:
            logger.warning(f"Error decoding attributedBody: {e}")
            return {'text': '[Message content not readable]', 'url': None}
    
    def get_attachment_paths(self, message_id: int) -> List[str]:
        """Get attachment file paths for a message"""
        try:
            conn = sqlite3.connect(self.messages_db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT filename
                FROM attachment
                INNER JOIN message_attachment_join 
                ON attachment.ROWID = message_attachment_join.attachment_id
                WHERE message_attachment_join.message_id = ?
            """
            
            cursor.execute(query, (message_id,))
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results if row[0]]
            
        except Exception as e:
            logger.warning(f"Error getting attachments: {e}")
            return []
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send a message to the specified phone number or email.
        
        Args:
            phone_number: Phone number or email to send message to
            message: Message content to send
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Escape quotes in the message
            escaped_message = message.replace('"', '\\"').replace("'", "\\'")
            
            applescript_code = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{phone_number}" of targetService
                send "{escaped_message}" to targetBuddy
            end tell
            '''
            
            result = applescript.run_script(applescript_code)
            if result['success']:
                logger.info(f"Message sent to {phone_number}: {message}")
                return {"success": True, "message": "Message sent successfully"}
            else:
                logger.error(f"Failed to send message: {result.get('error')}")
                return {"success": False, "message": f"Failed to send message: {result.get('error')}"}
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"success": False, "message": f"Error sending message: {str(e)}"}
    
    def read_messages(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Read recent messages from a conversation using direct database access.
        
        Args:
            phone_number: Phone number or email to read messages from
            limit: Number of recent messages to retrieve
            
        Returns:
            List of dictionaries containing message information
        """
        try:
            # Check database access first
            if not self.check_database_access():
                logger.error("Cannot access Messages database - falling back to AppleScript")
                return self._read_messages_applescript(phone_number, limit)
            
            # Get all possible contact formats
            contact_formats = self.normalize_contact(phone_number)
            print(f"🔍 Trying contact formats: {contact_formats}")
            logger.info(f"Searching for messages with contact formats: {contact_formats}")
            
            # Create SQL IN clause with all contact formats
            contact_placeholders = ','.join(['?' for _ in contact_formats])
            
            conn = sqlite3.connect(self.messages_db_path)
            cursor = conn.cursor()
            
            query = f"""
                SELECT 
                    m.ROWID as message_id,
                    CASE 
                        WHEN m.text IS NOT NULL AND m.text != '' THEN m.text
                        WHEN m.attributedBody IS NOT NULL THEN hex(m.attributedBody)
                        ELSE NULL
                    END as content,
                    datetime(m.date/1000000000 + strftime('%s', '2001-01-01'), 'unixepoch', 'localtime') as date,
                    h.id as sender,
                    m.is_from_me,
                    m.is_audio_message,
                    m.cache_has_attachments,
                    m.subject,
                    CASE 
                        WHEN m.text IS NOT NULL AND m.text != '' THEN 0
                        WHEN m.attributedBody IS NOT NULL THEN 1
                        ELSE 2
                    END as content_type
                FROM message m 
                INNER JOIN handle h ON h.ROWID = m.handle_id 
                WHERE h.id IN ({contact_placeholders})
                    AND (m.text IS NOT NULL OR m.attributedBody IS NOT NULL OR m.cache_has_attachments = 1)
                    AND m.is_from_me IS NOT NULL
                    AND m.item_type = 0
                    AND m.is_audio_message = 0
                ORDER BY m.date DESC 
                LIMIT ?
            """
            
            cursor.execute(query, contact_formats + [limit])
            messages = cursor.fetchall()
            conn.close()
            
            if not messages:
                print(f"📭 No messages found for {phone_number}")
                logger.info(f"No messages found for {phone_number}")
                return []
            
            # Process messages
            processed_messages = []
            for msg in messages:
                (message_id, content, date, sender, is_from_me, 
                 is_audio_message, cache_has_attachments, subject, content_type) = msg
                
                # Decode content based on type
                if content_type == 1:  # attributedBody
                    decoded = self.decode_attributed_body(content)
                    text_content = decoded['text']
                    url = decoded['url']
                else:
                    text_content = content or ''
                    url_match = re.search(r'(https?://[^\s]+)', text_content)
                    url = url_match.group(1) if url_match else None
                
                # Get attachments
                attachments = []
                if cache_has_attachments:
                    attachments = self.get_attachment_paths(message_id)
                
                # Add subject if present
                if subject:
                    text_content = f"Subject: {subject}\n{text_content}"
                
                # Determine sender display
                sender_display = "You" if is_from_me else sender
                
                # Create message object
                message_obj = {
                    "sender": sender_display,
                    "content": text_content or '[No text content]',
                    "time": date,
                    "is_from_me": bool(is_from_me),
                    "attachments": attachments,
                    "url": url
                }
                
                # Add attachment info to content
                if attachments:
                    message_obj['content'] += f"\n[Attachments: {len(attachments)}]"
                
                # Add URL info to content
                if url:
                    message_obj['content'] += f"\n[URL: {url}]"
                
                processed_messages.append(message_obj)
            
            return processed_messages
            
        except Exception as e:
            logger.error(f"Error reading messages from database: {e}")
            # Fallback to AppleScript method
            return self._read_messages_applescript(phone_number, limit)
    
    def get_unread_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get unread messages from all contacts"""
        try:
            # Check database access
            if not self.check_database_access():
                logger.error("Cannot access Messages database")
                return []
            
            conn = sqlite3.connect(self.messages_db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    m.ROWID as message_id,
                    CASE 
                        WHEN m.text IS NOT NULL AND m.text != '' THEN m.text
                        WHEN m.attributedBody IS NOT NULL THEN hex(m.attributedBody)
                        ELSE NULL
                    END as content,
                    datetime(m.date/1000000000 + strftime('%s', '2001-01-01'), 'unixepoch', 'localtime') as date,
                    h.id as sender,
                    m.is_from_me,
                    m.is_audio_message,
                    m.cache_has_attachments,
                    m.subject,
                    CASE 
                        WHEN m.text IS NOT NULL AND m.text != '' THEN 0
                        WHEN m.attributedBody IS NOT NULL THEN 1
                        ELSE 2
                    END as content_type
                FROM message m 
                INNER JOIN handle h ON h.ROWID = m.handle_id 
                WHERE m.is_from_me = 0
                    AND m.is_read = 0
                    AND (m.text IS NOT NULL OR m.attributedBody IS NOT NULL OR m.cache_has_attachments = 1)
                    AND m.is_audio_message = 0
                    AND m.item_type = 0
                ORDER BY m.date DESC 
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            messages = cursor.fetchall()
            conn.close()
            
            if not messages:
                logger.info("No unread messages found")
                return []
            
            # Process messages (same logic as read_messages)
            processed_messages = []
            for msg in messages:
                (message_id, content, date, sender, is_from_me, 
                 is_audio_message, cache_has_attachments, subject, content_type) = msg
                
                # Decode content based on type
                if content_type == 1:  # attributedBody
                    decoded = self.decode_attributed_body(content)
                    text_content = decoded['text']
                    url = decoded['url']
                else:
                    text_content = content or ''
                    url_match = re.search(r'(https?://[^\s]+)', text_content)
                    url = url_match.group(1) if url_match else None
                
                # Get attachments
                attachments = []
                if cache_has_attachments:
                    attachments = self.get_attachment_paths(message_id)
                
                # Add subject if present
                if subject:
                    text_content = f"Subject: {subject}\n{text_content}"
                
                # Create message object
                message_obj = {
                    'content': text_content or '[No text content]',
                    'date': date,
                    'sender': sender,
                    'is_from_me': bool(is_from_me),
                    'attachments': attachments,
                    'url': url
                }
                
                # Add attachment info to content
                if attachments:
                    message_obj['content'] += f"\n[Attachments: {len(attachments)}]"
                
                # Add URL info to content
                if url:
                    message_obj['content'] += f"\n[URL: {url}]"
                
                processed_messages.append(message_obj)
            
            return processed_messages
            
        except Exception as e:
            logger.error(f"Error reading unread messages: {e}")
            return []
    
    def _read_messages_applescript(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fallback method using AppleScript for reading messages.
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Messages app")
            return []
        
        # Escape quotes in phone number/email
        safe_target = phone_number.replace('"', '\\"')
        
        script = f'''
        tell application "Messages"
            set messagesList to {{}}
            set targetContact to "{safe_target}"
            set messageLimit to {limit}
            
            try
                set targetChat to missing value
                
                -- Search through all chats to find matching conversation
                repeat with aChat in chats
                    -- Check if any participant matches our target
                    repeat with aBuddy in participants of aChat
                        set buddyID to id of aBuddy
                        set buddyHandle to handle of aBuddy
                        
                        -- Check both ID and handle for matches
                        if (buddyID contains targetContact) or (buddyHandle contains targetContact) or (targetContact contains buddyID) or (targetContact contains buddyHandle) then
                            set targetChat to aChat
                            exit repeat
                        end if
                    end repeat
                    if targetChat is not missing value then exit repeat
                end repeat
                
                if targetChat is not missing value then
                    -- Get all texts from the chat
                    set allTexts to texts of targetChat
                    set messageCount to count of allTexts
                    
                    -- Get the most recent messages
                    set startIndex to messageCount - messageLimit + 1
                    if startIndex < 1 then set startIndex to 1
                    
                    set recentMessages to items startIndex thru messageCount of allTexts
                    
                    repeat with aMessage in recentMessages
                        try
                            set messageText to text of aMessage
                            set messageDate to time sent of aMessage
                            
                            -- Handle sender information
                            try
                                set messageSender to handle of sender of aMessage
                            on error
                                try
                                    set messageSender to id of sender of aMessage
                                on error
                                    set messageSender to "Unknown"
                                end try
                            end try
                            
                            set messageInfo to (messageSender & "|" & messageText & "|" & (messageDate as string))
                            set end of messagesList to messageInfo
                        on error
                            -- Skip messages that can't be read
                        end try
                    end repeat
                else
                    return "No chat found for: " & targetContact
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
            elif messages_data.startswith("No chat found"):
                logger.info(f"No conversation found for {phone_number}")
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
                                "time": time_str,
                                "is_from_me": False,
                                "attachments": [],
                                "url": None
                            })
                        
            return messages_list
        else:
            logger.error(f"Failed to read messages: {result.get('error')}")
            return []
    
    def schedule_message(
        self, phone_number: str, message: str, scheduled_time: str
    ) -> Dict[str, Any]:
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
            "message": (
                "Message scheduling is not natively supported by Apple Messages. "
                "Consider using a third-party automation tool."
            ),
        }
    
    def get_unread_count(self) -> int:
        """
        Get the count of unread messages across all conversations.
        
        Returns:
            Number of unread messages
        """
        try:
            # Try database method first
            if self.check_database_access():
                conn = sqlite3.connect(self.messages_db_path)
                cursor = conn.cursor()
                
                query = """
                    SELECT COUNT(*)
                    FROM message m 
                    WHERE m.is_from_me = 0
                        AND m.is_read = 0
                        AND m.item_type = 0
                """
                
                cursor.execute(query)
                count = cursor.fetchone()[0]
                conn.close()
                
                return count
        except Exception as e:
            logger.warning(f"Database unread count failed, trying AppleScript: {e}")
        
        # Fallback to AppleScript
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
