"""
Apple Mail integration

Provides functionality to read, search, and send emails using the macOS Mail app.
"""

import logging
from typing import Dict, List, Any, Optional
from .applescript import applescript

logger = logging.getLogger(__name__)

class MailHandler:
    """Handler for Apple Mail app integration."""
    
    def __init__(self):
        """Initialize the mail handler."""
        self.app_name = "Mail"
    
    def get_unread_emails(self, account: Optional[str] = None, mailbox: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get unread emails from the specified account and mailbox.
        
        Args:
            account: Email account to search (optional)
            mailbox: Mailbox to search (optional, defaults to inbox)
            limit: Maximum number of emails to return
            
        Returns:
            List of dictionaries containing email information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return []
        
        # Build the AppleScript based on parameters
        if account and mailbox:
            target_clause = f'mailbox "{mailbox}" of account "{account}"'
        elif account:
            target_clause = f'inbox of account "{account}"'
        elif mailbox:
            target_clause = f'mailbox "{mailbox}"'
        else:
            target_clause = 'inbox'
        
        script = f'''
        tell application "Mail"
            set emailsList to {{}}
            set emailLimit to {limit}
            
            try
                set targetMailbox to {target_clause}
                set unreadMessages to (every message of targetMailbox whose read status is false)
                
                set messageCount to count of unreadMessages
                if messageCount > emailLimit then
                    set messagesToProcess to items 1 thru emailLimit of unreadMessages
                else
                    set messagesToProcess to unreadMessages
                end if
                
                repeat with aMessage in messagesToProcess
                    set messageSender to sender of aMessage
                    set messageSubject to subject of aMessage
                    set messageDate to date received of aMessage
                    set messageContent to content of aMessage
                    
                    set messageInfo to (messageSender & "|" & messageSubject & "|" & (messageDate as string) & "|" & messageContent)
                    set end of emailsList to messageInfo
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to emailsList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            emails_data = result['result']
            if emails_data.startswith("Error:"):
                logger.error(f"Mail error: {emails_data}")
                return []
            
            # Parse the emails data
            emails_list = []
            if emails_data:
                for email_entry in emails_data.split(";"):
                    if "|" in email_entry:
                        parts = email_entry.split("|", 3)
                        if len(parts) >= 4:
                            sender, subject, date_str, content = parts
                            emails_list.append({
                                "sender": sender,
                                "subject": subject,
                                "date": date_str,
                                "content": content[:200] + "..." if len(content) > 200 else content
                            })
                        
            return emails_list
        else:
            logger.error(f"Failed to get unread emails: {result.get('error')}")
            return []
    
    def search_emails(self, search_term: str, account: Optional[str] = None, mailbox: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search for emails containing the specified term.
        
        Args:
            search_term: Text to search for in emails
            account: Email account to search (optional)
            mailbox: Mailbox to search (optional)
            limit: Maximum number of emails to return
            
        Returns:
            List of dictionaries containing email information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Mail app")
            return []
        
        # Build the AppleScript based on parameters
        if account and mailbox:
            target_clause = f'mailbox "{mailbox}" of account "{account}"'
        elif account:
            target_clause = f'account "{account}"'
        else:
            target_clause = 'every mailbox'
        
        script = f'''
        tell application "Mail"
            set emailsList to {{}}
            set emailLimit to {limit}
            set searchTerm to "{search_term}"
            set emailCount to 0
            
            try
                if "{account}" is not "" and "{mailbox}" is not "" then
                    set targetMessages to (every message of {target_clause} whose (subject contains searchTerm) or (content contains searchTerm))
                else if "{account}" is not "" then
                    set targetMessages to {{}}
                    repeat with aMailbox in mailboxes of {target_clause}
                        set mailboxMessages to (every message of aMailbox whose (subject contains searchTerm) or (content contains searchTerm))
                        set targetMessages to targetMessages & mailboxMessages
                    end repeat
                else
                    set targetMessages to {{}}
                    repeat with anAccount in accounts
                        repeat with aMailbox in mailboxes of anAccount
                            set mailboxMessages to (every message of aMailbox whose (subject contains searchTerm) or (content contains searchTerm))
                            set targetMessages to targetMessages & mailboxMessages
                        end repeat
                    end repeat
                end if
                
                repeat with aMessage in targetMessages
                    if emailCount >= emailLimit then exit repeat
                    
                    set messageSender to sender of aMessage
                    set messageSubject to subject of aMessage
                    set messageDate to date received of aMessage
                    set messageContent to content of aMessage
                    
                    set messageInfo to (messageSender & "|" & messageSubject & "|" & (messageDate as string) & "|" & messageContent)
                    set end of emailsList to messageInfo
                    set emailCount to emailCount + 1
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to emailsList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            emails_data = result['result']
            if emails_data.startswith("Error:"):
                logger.error(f"Mail search error: {emails_data}")
                return []
            
            # Parse the emails data
            emails_list = []
            if emails_data:
                for email_entry in emails_data.split(";"):
                    if "|" in email_entry:
                        parts = email_entry.split("|", 3)
                        if len(parts) >= 4:
                            sender, subject, date_str, content = parts
                            emails_list.append({
                                "sender": sender,
                                "subject": subject,
                                "date": date_str,
                                "content": content[:200] + "..." if len(content) > 200 else content
                            })
                        
            return emails_list
        else:
            logger.error(f"Failed to search emails: {result.get('error')}")
            return []
    
    def send_email(self, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Escape quotes in the content
        safe_to = to.replace('"', '\\"')
        safe_subject = subject.replace('"', '\\"')
        safe_body = body.replace('"', '\\"')
        safe_cc = cc.replace('"', '\\"') if cc else ""
        safe_bcc = bcc.replace('"', '\\"') if bcc else ""
        
        # Build CC and BCC clauses
        cc_clause = f'set cc recipients to "{safe_cc}"' if cc else ""
        bcc_clause = f'set bcc recipients to "{safe_bcc}"' if bcc else ""
        
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
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": "Email sent successfully"}
            else:
                logger.error(f"Mail send error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to send email: {result.get('error')}")
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
            target_clause = f'account "{account}"'
        else:
            target_clause = 'every account'
        
        script = f'''
        tell application "Mail"
            set mailboxList to {{}}
            
            try
                if "{account}" is not "" then
                    repeat with aMailbox in mailboxes of {target_clause}
                        set end of mailboxList to name of aMailbox
                    end repeat
                else
                    repeat with anAccount in accounts
                        repeat with aMailbox in mailboxes of anAccount
                            set end of mailboxList to ((name of anAccount) & ": " & (name of aMailbox))
                        end repeat
                    end repeat
                end if
                
                set AppleScript's text item delimiters to ", "
                set resultString to mailboxList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            mailboxes_data = result['result']
            if mailboxes_data.startswith("Error:"):
                logger.error(f"Mail mailboxes error: {mailboxes_data}")
                return []
            
            return mailboxes_data.split(", ") if mailboxes_data else []
        else:
            logger.error(f"Failed to list mailboxes: {result.get('error')}")
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
            set accountList to {}
            
            try
                repeat with anAccount in accounts
                    set end of accountList to name of anAccount
                end repeat
                
                set AppleScript's text item delimiters to ", "
                set resultString to accountList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            accounts_data = result['result']
            if accounts_data.startswith("Error:"):
                logger.error(f"Mail accounts error: {accounts_data}")
                return []
            
            return accounts_data.split(", ") if accounts_data else []
        else:
            logger.error(f"Failed to list accounts: {result.get('error')}")
            return [] 