
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
