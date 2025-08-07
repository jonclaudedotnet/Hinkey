#!/usr/bin/env python3
"""
Google Meet API Setup for Siobhan
Direct API integration for meeting participation
"""

import json
import os
from pathlib import Path
import subprocess

def check_prerequisites():
    """Check if we have necessary tools and accounts"""
    print("🔍 Checking Prerequisites for Google Meet API...")
    
    requirements = {
        'google_account': "You'll need a Google Workspace account with Meet API access",
        'api_credentials': "Service account or OAuth credentials from Google Cloud Console",
        'meet_api_enabled': "Google Meet API enabled in Google Cloud Console",
        'python_libraries': "google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client"
    }
    
    print("📋 Requirements:")
    for req, desc in requirements.items():
        print(f"   • {desc}")
    
    return True

def create_api_setup_guide():
    """Create step-by-step API setup guide"""
    print("\n📚 Creating Google Meet API Setup Guide...")
    
    guide = """
# Google Meet API Setup Guide for Siobhan

## Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the Google Meet API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Meet API"
   - Click "Enable"

## Step 2: Authentication Setup

### Option A: Service Account (Recommended for bots)
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in service account details
4. Download the JSON key file
5. Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

### Option B: OAuth 2.0 (For user authentication)
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Download the JSON file

## Step 3: Required Scopes

For Google Meet API access, you'll need these scopes:
- `https://www.googleapis.com/auth/meetings.space.created`
- `https://www.googleapis.com/auth/meetings.space.readonly`
- `https://www.googleapis.com/auth/calendar.readonly` (for meeting details)

## Step 4: API Limitations

⚠️ Important: Google Meet API currently has limitations:
- Can create meetings and get meeting info
- Cannot directly join as a bot participant
- Real-time audio/video requires additional setup
- May need Google Workspace Admin approval

## Alternative: Meet Bot Frameworks

Consider these alternatives for actual bot participation:
1. **Recall.ai** - Meeting bot service with API
2. **AssemblyAI** - Real-time transcription with meeting bots
3. **Daily.co** - Video API with bot participants
4. **Agora.io** - Real-time communication with bot support
"""
    
    guide_path = Path("google_meet_api_guide.md")
    with open(guide_path, 'w') as f:
        f.write(guide)
    
    print(f"✅ Setup guide created: {guide_path}")
    return guide_path

def install_google_api_libraries():
    """Install required Google API libraries"""
    print("\n📦 Installing Google API Libraries...")
    
    libraries = [
        'google-auth',
        'google-auth-oauthlib', 
        'google-auth-httplib2',
        'google-api-python-client',
        'google-cloud-speech',  # For speech recognition
        'google-cloud-texttospeech'  # For TTS
    ]
    
    for lib in libraries:
        try:
            print(f"   Installing {lib}...")
            result = subprocess.run(['pip', 'install', lib], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {lib} installed")
            else:
                print(f"   ⚠️ {lib} installation warning: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Error installing {lib}: {e}")
    
    print("✅ Library installation complete")

def create_meet_api_client():
    """Create basic Google Meet API client template"""
    print("\n🔧 Creating Google Meet API Client Template...")
    
    client_code = '''#!/usr/bin/env python3
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
'''
    
    client_path = Path("siobhan_meet_client.py")
    with open(client_path, 'w') as f:
        f.write(client_code)
    
    print(f"✅ Meet API client created: {client_path}")
    return client_path

def create_bot_alternatives_guide():
    """Create guide for meeting bot alternatives"""
    print("\n🤖 Creating Meeting Bot Alternatives Guide...")
    
    alternatives = """
# Meeting Bot Alternatives for Siobhan

## Option 1: Recall.ai (Recommended)
- **Website**: https://recall.ai/
- **What it does**: Join meetings as a bot, record, transcribe
- **API**: REST API for bot control
- **Pricing**: Pay per meeting minute
- **Integration**: 
  ```python
  import requests
  
  # Start a bot in Google Meet
  response = requests.post('https://us-west-2.recall.ai/api/v1/bot', {
      'meeting_url': 'https://meet.google.com/xxx-xxx-xxx',
      'bot_name': 'Siobhan'
  })
  ```

## Option 2: AssemblyAI Real-time
- **Website**: https://www.assemblyai.com/
- **What it does**: Real-time transcription and audio processing
- **API**: WebSocket for live audio
- **Integration with meeting bots**: Yes
- **Features**: Speaker diarization, sentiment analysis

## Option 3: Daily.co Video API
- **Website**: https://daily.co/
- **What it does**: Video/audio API with bot participants
- **Features**: Custom meeting rooms, bot frameworks
- **Good for**: Building custom meeting experiences

## Option 4: Agora.io
- **Website**: https://www.agora.io/
- **What it does**: Real-time communication platform
- **Bot support**: Yes, can join as participant
- **Features**: Voice/video, recording, transcription

## Option 5: Symbl.ai
- **Website**: https://symbl.ai/
- **What it does**: Conversation intelligence API
- **Features**: Join meetings, real-time insights
- **Integration**: REST API and WebSocket

## Recommended Approach for Siobhan

1. **Use Recall.ai** for actual meeting participation
2. **Integrate with Dolores** for intelligent responses  
3. **Use our existing voice system** for TTS
4. **Keep the rolling audio buffer** for privacy

### Implementation Strategy:
```python
# 1. Use Recall.ai bot to join meeting
recall_bot = RecallBot()
bot_id = recall_bot.join_meeting(meeting_url)

# 2. Get real-time transcription
transcription = recall_bot.get_live_transcript(bot_id)

# 3. Process with Dolores when wake word detected
if 'siobhan' in transcription.lower():
    response = ask_dolores(transcription)
    recall_bot.speak(bot_id, response)
```
"""
    
    alternatives_path = Path("meeting_bot_alternatives.md")
    with open(alternatives_path, 'w') as f:
        f.write(alternatives)
    
    print(f"✅ Bot alternatives guide created: {alternatives_path}")
    return alternatives_path

def main():
    """Set up Google Meet API integration"""
    print("🚀 Google Meet API Setup for Siobhan")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    
    # Create setup guide
    guide_path = create_api_setup_guide()
    
    # Install libraries
    install_google_api_libraries()
    
    # Create API client template
    client_path = create_meet_api_client()
    
    # Create alternatives guide
    alternatives_path = create_bot_alternatives_guide()
    
    print("\n🎯 NEXT STEPS:")
    print("=" * 50)
    print("1. 📖 Read the setup guide:")
    print(f"   cat {guide_path}")
    print()
    print("2. 🔑 Get Google Cloud credentials:")
    print("   - Go to Google Cloud Console")
    print("   - Enable Google Meet API")
    print("   - Create OAuth credentials")
    print("   - Download as 'credentials.json'")
    print()
    print("3. 🧪 Test the API client:")
    print(f"   python3 {client_path}")
    print()
    print("4. 🤖 Consider bot alternatives:")
    print(f"   cat {alternatives_path}")
    print()
    print("💡 RECOMMENDATION: Use Recall.ai for actual meeting bots")
    print("   Google Meet API has limitations for real-time participation")

if __name__ == "__main__":
    main()