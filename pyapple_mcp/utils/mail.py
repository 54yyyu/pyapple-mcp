"""
Apple Mail integration

Provides functionality to read, search, and send emails using local Mail database.
Optimized for performance by accessing SQLite database directly.
"""

import logging
import sqlite3
import re
import email
import email.policy
from email.header import decode_header
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from .applescript import applescript

logger = logging.getLogger(__name__)

class MailHandler:
    """Handler for Apple Mail app integration using local database access."""
    
    def __init__(self, mail_dir: Optional[str] = None):
        """Initialize the mail handler."""
        self.app_name = "Mail"
        self.mail_dir = Path(mail_dir) if mail_dir else Path.home() / "Library" / "Mail"
        self.envelope_db = self.mail_dir / "V10" / "MailData" / "Envelope Index"
    
    def _get_emails_from_db(
        self,
        limit: int = 20,
        content_length: int = 500,
        unread_only: bool = False,
        search_term: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Retrieve emails from the local Mail database.

        Args:
            limit: Maximum number of emails to return
            content_length: Maximum content length per email
            unread_only: If True, only return unread emails
            search_term: If provided, search for this term in emails

        Returns:
            List of email dictionaries
        """
        if not self.envelope_db.exists():
            logger.error(f"Mail database not found at {self.envelope_db}")
            return []
        
        emails = []
        
        try:
            conn = sqlite3.connect(str(self.envelope_db))
            cursor = conn.cursor()
            
            # Build the query with proper joins - include display name
            query = """
            SELECT
                m.ROWID,
                COALESCE(addr.address, 'Unknown Sender') as sender_address,
                COALESCE(addr.comment, '') as sender_comment,
                COALESCE(subj.subject, 'No Subject') as subject,
                m.date_received,
                COALESCE(mb.url, 'Unknown Mailbox') as mailbox,
                m.read
            FROM messages m
            LEFT JOIN addresses addr ON m.sender = addr.ROWID
            LEFT JOIN subjects subj ON m.subject = subj.ROWID
            LEFT JOIN mailboxes mb ON m.mailbox = mb.ROWID
            WHERE m.deleted = 0
            """
            
            # Add unread filter if needed
            if unread_only:
                query += " AND m.read = 0"
            
            query += " ORDER BY m.date_received DESC LIMIT ?"
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            for row in rows:
                message_id, sender_address, sender_comment, subject, date_received, mailbox, read_status = row
                
                # Combine sender address and comment to create full sender info
                if sender_comment and sender_comment.strip():
                    # If there's a comment (display name), combine it with address
                    sender = f"{sender_comment} <{sender_address}>" if sender_address != 'Unknown Sender' else sender_comment
                else:
                    # Just use the address
                    sender = sender_address
                
                # Decode headers
                sender = self._decode_mime_header(sender) if sender else "Unknown Sender"
                subject = self._decode_mime_header(subject) if subject else "No Subject"
                
                # Convert date
                date_str = "Unknown Date"
                if date_received:
                    try:
                        # Mail uses Core Data timestamp (seconds since 2001-01-01)
                        date_str = datetime.fromtimestamp(date_received + 978307200).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        date_str = "Unknown Date"
                
                # Clean up mailbox name
                if mailbox and mailbox != 'Unknown Mailbox':
                    # Extract meaningful mailbox name from URL
                    mailbox_name = mailbox.split('/')[-1].replace('.mbox', '') if '/' in mailbox else mailbox
                    # URL decode the mailbox name
                    mailbox_name = mailbox_name.replace('%20', ' ')
                else:
                    mailbox_name = "Unknown Mailbox"
                
                # Get content only when needed to avoid performance issues
                content = ""
                if search_term:
                    # For search, don't fetch content initially for performance
                    content = ""
                else:
                    # For non-search operations, get content
                    content = self._get_searchable_content(cursor, message_id, content_length)
                
                email_data = {
                    'id': message_id,
                    'sender': sender,
                    'subject': subject,
                    'date': date_str,
                    'mailbox': mailbox_name,
                    'content': content,
                    'read': bool(read_status)
                }
                
                # If searching, filter by search term
                if search_term:
                    if self._matches_search_term(email_data, search_term):
                        emails.append(email_data)
                else:
                    emails.append(email_data)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []
        
        return emails
    
    def _get_searchable_content_for_message(self, message_id: int, content_length: int) -> str:
        """Get content for a specific message ID (used after search)."""
        try:
            conn = sqlite3.connect(str(self.envelope_db))
            cursor = conn.cursor()
            content = self._get_searchable_content(cursor, message_id, content_length)
            conn.close()
            return content
        except Exception as e:
            logger.debug(f"Error getting content for message {message_id}: {e}")
            return ""
    
    def _get_searchable_content(self, cursor, message_id: int, content_length: int) -> str:
        """Try to get content from .emlx files efficiently."""
        content = ""
        
        # Try to find the .emlx file for this message
        try:
            # Look for .emlx files in account directories  
            v10_dir = self.mail_dir / "V10"
            
            # Search for the .emlx file with the message ID
            # Use a more efficient search with early exit
            for account_dir in v10_dir.iterdir():
                if account_dir.is_dir() and not account_dir.name.startswith('.') and account_dir.name != "MailData":
                    # Look for the specific .emlx file in Messages directories
                    try:
                        for messages_dir in account_dir.rglob("Messages"):
                            if messages_dir.is_dir():
                                emlx_file = messages_dir / f"{message_id}.emlx"
                                if emlx_file.exists():
                                    content = self._parse_emlx_file(emlx_file)
                                    if content:
                                        return content[:content_length] + "..." if len(content) > content_length else content
                    except Exception as e:
                        logger.debug(f"Error searching in {account_dir}: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Error reading .emlx file for message {message_id}: {e}")
        
        # If no content found, return empty string (don't use slow AppleScript)
        return ""
    
    def _parse_emlx_file(self, emlx_path: Path) -> str:
        """Parse a .emlx file and extract text content."""
        try:
            with open(emlx_path, 'rb') as f:
                # First line contains the byte count
                f.readline()
                email_data = f.read()
            
            msg = email.message_from_bytes(email_data, policy=email.policy.default)
            return self._extract_text_content(msg)
            
        except Exception as e:
            logger.debug(f"Error parsing .emlx file {emlx_path}: {e}")
            return ""
    
    def _extract_text_content(self, msg):
        """Extract text content from email message."""
        content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            content += payload.decode('utf-8', errors='ignore')
                        except:
                            content += str(payload)
                elif part.get_content_type() == "text/html" and not content:
                    # Fallback to HTML if no plain text
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            html_content = payload.decode('utf-8', errors='ignore')
                            # Simple HTML tag removal
                            content += re.sub(r'<[^>]+>', '', html_content)
                        except:
                            pass
        else:
            if msg.get_content_type() == "text/plain":
                payload = msg.get_payload(decode=True)
                if payload:
                    try:
                        content += payload.decode('utf-8', errors='ignore')
                    except:
                        content += str(payload)
        
        return content.strip()
    
    def _decode_mime_header(self, header_value: str) -> str:
        """Decode MIME encoded headers."""
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string
        except Exception:
            return str(header_value)
    
    def _matches_search_term_quick(self, email_data: Dict[str, str], search_term: str) -> bool:
        """Quick check if email matches search term in sender/subject only (no content)."""
        search_term_lower = search_term.lower()
        
        # Search only in sender and subject for quick check
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        
        return search_term_lower in sender or search_term_lower in subject
    
    def _matches_search_term(self, email_data: Dict[str, str], search_term: str) -> bool:
        """Check if email matches the search term (case insensitive)."""
        search_term_lower = search_term.lower()
        
        # Search in sender, subject, and content
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        content = email_data.get('content', '').lower()
        
        # Check each field
        if search_term_lower in sender or search_term_lower in subject or search_term_lower in content:
            return True
        
        return False
    
    def mark_as_read(self, message_ids: List[int]) -> Dict[str, Any]:
        """
        Mark emails as read using AppleScript.
        
        Args:
            message_ids: List of message IDs to mark as read
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return {"success": False, "message": "Cannot access Mail app"}
        
        if not message_ids:
            return {"success": True, "message": "No emails to mark as read"}
        
        # Convert message IDs to string for AppleScript
        ids_string = ",".join(str(id) for id in message_ids)
        
        script = f'''
        tell application "Mail"
            try
                set messageIds to {{{ids_string}}}
                set markedCount to 0
                
                repeat with messageId in messageIds
                    try
                        -- Find the message by ID across all mailboxes
                        repeat with anAccount in accounts
                            repeat with aMailbox in mailboxes of anAccount
                                try
                                    repeat with aMessage in messages of aMailbox
                                        if (id of aMessage as string) is equal to (messageId as string) then
                                            set read status of aMessage to true
                                            set markedCount to markedCount + 1
                                            exit repeat
                                        end if
                                    end repeat
                                on error
                                    -- Skip problematic messages
                                end try
                            end repeat
                        end repeat
                    on error
                        -- Skip problematic message IDs
                    end try
                end repeat
                
                return "Success: Marked " & markedCount & " emails as read"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            if result['result'].startswith("Success:"):
                return {"success": True, "message": result['result']}
            else:
                return {"success": False, "message": result['result']}
        else:
            return {"success": False, "message": f"Failed to mark emails as read: {result.get('error')}"}
    
    def get_unread_emails(
        self,
        account: Optional[str] = None,
        mailbox: Optional[str] = None,
        limit: int = 10,
        full_content: bool = False,
        search_range: Optional[int] = None,
        mark_read: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Get unread emails from the local Mail database.
        
        Args:
            account: Email account to search (optional, searches all accounts if not specified)
            mailbox: Mailbox to search (optional, searches all mailboxes if not specified)
            limit: Maximum number of emails to return (default: 10, use -1 for all)
            full_content: If True, return full email content; if False, truncate (default: False)
            search_range: Number of recent messages to search through (optional, ignored for DB method)
            mark_read: If True, mark the retrieved emails as read (default: False)
            
        Returns:
            List of dictionaries containing email information
        """
        # Handle -1 limit (search all)
        actual_limit = 999999 if limit == -1 else limit
        
        # Set content length based on full_content flag
        content_length = 10000 if full_content else 500
        
        # Get unread emails from database
        emails = self._get_emails_from_db(
            limit=actual_limit, 
            content_length=content_length, 
            unread_only=True
        )
        
        # Filter by account/mailbox if specified
        if account or mailbox:
            filtered_emails = []
            for email in emails:
                include_email = True
                
                if account and account.lower() not in email.get('mailbox', '').lower():
                    # For now, we don't have direct account info in the simplified approach
                    # This could be enhanced by joining with account tables
                    pass
                
                if mailbox and mailbox.lower() not in email.get('mailbox', '').lower():
                    include_email = False
                
                if include_email:
                    filtered_emails.append(email)
            
            emails = filtered_emails
        
        # Mark as read if requested
        if mark_read and emails:
            message_ids = [email['id'] for email in emails]
            mark_result = self.mark_as_read(message_ids)
            if mark_result['success']:
                logger.info(f"Marked {len(message_ids)} emails as read")
            else:
                logger.error(f"Failed to mark emails as read: {mark_result['message']}")
        
        return emails
    
    def search_emails(
        self,
        search_term: str,
        account: Optional[str] = None,
        mailbox: Optional[str] = None,
        limit: int = 10,
        full_content: bool = False,
        search_range: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Search for emails containing the specified term using the local Mail database.
        
        Args:
            search_term: Text to search for in emails (case insensitive)
            account: Email account to search (optional, searches all accounts if not specified)
            mailbox: Mailbox to search (optional, searches all mailboxes if not specified)
            limit: Maximum number of emails to return (default: 10, use -1 for all)
            full_content: If True, return full email content; if False, truncate (default: False)
            search_range: Number of recent messages to search through (optional, ignored for DB method)
            
        Returns:
            List of dictionaries containing email information
        """
        # Handle -1 limit (search all)
        actual_limit = 999999 if limit == -1 else limit
        
        # Set content length based on full_content flag
        content_length = 10000 if full_content else 500
        
        # For search, we need to look through many more emails than the limit
        # to find matches, especially if the search term is rare
        search_through_count = 5000  # Search through 5000 recent emails to find matches
        
        # Search emails using database
        emails = self._get_emails_from_db(
            limit=search_through_count,  # Search through many more emails
            content_length=content_length,
            unread_only=False,
            search_term=search_term
        )
        
        # Now get content for matched emails if full_content is requested
        if full_content:
            for email in emails:
                if not email['content']:  # Only get content if not already retrieved
                    email['content'] = self._get_searchable_content_for_message(email['id'], content_length)
        
        # Filter by account/mailbox if specified
        if account or mailbox:
            filtered_emails = []
            for email in emails:
                include_email = True
                
                if account and account.lower() not in email.get('mailbox', '').lower():
                    # For now, we don't have direct account info in the simplified approach
                    # This could be enhanced by joining with account tables
                    pass
                
                if mailbox and mailbox.lower() not in email.get('mailbox', '').lower():
                    include_email = False
                
                if include_email:
                    filtered_emails.append(email)
            
            emails = filtered_emails
        
        # Limit results
        return emails[:actual_limit] if actual_limit != 999999 else emails
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email to the specified recipient(s).
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC email address (optional)
            bcc: BCC email address (optional)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return {"success": False, "message": "Cannot access Mail app"}
        
        # Escape quotes and special characters
        safe_to = to.replace('"', '\\"').replace("'", "\\'")
        safe_subject = subject.replace('"', '\\"').replace("'", "\\'")
        safe_body = body.replace('"', '\\"').replace("'", "\\'")
        safe_cc = cc.replace('"', '\\"').replace("'", "\\'") if cc else ""
        safe_bcc = bcc.replace('"', '\\"').replace("'", "\\'") if bcc else ""
        
        # Build CC and BCC clauses
        cc_clause = f'make new cc recipient with properties {{address:"{safe_cc}"}}' if cc else ""
        bcc_clause = f'make new bcc recipient with properties {{address:"{safe_bcc}"}}' if bcc else ""
        
        script = f'''
        tell application "Mail"
            try
                set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}"}}
                
                tell newMessage
                    make new to recipient with properties {{address:"{safe_to}"}}
                    {cc_clause}
                    {bcc_clause}
                end tell
                
                send newMessage
                return "Success: Email sent"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            if result['result'].startswith("Success:"):
                return {"success": True, "message": "Email sent successfully"}
            else:
                return {"success": False, "message": result['result']}
        else:
            return {"success": False, "message": f"Failed to send email: {result.get('error')}"}
    
    def list_mailboxes(self, account: Optional[str] = None) -> List[str]:
        """
        List available mailboxes for the specified account.
        
        Args:
            account: Email account to list mailboxes for (optional)
            
        Returns:
            List of mailbox names
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return []
        
        if account:
            script = f'''
            tell application "Mail"
                try
                    set targetAccount to account "{account}"
                    set mailboxNames to name of every mailbox of targetAccount
                    set AppleScript's text item delimiters to "|||"
                    set resultString to mailboxNames as string
                    set AppleScript's text item delimiters to ""
                    return resultString
                on error errMsg number errNum
                    return "Error " & errNum & ": " & errMsg
                end try
            end tell
            '''
        else:
            script = '''
            tell application "Mail"
                try
                    set mailboxList to {}
                    repeat with anAccount in accounts
                        set accountName to name of anAccount as string
                        repeat with aMailbox in mailboxes of anAccount
                            set mailboxName to name of aMailbox as string
                            set end of mailboxList to accountName & ": " & mailboxName
                        end repeat
                    end repeat
                    set AppleScript's text item delimiters to "|||"
                    set resultString to mailboxList as string
                    set AppleScript's text item delimiters to ""
                    return resultString
                on error errMsg number errNum
                    return "Error " & errNum & ": " & errMsg
                end try
            end tell
            '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result'] and not result['result'].startswith("Error"):
            return result['result'].split("|||") if result['result'] else []
        else:
            logger.error(f"Failed to list mailboxes: {result.get('result', result.get('error'))}")
            return []
    
    def list_accounts(self) -> List[str]:
        """
        List available email accounts.
        
        Returns:
            List of account names
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return []
        
        script = '''
        tell application "Mail"
            try
                set accountNames to name of every account
                set AppleScript's text item delimiters to "|||"
                set resultString to accountNames as string
                set AppleScript's text item delimiters to ""
                return resultString
            on error errMsg number errNum
                return "Error " & errNum & ": " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result'] and not result['result'].startswith("Error"):
            return result['result'].split("|||") if result['result'] else []
        else:
            logger.error(f"Failed to list accounts: {result.get('result', result.get('error'))}")
            return []
