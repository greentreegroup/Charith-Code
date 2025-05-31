# services/docs_service.py

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.auth import get_google_creds
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class DocsService:
    def __init__(self):
        self.creds = get_google_creds()
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    async def get_activity(self, start_date=None, end_date=None):
        try:
            # Convert dates to RFC 3339 timestamp format
            query_parts = ["mimeType='application/vnd.google-apps.document'"]
            
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                    hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                )
                query_parts.append(f"modifiedTime >= '{start_dt.isoformat()}'")
            
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
                )
                query_parts.append(f"modifiedTime <= '{end_dt.isoformat()}'")

            # Combine all query parts with AND
            query = ' and '.join(query_parts)

            docs = self.drive_service.files().list(
                q=query,
                pageSize=100,
                fields="files(id,name,modifiedTime,lastModifyingUser)",
                orderBy="modifiedTime desc"
            ).execute().get('files', [])
            
            return [self._format_doc(doc) for doc in docs]

        except HttpError as e:
            logger.error(f"Docs API Error: {e}", exc_info=True)
            return {"error": f"Docs API Error: {e.reason}"}
        except Exception as e:
            logger.error(f"Unexpected Error: {e}", exc_info=True)
            return {"error": "Internal server error"}

    def _format_doc(self, doc):
        # Convert the modifiedTime to include timezone info
        modified_time = datetime.fromisoformat(doc['modifiedTime'].replace('Z', '+00:00'))
        
        return {
            'Platform': 'Google Docs',
            'Activity_ID': doc['id'],
            'User': doc.get('lastModifyingUser', {}).get('displayName', ''),
            'File_Type': 'Document',
            'Timestamp': modified_time.isoformat(),
            'Date_Extracted': datetime.now(timezone.utc).isoformat()  # Now includes full timestamp
        }
