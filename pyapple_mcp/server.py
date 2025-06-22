#!/usr/bin/env python3
"""
PyApple MCP Server

Main server implementation providing Apple-native tools for the Model Context Protocol.
Supports integration with Messages, Notes, Contacts, Mail, Calendar, Reminders,
Maps, and Web Search.
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Import all tool implementations
from .utils.calendar import CalendarHandler
from .utils.contacts import ContactsHandler
from .utils.mail import MailHandler
from .utils.maps import MapsHandler
from .utils.messages import MessagesHandler
from .utils.notes import NotesHandler
from .utils.reminders import RemindersHandler
from .utils.websearch import WebSearchHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)

# Create the FastMCP server
app = FastMCP(
    "PyApple MCP Tools",
    dependencies=[
        "httpx>=0.25.0",
        "beautifulsoup4>=4.12.0",
        "pyobjc-framework-Cocoa>=10.0",
        "pyobjc-framework-AddressBook>=10.0",
        "pyobjc-framework-EventKit>=10.0",
        "pyobjc-framework-ScriptingBridge>=10.0",
        "pyobjc-framework-MapKit>=10.0",
    ],
)

# Initialize handlers
contacts_handler = ContactsHandler()
notes_handler = NotesHandler()
messages_handler = MessagesHandler()
mail_handler = MailHandler()
reminders_handler = RemindersHandler()
calendar_handler = CalendarHandler()
maps_handler = MapsHandler()
websearch_handler = WebSearchHandler()

# Tool: Contacts
@app.tool()
def contacts(
    operation: str = "search",
    name: str = None,
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    email: str = None,
) -> str:
    """
    Search, add, and manage contacts in Apple Contacts app.

    Args:
        operation: Operation to perform: 'search', 'add', or 'delete' 
            (default: 'search')
        name: Name to search for (optional - if not provided, returns all contacts)
        first_name: First name for new contact (required for add operation)
        last_name: Last name for new contact (optional for add operation)
        phone: Phone number for new contact (optional for add operation)
        email: Email address for new contact (optional for add operation)

    Returns:
        String containing contact information or operation result
    """
    try:
        if operation == "add":
            if not first_name:
                return "First name is required for add operation"

            result = contacts_handler.add_contact(
                first_name, last_name or "", phone or "", email or ""
            )
            if result["success"]:
                contact_info = f"Added contact: {first_name}"
                if last_name:
                    contact_info += f" {last_name}"
                if phone:
                    contact_info += f" (Phone: {phone})"
                if email:
                    contact_info += f" (Email: {email})"
                return contact_info
            else:
                return f"Failed to add contact: {result['message']}"

        elif operation == "delete":
            if not name:
                return "Contact name is required for delete operation"

            result = contacts_handler.delete_contact(name)
            if result["success"]:
                return f"Successfully deleted contact: {result['message']}"
            else:
                return f"Failed to delete contact: {result['message']}"
                
        else:  # Default search operation
            if name:
                numbers = contacts_handler.find_number(name)
                if numbers:
                    return f"{name}: {', '.join(numbers)}"
                else:
                    return (
                        f'No contact found for "{name}". Try a different name or '
                        "use no name parameter to list all contacts."
                    )
            else:
                all_numbers = contacts_handler.get_all_numbers()
                contact_count = len(all_numbers)
                
                if contact_count == 0:
                    return (
                        "No contacts found in the address book. Please make sure you "
                        "have granted access to Contacts."
                    )
                
                # Format contacts for display (limit to first 50 to avoid 
                # overwhelming output)
                contacts_list = []
                for contact_name, phone_numbers in list(all_numbers.items())[:50]:
                    contacts_list.append(
                        f"{contact_name}: {', '.join(phone_numbers)}"
                    )
                
                result = f"Found {contact_count} contacts"
                if contact_count > 50:
                    result += " (showing first 50)"
                result += ":\n\n" + "\n".join(contacts_list)
                
                return result
            
    except Exception as e:
        logger.error(f"Error in contacts tool: {e}")
        return f"Error accessing contacts: {str(e)}"

# Tool: Notes
@app.tool()
def notes(
    operation: str,
    search_text: str = None,
    title: str = None,
    body: str = None,
    folder_name: str = "Claude",
) -> str:
    """
    Search, retrieve, create, and delete notes in Apple Notes app.

    Args:
        operation: Operation to perform: 'search', 'list', 'view', 'create', or 'delete'
        search_text: Text to search for in notes (required for search, view, and delete operations)
        title: Title of the note to create (required for create operation)
        body: Content of the note to create (required for create operation)
        folder_name: Name of the folder to create the note in (optional for create, defaults to 'Claude')

    Returns:
        String containing notes information or operation result
    """
    try:
        if operation == "search":
            if not search_text:
                return "Search text is required for search operation"
            
            results = notes_handler.search_notes(search_text)
            if results:
                formatted_results = []
                for note in results:
                    formatted_results.append(
                        f"Title: {note['title']}\nContent: {note['content'][:200]}..."
                    )
                return (
                    f"Found {len(results)} notes matching '{search_text}':\n\n"
                    + "\n\n".join(formatted_results)
                )
            else:
                return f"No notes found matching '{search_text}'"
                
        elif operation == "view":
            if not search_text:
                return "Note title is required for view operation"
            
            results = notes_handler.search_notes(search_text)
            if results:
                # Find exact title match or closest match
                exact_match = next(
                    (
                        note
                        for note in results
                        if note["title"].lower() == search_text.lower()
                    ),
                    None,
                )
                if exact_match:
                    return (
                        f"Title: {exact_match['title']}\n\n"
                        f"Full Content:\n{exact_match['content']}"
                    )
                else:
                    # Show first match with full content
                    first_match = results[0]
                    return (
                        f"Title: {first_match['title']}\n\n"
                        f"Full Content:\n{first_match['content']}"
                    )
            else:
                return f"No notes found matching '{search_text}'"
                
        elif operation == "list":
            results = notes_handler.list_notes()
            if results:
                formatted_results = []
                for note in results:
                    formatted_results.append(
                        f"Title: {note['title']}\nContent: {note['content'][:100]}..."
                    )
                return (
                    f"Found {len(results)} notes:\n\n" + "\n\n".join(formatted_results)
                )
            else:
                return "No notes found"
                
        elif operation == "create":
            if not title or not body:
                return "Title and body are required for create operation"
            
            result = notes_handler.create_note(title, body, folder_name)
            if result["success"]:
                return f"Successfully created note '{title}' in folder '{folder_name}'"
            else:
                return f"Failed to create note: {result['message']}"

        elif operation == "delete":
            if not search_text:
                return "Search text is required for delete operation"
            
            result = notes_handler.delete_note(search_text)
            if result["success"]:
                return f"Successfully deleted note: {result['message']}"
            else:
                return f"Failed to delete note: {result['message']}"
        else:
            return (
                f"Unknown operation: {operation}. Valid operations are: "
                "search, list, view, create, delete"
            )
            
    except Exception as e:
        logger.error(f"Error in notes tool: {e}")
        return f"Error accessing notes: {str(e)}"

# Tool: Messages
@app.tool()
def messages(
    operation: str,
    phone_number: str = None,
    message: str = None,
    limit: int = 10,
    scheduled_time: str = None,
) -> str:
    """
    Interact with Apple Messages app - send, read, schedule messages and check unread messages.

    Args:
        operation: Operation to perform: 'send', 'read', 'schedule', or 'unread'
        phone_number: Phone number for send, read, and schedule operations
        message: Message to send (required for send and schedule operations)
        limit: Number of messages to read (optional, for read and unread operations)
        scheduled_time: ISO string of when to send message (required for schedule operation)

    Returns:
        String containing operation result or message content
    """
    try:
        if operation == "send":
            if not phone_number or not message:
                return "Phone number and message are required for send operation"
            
            result = messages_handler.send_message(phone_number, message)
            if result["success"]:
                return f"Message sent successfully to {phone_number}: {message}"
            else:
                return f"Failed to send message: {result['message']}"
                
        elif operation == "read":
            if not phone_number:
                return "Phone number is required for read operation"
            
            messages_list = messages_handler.read_messages(phone_number, limit)
            if messages_list:
                formatted_messages = []
                for msg in messages_list:
                    # Handle both old and new message format
                    sender = msg.get('sender', 'Unknown')
                    content = msg.get('content', '')
                    time = msg.get('time', msg.get('date', ''))
                    formatted_messages.append(f"[{time}] {sender}: {content}")
                return (
                    f"Last {len(messages_list)} messages with {phone_number}:\n\n"
                    + "\n".join(formatted_messages)
                )
            else:
                return f"No messages found with {phone_number}"
                
        elif operation == "schedule":
            if not phone_number or not message or not scheduled_time:
                return "Phone number, message, and scheduled_time are required for schedule operation"
            
            result = messages_handler.schedule_message(
                phone_number, message, scheduled_time
            )
            if result["success"]:
                return (
                    f"Message scheduled successfully to {phone_number} at "
                    f"{scheduled_time}: {message}"
                )
            else:
                return f"Failed to schedule message: {result['message']}"
                
        elif operation == "unread":
            # Get unread messages instead of just count
            unread_messages = messages_handler.get_unread_messages(limit)
            if unread_messages:
                formatted_messages = []
                for msg in unread_messages:
                    formatted_messages.append(
                    f"[{msg['date']}] {msg['sender']}: {msg['content']}"
                )
                return (
                    f"Found {len(unread_messages)} unread messages:\n\n"
                    + "\n".join(formatted_messages)
                )
            else:
                return "No unread messages found"
        else:
            return (
                f"Unknown operation: {operation}. Valid operations are: "
                "send, read, schedule, unread"
            )
            
    except Exception as e:
        logger.error(f"Error in messages tool: {e}")
        return f"Error accessing messages: {str(e)}"

# Tool: Mail
@app.tool()
def mail(
    operation: str,
    account: str = None,
    mailbox: str = None,
    limit: int = 10,
    search_term: str = None,
    to: str = None,
    subject: str = None,
    body: str = None,
    cc: str = None,
    bcc: str = None,
    full_content: bool = False,
    search_range: int = None,
    mark_read: bool = False,
) -> str:
    """
    Interact with Apple Mail app - read unread emails, search emails, and send emails.
    Optimized for performance by accessing local Mail database directly.
    Searches all accounts by default when no account is specified.

    Args:
        operation: Operation to perform: 'unread', 'search', 'send', 'mailboxes', or 'accounts'
        account: Email account to use (optional, searches all accounts if not specified)
        mailbox: Mailbox to use (optional)
        limit: Number of emails to retrieve (optional, for unread and search operations)
        search_term: Text to search for in emails (required for search operation)
        to: Recipient email address (required for send operation)
        subject: Email subject (required for send operation)
        body: Email body content (required for send operation)
        cc: CC email address (optional for send operation)
        bcc: BCC email address (optional for send operation)
        full_content: If True, return full email content without truncation (default: False)
        search_range: Number of recent messages to search through per inbox (optional, ignored for database method)
        mark_read: If True, mark retrieved unread emails as read (default: False, only for unread operation)

    Returns:
        String containing email information or operation result
    """
    try:
        if operation == "unread":
            # Use optimized database approach for unread emails
            emails = mail_handler.get_unread_emails(
                account, mailbox, limit, full_content, search_range, mark_read
            )
            if emails:
                formatted_emails = []
                for email in emails:
                    email_info = f"From: {email['sender']}\nSubject: {email['subject']}\nDate: {email['date']}"
                    if email.get('mailbox'):
                        email_info += f"\nMailbox: {email['mailbox']}"
                    if full_content or len(email['content']) <= 500:
                        email_info += f"\nContent: {email['content']}"
                    else:
                        email_info += f"\nContent: {email['content'][:500]}..."
                    formatted_emails.append(email_info)
                
                result = f"Found {len(emails)} unread emails"
                if mark_read:
                    result += " (marked as read)"
                result += ":\n\n" + "\n\n".join(formatted_emails)
                return result
            else:
                return "No unread emails found"
                
        elif operation == "search":
            if not search_term:
                return "Search term is required for search operation"
            
            emails = mail_handler.search_emails(search_term, account, mailbox, limit, full_content, search_range)
            if emails:
                formatted_emails = []
                for email in emails:
                    email_info = f"From: {email['sender']}\nSubject: {email['subject']}\nDate: {email['date']}"
                    if email.get('account'):
                        email_info += f"\nAccount: {email['account']}"
                    if email.get('mailbox'):
                        email_info += f"\nMailbox: {email['mailbox']}"
                    if full_content or len(email['content']) <= 500:
                        email_info += f"\nContent: {email['content']}"
                    else:
                        email_info += f"\nContent: {email['content'][:500]}..."
                    formatted_emails.append(email_info)
                
                result = f"Found {len(emails)} emails matching '{search_term}' (case insensitive)"
                if limit == -1:
                    result += " (all)"
                else:
                    result += f" (limit: {limit})"
                result += ":\n\n" + "\n\n".join(formatted_emails)
                return result
            else:
                return f"No emails found matching '{search_term}'"
                
        elif operation == "send":
            if not to or not subject or not body:
                return "To, subject, and body are required for send operation"
            
            result = mail_handler.send_email(to, subject, body, cc, bcc)
            if result["success"]:
                return f"Email sent successfully to {to} with subject '{subject}'"
            else:
                return f"Failed to send email: {result['message']}"
                
        elif operation == "mailboxes":
            mailboxes = mail_handler.list_mailboxes(account)
            if mailboxes:
                return f"Available mailboxes: {', '.join(mailboxes)}"
            else:
                return "No mailboxes found"
                
        elif operation == "accounts":
            accounts = mail_handler.list_accounts()
            if accounts:
                return f"Available accounts: {', '.join(accounts)}"
            else:
                return "No email accounts found"
                
        else:
            return f"Unknown operation: {operation}. Valid operations are: unread, search, send, mailboxes, accounts"
            
    except Exception as e:
        logger.error(f"Error in mail tool: {e}")
        return f"Error accessing mail: {str(e)}"

# Tool: Reminders
@app.tool()
def reminders(
    operation: str,
    search_text: str = None,
    name: str = None,
    list_name: str = None,
    list_id: str = None,
    props: List[str] = None,
    notes: str = None,
    due_date: str = None,
    show_completed: bool = False,
) -> str:
    """
    Search, create, and open reminders in Apple Reminders app.
    
    Args:
        operation: Operation to perform: 'list', 'search', 'open', 'create', or 'listById'
        search_text: Text to search for in reminders (required for search and open operations)
        name: Name of the reminder to create (required for create operation)
        list_name: Name of the list to create reminder in (optional for create operation)
        list_id: ID of the list to get reminders from (required for listById operation)
        props: Properties to include in reminders (optional for listById operation)
        notes: Additional notes for reminder (optional for create operation)
        due_date: Due date for reminder in ISO format (optional for create operation)
        show_completed: Whether to show completed reminders (default: False, shows only incomplete)
    
    Returns:
        String containing reminder information or operation result
    """
    try:
        if operation == "list":
            result = reminders_handler.list_reminders(show_completed=show_completed)
            if result:
                formatted_reminders = []
                for reminder in result:
                    formatted_reminders.append(f"• {reminder['name']} (List: {reminder['list']})")
                
                status_text = "all" if show_completed else "incomplete"
                return f"Found {len(formatted_reminders)} {status_text} reminders:\n\n" + "\n".join(formatted_reminders)
            else:
                status_text = "incomplete" if not show_completed else ""
                return f"No {status_text} reminders found"
                
        elif operation == "search":
            if not search_text:
                return "Search text is required for search operation"
            
            result = reminders_handler.search_reminders(search_text)
            if result:
                formatted_reminders = []
                for reminder in result:
                    formatted_reminders.append(f"• {reminder['name']} (List: {reminder['list']})")
                return f"Found {len(result)} reminders matching '{search_text}':\n\n" + "\n".join(formatted_reminders)
            else:
                return f"No reminders found matching '{search_text}'"
                
        elif operation == "create":
            if not name:
                return "Name is required for create operation"
            
            result = reminders_handler.create_reminder(name, list_name, notes, due_date)
            if result["success"]:
                return f"Successfully created reminder '{name}'"
            else:
                return f"Failed to create reminder: {result['message']}"
                
        elif operation == "open":
            if not search_text:
                return "Search text is required for open operation"
            
            result = reminders_handler.open_reminder(search_text)
            if result["success"]:
                return f"Opened reminder: {result['message']}"
            else:
                return f"Failed to open reminder: {result['message']}"
        else:
            return f"Unknown operation: {operation}. Valid operations are: list, search, create, open"
            
    except Exception as e:
        logger.error(f"Error in reminders tool: {e}")
        return f"Error accessing reminders: {str(e)}"

# Tool: Calendar
@app.tool()
def calendar(
    operation: str,
    search_text: str = None,
    event_id: str = None,
    limit: int = 10,
    from_date: str = None,
    to_date: str = None,
    title: str = None,
    start_date: str = None,
    end_date: str = None,
    location: str = None,
    notes: str = None,
    is_all_day: bool = False,
    calendar_name: str = None,
    target_calendar_name: str = None,
    invitees: List[str] = None,
) -> str:
    """
    Search, create, delete, move, and open calendar events in Apple Calendar app.
    
    Args:
        operation: Operation to perform: 'search', 'open', 'list', 'create', 'delete', 'move', or 'calendars'
        search_text: Text to search for in event titles, locations, and notes (required for search)
        event_id: ID of the event to open, delete, or move (required for open, delete, and move operations)
        limit: Number of events to retrieve (optional, default 10)
        from_date: Start date for search range in ISO format (optional, default is today)
        to_date: End date for search range in ISO format (optional)
        title: Title of the event to create (required for create operation)
        start_date: Start date/time of the event in ISO format (required for create)
        end_date: End date/time of the event in ISO format (required for create)
        location: Location of the event (optional for create operation)
        notes: Additional notes for the event (optional for create operation)
        is_all_day: Whether the event is an all-day event (optional, default False)
        calendar_name: Name of the calendar to create event in or filter by (optional)
        target_calendar_name: Name of the calendar to move event to (required for move operation)
        invitees: List of email addresses to invite to the event (optional for create operation)
    
    Returns:
        String containing calendar information or operation result
    """
    try:
        if operation == "search":
            if not search_text:
                return "Search text is required for search operation"
            
            events = calendar_handler.search_events_db(search_text, limit, from_date, to_date, calendar_name)
            if events:
                formatted_events = []
                for event in events:
                    formatted_events.append(f"{event['title']} ({event['start_date']} - {event['end_date']})\nLocation: {event['location']}\nCalendar: {event['calendar_name']}\nID: {event['id']}")
                filter_info = f" in calendar '{calendar_name}'" if calendar_name else ""
                return f"Found {len(events)} events matching '{search_text}'{filter_info}:\n\n" + "\n\n".join(formatted_events)
            else:
                filter_info = f" in calendar '{calendar_name}'" if calendar_name else ""
                return f"No events found matching '{search_text}'{filter_info}"
                
        elif operation == "list":
            events = calendar_handler.get_events_db(limit, from_date, to_date, calendar_name)
            if events:
                formatted_events = []
                for event in events:
                    formatted_events.append(f"{event['title']} ({event['start_date']} - {event['end_date']})\nLocation: {event['location']}\nCalendar: {event['calendar_name']}\nID: {event['id']}")
                filter_info = f" in calendar '{calendar_name}'" if calendar_name else ""
                return f"Found {len(events)} events{filter_info}:\n\n" + "\n\n".join(formatted_events)
            else:
                filter_info = f" in calendar '{calendar_name}'" if calendar_name else ""
                return f"No events found{filter_info}"
                
        elif operation == "calendars":
            calendars = calendar_handler.get_available_calendars()
            if calendars:
                formatted_calendars = []
                for cal in calendars:
                    formatted_calendars.append(f"• {cal['title']} (Type: {cal['type']}) - ID: {cal['id']}")
                return f"Found {len(calendars)} calendars:\n\n" + "\n".join(formatted_calendars)
            else:
                return "No calendars found"
                
        elif operation == "create":
            if not title or not start_date or not end_date:
                return "Title, start_date, and end_date are required for create operation"
            
            result = calendar_handler.create_event(title, start_date, end_date, location, notes, is_all_day, calendar_name, invitees)
            if result["success"]:
                success_msg = f"Successfully created event '{title}' from {start_date} to {end_date}"
                if invitees:
                    success_msg += f" with {len(invitees)} invitee(s): {', '.join(invitees)}"
                return success_msg
            else:
                return f"Failed to create event: {result['message']}"
                
        elif operation == "move":
            if not event_id or not target_calendar_name:
                return "Event ID and target calendar name are required for move operation"
            
            result = calendar_handler.move_event(event_id, target_calendar_name)
            if result["success"]:
                return f"Successfully moved event: {result['message']}"
            else:
                return f"Failed to move event: {result['message']}"
                
        elif operation == "delete":
            if not event_id:
                return "Event ID is required for delete operation"
            
            result = calendar_handler.delete_event(event_id)
            if result["success"]:
                return f"Successfully deleted event: {result['message']}"
            else:
                return f"Failed to delete event: {result['message']}"
                
        elif operation == "open":
            if not event_id:
                return "Event ID is required for open operation"
            
            result = calendar_handler.open_event(event_id)
            if result["success"]:
                return f"Opened event: {result['message']}"
            else:
                return f"Failed to open event: {result['message']}"
        else:
            return f"Unknown operation: {operation}. Valid operations are: search, list, create, delete, move, open, calendars"
            
    except Exception as e:
        logger.error(f"Error in calendar tool: {e}")
        return f"Error accessing calendar: {str(e)}"

# Tool: Maps
@app.tool()
def maps(
    operation: str,
    query: str = None,
    limit: int = 5,
    name: str = None,
    address: str = None,
    from_address: str = None,
    to_address: str = None,
    transport_type: str = "driving",
    guide_name: str = None,
) -> str:
    """
    Search locations, manage guides, save favorites, and get directions using Apple Maps.
    
    Args:
        operation: Operation to perform
        query: Search query for locations (required for search)
        limit: Maximum number of results to return (optional for search)
        name: Name of the location (required for save and pin)
        address: Address of the location (required for save, pin, addToGuide)
        from_address: Starting address for directions (required for directions)
        to_address: Destination address for directions (required for directions)
        transport_type: Type of transport to use (optional for directions)
        guide_name: Name of the guide (required for createGuide and addToGuide)
    
    Returns:
        String containing maps information or operation result
    """
    try:
        if operation == "search":
            if not query:
                return "Search query is required for search operation"
            
            try:
                result = maps_handler.search_locations(query, limit)
                logger.info(f"Maps search result: {result}")
                if result["success"]:
                    return result["message"]
                else:
                    return f"Search failed: {result['message']}"
            except Exception as e:
                logger.error(f"Exception in maps search: {e}")
                return f"Error in maps search: {str(e)}"
                
        elif operation == "save":
            if not name or not address:
                return "Name and address are required for save operation"
            
            result = maps_handler.save_location(name, address)
            if result["success"]:
                return result["message"]
            else:
                return f"Save failed: {result['message']}"
            
        elif operation == "pin":
            if not name or not address:
                return "Name and address are required for pin operation"
            
            result = maps_handler.drop_pin(name, address)
            if result["success"]:
                return result["message"]
            else:
                return f"Pin failed: {result['message']}"
            
        elif operation == "directions":
            if not from_address or not to_address:
                return "From and to addresses are required for directions operation"
            
            result = maps_handler.get_directions(from_address, to_address, transport_type)
            if result["success"]:
                return result["message"]
            else:
                return f"Directions failed: {result['message']}"
            
        elif operation == "listGuides":
            result = maps_handler.list_guides()
            return result["message"]
            
        elif operation == "createGuide":
            if not guide_name:
                return "Guide name is required for createGuide operation"
            
            result = maps_handler.create_guide(guide_name)
            return result["message"]
            
        elif operation == "addToGuide":
            if not address or not guide_name:
                return "Address and guide name are required for addToGuide operation"
            
            result = maps_handler.add_to_guide(address, guide_name)
            return result["message"]
        else:
            return f"Unknown operation: {operation}. Valid operations are: search, save, pin, directions, listGuides, createGuide, addToGuide"
            
    except Exception as e:
        logger.error(f"Error in maps tool: {e}")
        return f"Error accessing maps: {str(e)}"

# Tool: Web Search
@app.tool()
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo and retrieve content from search results.
    
    Args:
        query: Search query to look up
    
    Returns:
        String containing search results with titles, URLs, and content snippets
    """
    try:
        result = websearch_handler.search_web_sync(query)
        if result["success"] and result["results"]:
            formatted_results = []
            for search_result in result["results"]:
                formatted_results.append(f"[{search_result['url']}] {search_result['title']} - {search_result['snippet']}\ncontent: {search_result['content']}")
            return f"Found {len(result['results'])} results for '{query}':\n\n" + "\n\n".join(formatted_results)
        else:
            return f"No results found for '{query}'"
            
    except Exception as e:
        logger.error(f"Error in web search tool: {e}")
        return f"Error performing web search: {str(e)}"

def main() -> None:
    """Main entry point for the server."""
    logger.info("Starting PyApple MCP Server...")
    
    # Check if running on macOS
    if sys.platform != "darwin":
        logger.error("PyApple MCP requires macOS to function properly")
        sys.exit(1)
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 