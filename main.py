# main.py

from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from typing import Optional, List, Dict, Any
from services.gmail_service import GmailService
from services.chat_service import ChatService
from services.calendar_service import CalendarService
from services.docs_service import DocsService
from utils.auth import get_google_creds
from config import Config
import logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = FastAPI(
   title="Google API Hub",
   description="""
   API for accessing Google services data. Date format for all endpoints: YYYY-MM-DD
   Example: 2024-02-19
  
   For more precise timing, you can also use: YYYY-MM-DDTHH:MM:SSZ
   Example: 2024-02-19T15:30:00Z
   """
)
@app.get("/api/gmail",
   tags=["Gmail"],
   summary="Get Gmail Data",
   description="""
   Retrieve email data with the following fields:
   - Platform
   - Email ID
   - Sent At time
   - From
   - To
   - Conversation ID
   - Reply To
   - Subject
   - Full Body
   - Date Extracted
  
   Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
   Example: 2024-02-19 or 2024-02-19T15:30:00Z
   """
)
async def get_gmail_data(
   start_date: Optional[str] = Query(
       None,
       description="Start date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   ),
   end_date: Optional[str] = Query(
       None,
       description="End date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   )
):
   try:
       service = GmailService()
       return await service.get_emails(start_date, end_date)
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
       
@app.get("/api/chats",
   tags=["Chat"],
   summary="Get Google Chat Data",
   description="""
   Retrieve chat messages with the following fields:
   - Platform
   - Chat ID
   - From
   - Channel
   - Message
   - Timestamp
   - Thread ID
   - Date Extracted
   
   Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
   Example: 2024-02-19 or 2024-02-19T15:30:00Z
   """
)
async def get_chat_data(
   start_date: Optional[str] = Query(
       None,
       description="Start date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   ),
   end_date: Optional[str] = Query(
       None,
       description="End date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   )
):
   try:
       service = ChatService()
       # Use get_messages_by_date_range for date filtering
       messages = await service.get_messages_by_date_range(start_date, end_date)
       # Return just the list of messages without the wrapper
       return messages
   except Exception as e:
       logger.error(f"Error getting chat data: {e}")
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar",
   tags=["Calendar"],
   summary="Get Calendar Data",
   description="""
   Retrieve calendar events with the following fields:
   - Platform
   - Event ID
   - Organizer
   - Attendees
   - Start Time
   - End Time
   - Subject
   - Description
   - Location
   - Meeting Type
   - Date Extracted
  
   Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
   Example: 2024-02-19 or 2024-02-19T15:30:00Z
   """
)
async def get_calendar_data(
   start_date: Optional[str] = Query(
       None,
       description="Start date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   ),
   end_date: Optional[str] = Query(
       None,
       description="End date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   )
):
   try:
       service = CalendarService()
       return await service.get_events(start_date, end_date)
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
       
@app.get("/api/docs",
   tags=["Documents"],
   summary="Get Google Docs Activity",
   description="""
   Retrieve document activity with the following fields:
   - Platform
   - Activity ID
   - User
   - File Type
   - Timestamp
   - Date Extracted
  
   Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
   Example: 2024-02-19 or 2024-02-19T15:30:00Z
   """
)
async def get_docs_activity(
   start_date: Optional[str] = Query(
       None,
       description="Start date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   ),
   end_date: Optional[str] = Query(
       None,
       description="End date in YYYY-MM-DD format (e.g., 2024-02-19) or YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)"
   )
):
   try:
       service = DocsService()
       return await service.get_activity(start_date, end_date)
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
   return {
       "app": "Google API Hub",
       "status": "running",
       "endpoints": {
           "Gmail": ["/api/gmail"],
           "Chat": ["/api/chats"],
           "Calendar": ["/api/calendar"],
           "Documents": ["/api/docs"]
       },
       "documentation": f"http://{Config.API_HOST}:{Config.API_PORT}/docs"
   }

if __name__ == "__main__":
   import uvicorn
   print(f"\nStarting server at http://{Config.API_HOST}:{Config.API_PORT}/docs")
   print(f"API documentation available at http://{Config.API_HOST}:{Config.API_PORT}/docs")
   print("\nDate format for all endpoints:")
   print("- Simple format: YYYY-MM-DD (e.g., 2024-02-19)")
   print("- Detailed format: YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-02-19T15:30:00Z)\n")
   uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
