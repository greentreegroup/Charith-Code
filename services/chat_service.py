# chat_service.py

from googleapiclient.discovery import build
from utils.auth import get_google_creds
import logging
from typing import Dict, List, Any, Optional
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

def to_async(func):
   """Decorator to convert a synchronous function to asynchronous"""
   @wraps(func)
   async def wrapper(*args, **kwargs):
       loop = asyncio.get_event_loop()
       return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
   return wrapper

class ChatService:
   """
   Service for interacting with Google Chat API.
  
   This class provides methods to fetch and process messages from Google Chat,
   extracting relevant information like sender, space details, content, and timestamps.
   """
  
   def __init__(self):
       """Initialize the Chat service with Google API credentials."""
       self.creds = get_google_creds()
       self.service = build('chat', 'v1', credentials=self.creds)
  
   @to_async
   def list_spaces(self) -> List[Dict[str, Any]]:
       """
       List all spaces (rooms and DMs) accessible to the authenticated user.
      
       Returns:
           List of space objects containing space information
       """
       try:
           spaces = self.service.spaces().list().execute()
           return spaces.get('spaces', [])
       except Exception as e:
           logger.error(f"Error listing spaces: {e}")
           return []
  
   @to_async
   def list_messages(self, space_name: str, page_size: int = 100) -> List[Dict[str, Any]]:
       """
       List messages from a specific space.
      
       Args:
           space_name: The name/ID of the space to fetch messages from
           page_size: Number of messages to fetch (default: 100)
          
       Returns:
           List of message objects
       """
       try:
           # Ensure space_name has the correct format
           if not space_name.startswith('spaces/'):
               space_name = f"spaces/{space_name}"
              
           result = self.service.spaces().messages().list(
               parent=space_name,
               pageSize=page_size
           ).execute()
           return result.get('messages', [])
       except Exception as e:
           logger.error(f"Error listing messages for space {space_name}: {e}")
           return []
  
   async def get_messages(self, space_name: str = None, date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
       """
       Get messages from a specific space, optionally filtered by date.
      
       Args:
           space_name: Optional name/ID of the space to fetch messages from
           date: Optional date filter in ISO format (YYYY-MM-DD)
           limit: Maximum number of messages to return (default: 100)
          
       Returns:
           List of processed message objects
       """
       try:
           # Check if the first parameter is actually a date (start_date from the original endpoint)
           # This handles the case when this function is called from the /api/chats endpoint
           if space_name and (space_name.startswith('20') and '-' in space_name):
               # This appears to be a date, not a space name
               start_date = space_name
               space_name = None
              
               # If date is present, treat it as end_date
               end_date = date
               date = None
              
               # Get all messages and filter by date range
               return await self.get_messages_by_date_range(start_date, end_date, limit)
          
           # Original functionality for specific space or all spaces
           if space_name:
               # Ensure space_name has the correct format
               if not space_name.startswith('spaces/'):
                   space_name = f"spaces/{space_name}"
                  
               # Get messages from a specific space
               raw_messages = await self.list_messages(space_name, page_size=limit)
           else:
               # Get messages from all spaces
               spaces = await self.list_spaces()
               raw_messages = []
               for space in spaces:
                   space_messages = await self.list_messages(space['name'], page_size=limit)
                   raw_messages.extend(space_messages)
                   if len(raw_messages) >= limit:
                       raw_messages = raw_messages[:limit]
                       break
          
           # Process and filter messages
           processed_messages = []
           for msg in raw_messages:
               # Apply date filter if provided
               if date and date not in msg.get('createTime', ''):
                   continue
              
               message_details = self.get_message_details(msg)
               if message_details:
                   processed_messages.append(message_details)
              
               if len(processed_messages) >= limit:
                   break
                  
           return processed_messages
       except Exception as e:
           logger.error(f"Error getting messages: {e}")
           return []
  
   def get_message_details(self, msg: Dict[str, Any]) -> Dict[str, Any]:
       """
       Extract detailed information from a message object.
      
       Args:
           msg: The raw message object from Google Chat API
          
       Returns:
           Dictionary containing structured message information
       """
       try:
           # Extract message content
           message_content = ""
           if 'text' in msg:
               message_content = msg['text']
           elif 'formattedText' in msg:
               message_content = msg.get('formattedText', {}).get('text', '')
           elif 'cards' in msg:
               message_content = "Card content (not plain text)"
              
           # Extract sender information
           sender = msg.get('sender', {})
           sender_name = sender.get('name', '')
           sender_display_name = sender.get('displayName', '')
          
           # Extract space information
           space = msg.get('space', {})
           space_name = space.get('name', '')
           space_display_name = space.get('displayName', '')
          
           # Return structured message data - removed 'To' field as requested
           return {
               'Platform': 'Google Chat',
               'Chat_ID': msg['name'],
               'From': sender_display_name or sender_name,
               'Channel': space_display_name,
               'Message': message_content,
               'Timestamp': msg['createTime'],
               'Thread_ID': msg.get('thread', {}).get('name', ''),
           }
       except Exception as e:
           logger.error(f"Error processing message details: {e}")
           return {}
  
   async def get_all_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
       """
       Fetch messages from all accessible spaces.
      
       Args:
           limit: Optional maximum number of messages to fetch per space
          
       Returns:
           List of structured message objects
       """
       try:
           spaces = await self.list_spaces()
           messages = []
          
           for space in spaces:
               space_name = space['name']
               space_messages = await self.list_messages(space_name, page_size=limit or 100)
              
               for msg in space_messages:
                   message_details = self.get_message_details(msg)
                   if message_details:
                       messages.append(message_details)
                  
                   if limit and len(messages) >= limit:
                       break
              
               if limit and len(messages) >= limit:
                   break
                  
           return messages
       except Exception as e:
           logger.error(f"Error fetching all messages: {e}")
           return []
  
   async def get_messages_by_space(self, space_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
       """
       Fetch messages from a specific space.
      
       Args:
           space_id: ID of the space to fetch messages from
           limit: Optional maximum number of messages to fetch
          
       Returns:
           List of structured message objects from the specified space
       """
       try:
           # Ensure space_id has the correct format
           if not space_id.startswith('spaces/'):
               space_id = f"spaces/{space_id}"
              
           space_messages = await self.list_messages(space_id, page_size=limit or 100)
           messages = []
          
           for msg in space_messages:
               message_details = self.get_message_details(msg)
               if message_details:
                   messages.append(message_details)
              
               if limit and len(messages) >= limit:
                   break
                  
           return messages
       except Exception as e:
           logger.error(f"Error fetching messages for space {space_id}: {e}")
           return []
          
   async def get_messages_by_date_range(self, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict[str, Any]]:
       """
       Get messages filtered by a date range.
      
       Args:
           start_date: Optional start date in ISO format (YYYY-MM-DD)
           end_date: Optional end date in ISO format (YYYY-MM-DD)
           limit: Maximum number of messages to return
          
       Returns:
           List of processed message objects within the date range
       """
       try:
           # Get all spaces
           spaces = await self.list_spaces()
           all_messages = []
          
           # Get messages from each space
           for space in spaces:
               space_messages = await self.list_messages(space['name'], page_size=limit)
              
               # Filter messages by date range
               for msg in space_messages:
                   message_time = msg.get('createTime', '')
                  
                   # Check if message is within date range
                   if start_date and not self._is_after_date(message_time, start_date):
                       continue
                      
                   if end_date and not self._is_before_date(message_time, end_date):
                       continue
                  
                   message_details = self.get_message_details(msg)
                   if message_details:
                       all_messages.append(message_details)
                  
                   if len(all_messages) >= limit:
                       break
              
               if len(all_messages) >= limit:
                   all_messages = all_messages[:limit]
                   break
                  
           return all_messages
       except Exception as e:
           logger.error(f"Error getting messages by date range: {e}")
           return []
      
   def _is_after_date(self, timestamp: str, date_str: str) -> bool:
       """Check if a timestamp is after a given date"""
       try:
           # Parse the timestamp (format: 2023-09-15T14:30:45.123456Z)
           timestamp_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
          
           # Compare dates as strings (works for YYYY-MM-DD format)
           return timestamp_date >= date_str
       except Exception:
           return False
          
   def _is_before_date(self, timestamp: str, date_str: str) -> bool:
       """Check if a timestamp is before a given date"""
       try:
           # Parse the timestamp (format: 2023-09-15T14:30:45.123456Z)
           timestamp_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
          
           # Compare dates as strings (works for YYYY-MM-DD format)
           return timestamp_date <= date_str
       except Exception:
           return False
