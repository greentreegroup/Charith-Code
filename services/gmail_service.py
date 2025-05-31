# services/gmail_service.py

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.auth import get_google_creds
from datetime import datetime
import base64
import logging

logger = logging.getLogger(__name__)

class GmailService:
    def __init__(self):
        self.creds = get_google_creds()
        self.service = build('gmail', 'v1', credentials=self.creds)

    async def get_emails(self, start_date=None, end_date=None):
        try:
            query = []
            if start_date:
                # Convert YYYY-MM-DD to timestamp format for Gmail API
                start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
                query.append(f'after:{start_timestamp}')
            if end_date:
                # Convert YYYY-MM-DD to timestamp format for Gmail API
                end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
                query.append(f'before:{end_timestamp}')

            result = self.service.users().messages().list(
                userId='me',
                q=' '.join(query) if query else '',
                maxResults=100
            ).execute()

            messages = result.get('messages', [])
            return [await self._format_message(m['id']) for m in messages]

        except HttpError as e:
            logger.error(f"Gmail API Error: {e}", exc_info=True)
            return {"error": f"Gmail API Error: {e.reason}"}
        except ValueError as e:
            logger.error(f"Invalid Date Format: {e}", exc_info=True)
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected Error: {e}", exc_info=True)
            return {"error": "Internal server error"}

    async def _format_message(self, msg_id):
        msg = self.service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
        
        # Get full message body
        body = ""
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

        return {
            'Platform': 'Gmail',
            'Email_ID': msg_id,
            'Sent_At': headers.get('date', ''),
            'From': headers.get('from', ''),
            'To': headers.get('to', ''),
            'Conversation_ID': msg['threadId'],
            'Reply_To': headers.get('reply-to', ''),
            'Subject': headers.get('subject', ''),
            'Full_Body': body or msg.get('snippet', ''),
            'Date_Extracted': datetime.now().isoformat()
        }
