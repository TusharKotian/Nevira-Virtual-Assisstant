# Nevira React UI

Modern web interface for Nevira AI Voice Assistant with real-time LiveKit integration.

## Features

- 🎙️ **Real-time Voice** - Talk to Nevira through your browser
- 🔊 **Live Audio** - Hear Nevira's responses instantly
- 🎨 **Modern UI** - Beautiful, responsive design
- 🔒 **Secure** - Token-based authentication
- 📊 **Live Status** - See who's speaking and connection quality
- 🎛️ **Controls** - Mute, unmute, connect, disconnect

## Architecture

```
React Client (Browser)
    ↓ Request token
Token Server (Node.js)
    ↓ Generate JWT
LiveKit Cloud
    ↔ Audio streams
Python Agent (agent.py)
    ↔ Google Gemini + Tools
```

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure

The app is pre-configured to connect to:
- Token Server: `http://localhost:3001`
- LiveKit: Your LiveKit cloud instance
- Room: `nevira-room`

To change these, edit `src/App.jsx`:

```javascript
const TOKEN_SERVER = 'http://localhost:3001/token';
const LIVEKIT_URL = 'wss://your-livekit-url';
const ROOM_NAME = 'nevira-room';
```

### 3. Start Development Server

```bash
npm run dev
```

App will open at: http://localhost:5173

## Usage

1. **Start Token Server** (in another terminal):
   ```bash
   cd ../token-server
   npm start
   ```

2. **Start Python Agent** (in another terminal):
   ```bash
   cd ..
   python agent.py dev
   ```

3. **Open React App**:
   - Go to http://localhost:5173
   - Click "Connect to Nevira"
   - Grant microphone permission
   - Start talking!

## Features

### Voice Interaction
- Click "Connect" to join the room
- Your microphone will be enabled automatically
- Speak naturally - Nevira will respond
- See visual indicators when you or Nevira are speaking

### Controls
- **Mute/Unmute** - Toggle your microphone
- **Disconnect** - Leave the conversation
- **Participants** - See who's in the room (you + agent)

### Visual Feedback
- 🟢 Green pulse when connected
- 🎤 Wave animation when you're speaking
- 🤖 Indicator when Nevira is responding
- 📊 Participant list showing agent status

## Customization

### Styling
Edit `src/App.css` to customize:
- Colors and gradients
- Button styles
- Animations
- Layout

### Functionality
Edit `src/App.jsx` to add:
- Push-to-talk mode
- Volume controls
- Recording functionality
- Chat messages
- Advanced audio processing

## Build for Production

```bash
npm run build
```

Output in `dist/` folder. Deploy to:
- Vercel
- Netlify
- GitHub Pages
- Any static hosting

## Troubleshooting

### Can't connect to token server
- Make sure token server is running: `cd ../token-server && npm start`
- Check CORS settings in token server
- Verify port 3001 is not in use

### No audio from agent
- Confirm Python agent is running: `python agent.py dev`
- Check that agent joins same room: `nevira-room`
- Look for agent in participants list
- Check browser console for errors

### Microphone permission denied
- Grant permission when browser asks
- Check browser settings: chrome://settings/content/microphone
- Try HTTPS if on mobile (mic requires secure context)

### Connection quality issues
- Check internet connection
- Verify LiveKit URL is correct
- Look at LiveKit dashboard for room status

## Development

### Project Structure
```
nevira-ui/
├── index.html          # HTML entry point
├── package.json        # Dependencies
├── vite.config.js      # Vite configuration
└── src/
    ├── main.jsx        # React entry point
    ├── App.jsx         # Main component
    └── App.css         # Styles
```

### Key Dependencies
- `react` - UI framework
- `livekit-client` - LiveKit WebRTC SDK
- `vite` - Build tool

### Adding Features

**Add chat messages:**
```javascript
import { DataPacket_Kind, RoomEvent } from 'livekit-client';

room.on(RoomEvent.DataReceived, (payload, participant) => {
  const message = new TextDecoder().decode(payload);
  console.log('Message from', participant.identity, ':', message);
});
```

**Send data to agent:**
```javascript
const encoder = new TextEncoder();
const data = encoder.encode(JSON.stringify({ command: 'search', query: 'weather' }));
await room.localParticipant.publishData(data, DataPacket_Kind.RELIABLE);
```

## Production Considerations

### Security
- Use HTTPS in production
- Implement rate limiting on token server
- Add user authentication
- Validate room names

### Performance
- Enable adaptive streaming
- Use dynacast for bandwidth optimization
- Implement reconnection logic
- Add connection quality indicators

### Monitoring
- Log connection events
- Track audio quality metrics
- Monitor token generation
- Set up error tracking (Sentry, etc.)

## Resources

- [LiveKit Docs](https://docs.livekit.io/)
- [React LiveKit Components](https://github.com/livekit/components-js)
- [Vite Documentation](https://vitejs.dev/)

## Support

Check the logs in browser console (F12) for detailed error messages.

For LiveKit issues, check: https://livekit.io/docs/guides/troubleshooting/
