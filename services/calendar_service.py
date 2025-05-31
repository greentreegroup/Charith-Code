# services/calendar_service.py

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.auth import get_google_creds
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.creds = get_google_creds()
        self.service = build('calendar', 'v3', credentials=self.creds)

    async def get_events(self, start_date=None, end_date=None):
        try:
            # Convert dates to RFC3339 format
            time_min = None
            time_max = None
            
            if start_date:
                time_min = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                ).isoformat()
            
            if end_date:
                time_max = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
                ).isoformat()

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return [self._format_event(event) for event in events_result.get('items', [])]

        except HttpError as e:
            logger.error(f"Calendar API Error: {e}", exc_info=True)
            return {"error": f"Calendar API Error: {str(e)}"}
        except ValueError as e:
            logger.error(f"Invalid Date Format: {e}", exc_info=True)
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected Error: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}

    def _format_event(self, event):
        return {
            'Platform': 'Google Calendar',
            'Event_ID': event['id'],
            'Organizer': event.get('organizer', {}).get('email', ''),
            'Attendees': [a.get('email') for a in event.get('attendees', [])],
            'Start_Time': event['start'].get('dateTime', event['start'].get('date')),
            'End_Time': event['end'].get('dateTime', event['end'].get('date')),
            'Subject': event.get('summary', ''),
            'Description': event.get('description', ''),
            'Location': event.get('location', ''),
            'Meeting_Type': 'Virtual' if any(key in event for key in ['hangoutLink', 'conferenceData']) else 'In-person',
            'Date_Extracted': datetime.now().isoformat()
        }
