
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
