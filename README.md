# Google API Data Extraction

An API that connects to multiple Google services, such as Google Docs, Google Drive, Gmail, and Google Calendar, to extract and manage user data.

## Setup

1. Create a Google Cloud Project  
- Go to [Google Cloud Console](https://console.cloud.google.com)  
- Create a new project  
- Enable the necessary APIs based on your use case:
  - **Google Docs API**
  - **Google Chat API**
  - **Google Gmail API**
  - **Google Calendar API**
- Create **OAuth 2.0 credentials**  
- Download the credentials file as `credentials.json`

2. Set Up Your Credentials  
- Copy the example file to create your own credentials file:  
  ```bash
  cp credentials.json.example credentials.json 

3. Install Dependencies  
   ```bash
   pip install -r requirements.txt

4. Run the API
   ```bash
   python main.py
