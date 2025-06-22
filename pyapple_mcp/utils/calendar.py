"""
Apple Calendar integration

Provides functionality to search, create, and manage calendar events using the macOS Calendar app.
"""

import logging
import sqlite3
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .applescript import applescript

logger = logging.getLogger(__name__)

class CalendarHandler:
    """Handler for Apple Calendar app integration."""
    
    def __init__(self):
        """Initialize the calendar handler."""
        self.app_name = "Calendar"
        self.db_path = os.path.expanduser(
            "~/Library/Calendars/Calendar.sqlitedb"
        )
    
    def get_available_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of available calendars from the database.
        
        Returns:
            List of dictionaries containing calendar information
        """
        conn = self._get_db_connection()
        if not conn:
            return []
        
        try:
            query = """
                SELECT 
                    ROWID,
                    title,
                    type,
                    external_id,
                    UUID
                FROM Calendar 
                WHERE title IS NOT NULL 
                ORDER BY title
            """
            
            cursor = conn.execute(query)
            calendars = []
            
            for row in cursor.fetchall():
                calendars.append({
                    "id": row["ROWID"],
                    "title": row["title"],
                    "type": row["type"] or "Unknown",
                    "external_id": row["external_id"] or "",
                    "uuid": row["UUID"]
                })
            
            return calendars
            
        except Exception as e:
            logger.error(f"Database calendar list error: {e}")
            return []
        finally:
            conn.close()

    def _get_db_connection(self):
        """Get a connection to the Calendar database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable accessing columns by name
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Calendar database: {e}")
            return None
    
    def _convert_core_data_date(self, core_data_timestamp: float) -> str:
        """Convert Core Data timestamp to readable date string."""
        if core_data_timestamp is None:
            return "No date"
        
        # Core Data uses a reference date of January 1, 2001 00:00:00 UTC
        # Convert to Unix timestamp then to datetime
        reference_date = datetime(2001, 1, 1)
        actual_date = reference_date + timedelta(seconds=core_data_timestamp)
        return actual_date.strftime("%Y-%m-%d %H:%M:%S")
    
    def search_events_db(
        self,
        search_text: str,
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        calendar_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for calendar events using direct database access.
        
        Args:
            search_text: Text to search for in event titles, locations, and notes
            limit: Maximum number of events to return
            from_date: Start date for search range in ISO format (optional)
            to_date: End date for search range in ISO format (optional)
            calendar_filter: Calendar name to filter by (optional)
            
        Returns:
            List of dictionaries containing event information
        """
        conn = self._get_db_connection()
        if not conn:
            return []
        
        try:
            # Calculate Core Data timestamps if date range provided
            date_filter = ""
            calendar_filter_clause = ""
            params = [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]
            
            if calendar_filter:
                calendar_filter_clause = " AND c.title = ?"
                params.append(calendar_filter)
            
            if from_date or to_date:
                reference_date = datetime(2001, 1, 1)
                
                if from_date:
                    start_dt = datetime.fromisoformat(from_date[:19])  # Remove timezone
                    start_timestamp = (start_dt - reference_date).total_seconds()
                    date_filter += " AND ci.start_date >= ?"
                    params.append(start_timestamp)
                
                if to_date:
                    end_dt = datetime.fromisoformat(to_date[:19])  # Remove timezone
                    end_timestamp = (end_dt - reference_date).total_seconds()
                    date_filter += " AND ci.end_date <= ?"
                    params.append(end_timestamp)
            
            query = f"""
                SELECT 
                    ci.ROWID,
                    ci.summary,
                    ci.description,
                    ci.start_date,
                    ci.end_date,
                    ci.all_day,
                    ci.UUID,
                    c.title as calendar_name,
                    l.title as location
                FROM CalendarItem ci 
                JOIN Calendar c ON ci.calendar_id = c.ROWID 
                LEFT JOIN Location l ON ci.location_id = l.ROWID
                WHERE (ci.summary LIKE ? OR ci.description LIKE ? OR l.title LIKE ?)
                {calendar_filter_clause}
                {date_filter}
                ORDER BY ci.start_date ASC 
                LIMIT ?
            """
            params.append(limit)
            
            cursor = conn.execute(query, params)
            events = []
            
            for row in cursor.fetchall():
                events.append({
                    "id": row["UUID"],
                    "title": row["summary"] or "Untitled",
                    "location": row["location"] or "Not specified",
                    "notes": row["description"] or "",
                    "start_date": self._convert_core_data_date(row["start_date"]),
                    "end_date": self._convert_core_data_date(row["end_date"]),
                    "calendar_name": row["calendar_name"],
                    "all_day": bool(row["all_day"])
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
        finally:
            conn.close()
    
    def get_events_db(
        self,
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        calendar_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events using direct database access.
        
        Args:
            limit: Maximum number of events to return
            from_date: Start date for search range in ISO format (optional)
            to_date: End date for search range in ISO format (optional)
            calendar_filter: Calendar name to filter by (optional)
            
        Returns:
            List of dictionaries containing event information
        """
        conn = self._get_db_connection()
        if not conn:
            return []
        
        try:
            # Set default date range if not provided
            if not from_date:
                from_date = datetime.now().isoformat()
            if not to_date:
                end_date = datetime.now() + timedelta(days=7)
                to_date = end_date.isoformat()
            
            # Calculate Core Data timestamps
            reference_date = datetime(2001, 1, 1)
            start_dt = datetime.fromisoformat(from_date[:19])
            end_dt = datetime.fromisoformat(to_date[:19])
            start_timestamp = (start_dt - reference_date).total_seconds()
            end_timestamp = (end_dt - reference_date).total_seconds()
            
            calendar_filter_clause = ""
            params = [start_timestamp, end_timestamp]
            
            if calendar_filter:
                calendar_filter_clause = " AND c.title = ?"
                params.append(calendar_filter)
            
            query = f"""
                SELECT 
                    ci.ROWID,
                    ci.summary,
                    ci.description,
                    ci.start_date,
                    ci.end_date,
                    ci.all_day,
                    ci.UUID,
                    c.title as calendar_name,
                    l.title as location
                FROM CalendarItem ci 
                JOIN Calendar c ON ci.calendar_id = c.ROWID 
                LEFT JOIN Location l ON ci.location_id = l.ROWID
                WHERE ci.start_date >= ? AND ci.start_date <= ?
                {calendar_filter_clause}
                ORDER BY ci.start_date ASC 
                LIMIT ?
            """
            params.append(limit)
            
            cursor = conn.execute(query, params)
            events = []
            
            for row in cursor.fetchall():
                events.append({
                    "id": row["UUID"],
                    "title": row["summary"] or "Untitled",
                    "location": row["location"] or "Not specified", 
                    "notes": row["description"] or "",
                    "start_date": self._convert_core_data_date(row["start_date"]),
                    "end_date": self._convert_core_data_date(row["end_date"]),
                    "calendar_name": row["calendar_name"],
                    "all_day": bool(row["all_day"])
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Database get events error: {e}")
            return []
        finally:
            conn.close()
    
    def search_events(
        self,
        search_text: str,
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for calendar events containing the specified text.
        
        Args:
            search_text: Text to search for in event titles, locations, and notes
            limit: Maximum number of events to return
            from_date: Start date for search range in ISO format (optional)
            to_date: End date for search range in ISO format (optional)
            
        Returns:
            List of dictionaries containing event information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Calendar app")
            return []
        
        # Set default date range if not provided
        if not from_date:
            from_date = datetime.now().isoformat()
        if not to_date:
            end_date = datetime.now() + timedelta(days=30)
            to_date = end_date.isoformat()
        
        # Parse dates to proper format for AppleScript
        try:
            start_dt = datetime.fromisoformat(from_date[:10])
            end_dt = datetime.fromisoformat(to_date[:10])
            
            # Format for AppleScript (MM/DD/YYYY)
            start_date_str = start_dt.strftime("%m/%d/%Y")
            end_date_str = end_dt.strftime("%m/%d/%Y")
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return []
        
        # Escape quotes in search text
        safe_search_text = search_text.replace('"', '\\"')
        
        script = f'''
        tell application "Calendar"
            set eventsList to {{}}
            set searchText to "{safe_search_text}"
            set eventLimit to {limit}
            set eventCount to 0
            
            try
                set startDate to date "{start_date_str}"
                set endDate to date "{end_date_str} 11:59:59 PM"
                
                repeat with aCalendar in calendars
                    if eventCount >= eventLimit then exit repeat
                    
                    -- Better date range logic: find events that overlap with our date range
                    set calendarEvents to (every event of aCalendar whose (start date <= endDate) and (end date >= startDate))
                    
                    repeat with anEvent in calendarEvents
                        if eventCount >= eventLimit then exit repeat
                        
                        set eventTitle to summary of anEvent
                        
                        -- Handle potentially empty values
                        try
                            set eventLocation to location of anEvent
                        on error
                            set eventLocation to ""
                        end try
                        
                        try
                            set eventDescription to description of anEvent
                        on error
                            set eventDescription to ""
                        end try
                        
                        if (eventTitle contains searchText) or (eventLocation contains searchText) or (eventDescription contains searchText) then
                            set eventStart to start date of anEvent
                            set eventEnd to end date of anEvent
                            set eventCalendar to title of aCalendar
                            set eventUID to uid of anEvent
                            
                            set eventInfo to (eventTitle & "|" & eventLocation & "|" & eventDescription & "|" & (eventStart as string) & "|" & (eventEnd as string) & "|" & eventCalendar & "|" & eventUID)
                            set end of eventsList to eventInfo
                            set eventCount to eventCount + 1
                        end if
                    end repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to eventsList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            events_data = result['result']
            if events_data.startswith("Error:"):
                logger.error(f"Calendar search error: {events_data}")
                return []
            
            # Parse the events data
            events_list = []
            if events_data:
                for event_entry in events_data.split(";"):
                    if "|" in event_entry:
                        parts = event_entry.split("|", 6)
                        if len(parts) >= 7:
                            title, location, description, start_date, end_date, calendar_name, uid = parts
                            events_list.append({
                                "title": title,
                                "location": location or "Not specified",
                                "notes": description,
                                "start_date": start_date,
                                "end_date": end_date,
                                "calendar_name": calendar_name,
                                "id": uid
                            })
                        
            return events_list
        else:
            logger.error(f"Failed to search events: {result.get('error')}")
            return []
    
    def get_events(
        self,
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events in a specified date range.
        
        Args:
            limit: Maximum number of events to return
            from_date: Start date for search range in ISO format (optional)
            to_date: End date for search range in ISO format (optional)
            
        Returns:
            List of dictionaries containing event information
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Calendar app")
            return []
        
        # Set default date range if not provided
        if not from_date:
            from_date = datetime.now().isoformat()
        if not to_date:
            end_date = datetime.now() + timedelta(days=1)  # Default to just today + 1 day
            to_date = end_date.isoformat()
        
        # Parse dates to proper format for AppleScript
        try:
            start_dt = datetime.fromisoformat(from_date[:10])
            end_dt = datetime.fromisoformat(to_date[:10])
            
            # Format for AppleScript (MM/DD/YYYY)
            start_date_str = start_dt.strftime("%m/%d/%Y")
            end_date_str = end_dt.strftime("%m/%d/%Y")
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return []
        
        script = f'''
        tell application "Calendar"
            set eventsList to {{}}
            set eventLimit to {limit}
            set eventCount to 0
            
            try
                set startDate to date "{start_date_str}"
                set endDate to date "{end_date_str} 11:59:59 PM"
                
                repeat with aCalendar in calendars
                    if eventCount >= eventLimit then exit repeat
                    
                    -- Better date range logic: find events that overlap with our date range
                    set calendarEvents to (every event of aCalendar whose (start date <= endDate) and (end date >= startDate))
                    
                    repeat with anEvent in calendarEvents
                        if eventCount >= eventLimit then exit repeat
                        
                        set eventTitle to summary of anEvent
                        
                        -- Handle potentially empty values
                        try
                            set eventLocation to location of anEvent
                        on error
                            set eventLocation to ""
                        end try
                        
                        try
                            set eventDescription to description of anEvent
                        on error
                            set eventDescription to ""
                        end try
                        
                        set eventStart to start date of anEvent
                        set eventEnd to end date of anEvent
                        set eventCalendar to title of aCalendar
                        set eventUID to uid of anEvent
                        
                        set eventInfo to (eventTitle & "|" & eventLocation & "|" & eventDescription & "|" & (eventStart as string) & "|" & (eventEnd as string) & "|" & eventCalendar & "|" & eventUID)
                        set end of eventsList to eventInfo
                        set eventCount to eventCount + 1
                    end repeat
                end repeat
                
                set AppleScript's text item delimiters to ";"
                set resultString to eventsList as string
                set AppleScript's text item delimiters to ""
                return resultString
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            events_data = result['result']
            if events_data.startswith("Error:"):
                logger.error(f"Calendar get events error: {events_data}")
                return []
            
            # Parse the events data
            events_list = []
            if events_data:
                for event_entry in events_data.split(";"):
                    if "|" in event_entry:
                        parts = event_entry.split("|", 6)
                        if len(parts) >= 7:
                            title, location, description, start_date, end_date, calendar_name, uid = parts
                            events_list.append({
                                "title": title,
                                "location": location or "Not specified",
                                "notes": description,
                                "start_date": start_date,
                                "end_date": end_date,
                                "calendar_name": calendar_name,
                                "id": uid
                            })
                        
            return events_list
        else:
            logger.error(f"Failed to get events: {result.get('error')}")
            return []
    
    def create_event(
        self,
        title: str,
        start_date: str,
        end_date: str,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        is_all_day: bool = False,
        calendar_name: Optional[str] = None,
        invitees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            title: Title of the event
            start_date: Start date/time in ISO format
            end_date: End date/time in ISO format
            location: Location of the event (optional)
            notes: Additional notes for the event (optional)
            is_all_day: Whether the event is all-day (optional)
            calendar_name: Name of the calendar to create the event in (optional)
            invitees: List of email addresses to invite to the event (optional)
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Calendar app")
            return {"success": False, "message": "Cannot access Calendar app"}
        
        # Escape quotes in the content
        safe_title = title.replace('"', '\\"')
        safe_location = (location or "").replace('"', '\\"')
        safe_notes = (notes or "").replace('"', '\\"')
        safe_calendar = (calendar_name or "").replace('"', '\\"')
        
        # Process invitees
        invitee_script = ""
        if invitees and len(invitees) > 0:
            # Create AppleScript to add attendees
            attendee_lines = []
            for invitee in invitees:
                safe_invitee = invitee.replace('"', '\\"')
                attendee_lines.append(f'make new attendee at newEvent with properties {{email:"{safe_invitee}"}}')
            invitee_script = "\n                ".join(attendee_lines)
        
        # Parse ISO dates to AppleScript format
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Format for AppleScript - use explicit format that AppleScript can parse correctly
            start_date_str = start_dt.strftime("%B %d, %Y at %I:%M:%S %p")
            end_date_str = end_dt.strftime("%B %d, %Y at %I:%M:%S %p")
        except ValueError:
            return {"success": False, "message": "Invalid date format. Please use ISO format."}
        
        # Build calendar clause - be more specific about default calendar
        if calendar_name:
            calendar_clause = f'calendar "{safe_calendar}"'
        else:
            calendar_clause = '(first calendar whose writable is true)'
        
        # Build location clause
        location_clause = f'set location of newEvent to "{safe_location}"' if safe_location else ""
        
        # Build notes clause
        notes_clause = f'set description of newEvent to "{safe_notes}"' if safe_notes else ""
        
        # Build all-day clause
        all_day_clause = f'set allday event of newEvent to {str(is_all_day).lower()}'
        
        # Build the AppleScript with conditional clauses
        clauses = []
        if location_clause:
            clauses.append(location_clause)
        if notes_clause:
            clauses.append(notes_clause)
        clauses.append(all_day_clause)
        if invitee_script:
            clauses.append(invitee_script)
        
        additional_properties = "\n                ".join(clauses)
        
        script = f'''
        tell application "Calendar"
            try
                set targetCalendar to {calendar_clause}
                set startDate to date "{start_date_str}"
                set endDate to date "{end_date_str}"
                
                set newEvent to make new event at targetCalendar with properties {{summary:"{safe_title}", start date:startDate, end date:endDate}}
                
                {additional_properties}
                
                return "Success: Event created"
                
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = applescript.run_script(script)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": "Event created successfully"}
            else:
                logger.error(f"Calendar creation error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to create event: {result.get('error')}")
            return {"success": False, "message": f"Failed to create event: {result.get('error')}"}
    
    def _find_event_calendar_db(self, event_id: str) -> Optional[str]:
        """
        Find which calendar contains the event using database lookup.
        
        Args:
            event_id: UUID of the event to find
            
        Returns:
            Calendar title if found, None otherwise
        """
        conn = self._get_db_connection()
        if not conn:
            return None
        
        try:
            query = """
                SELECT c.title 
                FROM CalendarItem ci 
                JOIN Calendar c ON ci.calendar_id = c.ROWID 
                WHERE ci.UUID = ?
            """
            
            cursor = conn.execute(query, [event_id])
            row = cursor.fetchone()
            
            if row:
                return row["title"]
            return None
            
        except Exception as e:
            logger.error(f"Database calendar lookup error: {e}")
            return None
        finally:
            conn.close()

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        Delete a specific calendar event.

        Args:
            event_id: ID of the event to delete
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Calendar app")
            return {"success": False, "message": "Cannot access Calendar app"}
        
        # First, try to find which calendar contains the event using database lookup
        calendar_name = self._find_event_calendar_db(event_id)
        
        # Escape inputs to prevent injection issues
        safe_event_id = event_id.replace('"', '\\"')
        
        if calendar_name:
            # Optimized approach: target specific calendar
            logger.info(f"Found event in calendar '{calendar_name}', using targeted deletion")
            safe_calendar_name = calendar_name.replace('"', '\\"')
            
            # Determine timeout based on calendar type - longer for email-based calendars
            timeout = 120 if any(indicator in calendar_name.lower() for indicator in ['@', 'gmail', 'exchange', 'outlook']) else 60
            
            script = f'''
            tell application "Calendar"
                try
                    set eventUID to "{safe_event_id}"
                    set targetCalendarName to "{safe_calendar_name}"
                    
                    -- Find the specific calendar
                    set targetCalendar to null
                    repeat with aCalendar in calendars
                        if title of aCalendar is targetCalendarName then
                            set targetCalendar to aCalendar
                            exit repeat
                        end if
                    end repeat
                    
                    if targetCalendar is null then
                        return "Error: Calendar not found: " & targetCalendarName
                    end if
                    
                    -- Search only in this calendar (much faster)
                    set calendarEvents to events of targetCalendar
                    
                    repeat with currentEvent in calendarEvents
                        try
                            if uid of currentEvent is eventUID then
                                set eventTitle to summary of currentEvent
                                delete currentEvent
                                return "Success: Deleted event: " & eventTitle
                            end if
                        on error
                            -- Skip problematic events
                        end try
                    end repeat
                    
                    return "Error: Event not found in target calendar"
                    
                on error errMsg
                    return "Error: " & errMsg
                end try
            end tell
            '''
        else:
            # Fallback: search all calendars (slower but comprehensive)
            logger.warning(f"Could not determine calendar for event {event_id}, using fallback method")
            timeout = 60
            
            script = f'''
            tell application "Calendar"
                try
                    set eventUID to "{safe_event_id}"
                    set foundEvent to null
                    set foundEventTitle to ""
                    
                    -- Get all calendars first
                    set allCalendars to calendars
                    
                    repeat with aCalendar in allCalendars
                        try
                            -- Get all events for this calendar as a list
                            set calendarEvents to events of aCalendar
                            
                            -- Check each event's UID
                            repeat with i from 1 to count of calendarEvents
                                try
                                    set currentEvent to item i of calendarEvents
                                    if uid of currentEvent is eventUID then
                                        set foundEvent to currentEvent
                                        set foundEventTitle to summary of currentEvent
                                        exit repeat
                                    end if
                                on error
                                    -- Skip problematic events
                                end try
                            end repeat
                            
                            if foundEvent is not null then exit repeat
                        on error
                            -- Skip problematic calendars
                        end try
                    end repeat
                    
                    if foundEvent is not null then
                        delete foundEvent
                        return "Success: Deleted event: " & foundEventTitle
                    else
                        return "Error: No event found with ID: " & eventUID
                    end if
                    
                on error errMsg
                    return "Error: " & errMsg
                end try
            end tell
            '''
        
        result = applescript.run_script(script, timeout=timeout)
        if result['success'] and result['result']:
            result_msg = result['result']
            if result_msg.startswith("Success:"):
                return {"success": True, "message": result_msg.replace("Success: ", "")}
            else:
                logger.error(f"Calendar delete error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to delete event: {result.get('error')}")
            return {"success": False, "message": f"Failed to delete event: {result.get('error')}"}

    def open_event(self, event_id: str) -> Dict[str, Any]:
        """
        Open a specific calendar event in the Calendar app.
        
        Args:
            event_id: ID of the event to open
            
        Returns:
            Dictionary with success status and message
        """
        if not applescript.check_app_access(self.app_name):
            logger.error("Cannot access Calendar app")
            return {"success": False, "message": "Cannot access Calendar app"}
        
        script = f'''
        tell application "Calendar"
            try
                activate
                
                -- Search for the event by UID
                set eventUID to "{event_id}"
                set foundEvent to null
                
                repeat with aCalendar in calendars
                    repeat with anEvent in events of aCalendar
                        if uid of anEvent is eventUID then
                            set foundEvent to anEvent
                            exit repeat
                        end if
                    end repeat
                    if foundEvent is not null then exit repeat
                end repeat
                
                if foundEvent is not null then
                    show foundEvent
                    return "Success: Opened event: " & summary of foundEvent
                else
                    return "Error: No event found with ID: " & eventUID
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
                logger.error(f"Calendar open error: {result_msg}")
                return {"success": False, "message": result_msg}
        else:
            logger.error(f"Failed to open event: {result.get('error')}")
            return {"success": False, "message": f"Failed to open event: {result.get('error')}"} 