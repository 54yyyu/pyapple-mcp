"""
Apple Calendar integration

Provides functionality to search, create, and manage calendar events using the macOS Calendar app.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .applescript import applescript

logger = logging.getLogger(__name__)

class CalendarHandler:
    """Handler for Apple Calendar app integration."""
    
    def __init__(self):
        """Initialize the calendar handler."""
        self.app_name = "Calendar"
    
    def search_events(self, search_text: str, limit: int = 10, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
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
    
    def get_events(self, limit: int = 10, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
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
    
    def create_event(self, title: str, start_date: str, end_date: str, location: Optional[str] = None, notes: Optional[str] = None, is_all_day: bool = False, calendar_name: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Parse ISO dates to AppleScript format
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            start_date_str = start_dt.strftime("%m/%d/%Y %H:%M:%S")
            end_date_str = end_dt.strftime("%m/%d/%Y %H:%M:%S")
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