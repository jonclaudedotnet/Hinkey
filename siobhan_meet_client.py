#!/usr/bin/env python3
"""
Google Meet API Client for Siobhan
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SiobhanMeetClient:
    """Google Meet API client for Siobhan"""
    
    def __init__(self, credentials_path=None):
        self.credentials_path = credentials_path or 'credentials.json'
        self.token_path = 'token.json'
        self.scopes = [
            'https://www.googleapis.com/auth/meetings.space.created',
            'https://www.googleapis.com/auth/meetings.space.readonly',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
        self.service = None
        self.setup_authentication()
    
    def setup_authentication(self):
        """Set up Google API authentication"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build the service
        try:
            self.service = build('meet', 'v2', credentials=creds)
            print("✅ Google Meet API client authenticated")
        except Exception as e:
            print(f"❌ Failed to build Meet service: {e}")
            # Fallback to Calendar API for basic meeting info
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Using Calendar API as fallback")
    
    def create_meeting_space(self):
        """Create a new Google Meet space"""
        try:
            # Create a meeting space
            request_body = {}
            
            result = self.service.spaces().create(body=request_body).execute()
            
            meeting_url = result.get('meetingUri')
            space_name = result.get('name')
            
            print(f"✅ Meeting created: {meeting_url}")
            return {
                'url': meeting_url,
                'space_name': space_name,
                'result': result
            }
            
        except HttpError as e:
            print(f"❌ Error creating meeting: {e}")
            return None
    
    def get_meeting_info(self, space_name):
        """Get information about a meeting space"""
        try:
            result = self.service.spaces().get(name=space_name).execute()
            return result
        except HttpError as e:
            print(f"❌ Error getting meeting info: {e}")
            return None
    
    def join_meeting_as_bot(self, meeting_url):
        """
        Attempt to join meeting as bot
        Note: This is limited by Google Meet API capabilities
        """
        print("⚠️ Direct bot participation not supported by Google Meet API")
        print("   Consider using third-party meeting bot services:")
        print("   - Recall.ai")
        print("   - AssemblyAI Real-time")
        print("   - Daily.co bot framework")
        
        return False

def main():
    """Test the Google Meet API client"""
    print("🤖 Testing Google Meet API Client")
    print("=" * 40)
    
    # Check for credentials
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        print("   Download OAuth credentials from Google Cloud Console")
        print("   and save as 'credentials.json'")
        return
    
    try:
        # Create client
        client = SiobhanMeetClient()
        
        # Test creating a meeting
        meeting = client.create_meeting_space()
        
        if meeting:
            print(f"🎉 Success! Meeting URL: {meeting['url']}")
        else:
            print("❌ Failed to create meeting")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
