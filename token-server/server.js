/**
 * Nevira Token Server
 * Securely mints LiveKit access tokens for React clients
 */
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { AccessToken, RoomServiceClient } = require('livekit-server-sdk');

const app = express();

// Middleware
// Allow localhost and 127.0.0.1 (different ways the dev server can be accessed)
const allowedOrigins = [
  process.env.CORS_ORIGIN || 'http://localhost:5173',
  'http://localhost:5173',
  'http://127.0.0.1:5173',
];

app.use(cors({
  origin: (origin, callback) => {
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin)) return callback(null, true);
    // Fallback: allow any localhost/127.0.0.1 port during dev
    if (/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origin)) return callback(null, true);
    return callback(new Error('CORS not allowed for origin: ' + origin));
  },
  credentials: true,
}));
app.use(express.json());

// Configuration
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;
const PORT = process.env.PORT || 3001;

// Validate configuration
if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
  console.error('❌ ERROR: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env');
  process.exit(1);
}

// Single consolidated /token route with capacity check
app.post('/token', async (req, res) => {
  try {
    const { identity, roomName } = req.body;

    if (!identity) {
      return res.status(400).json({ error: 'identity is required' });
    }

    const room = roomName || 'nevira-room';

    // Enforce participant limit (default 2 to allow client + agent)
    const maxParticipants = parseInt(process.env.MAX_PARTICIPANTS || '2', 10);

    let participants = [];
    try {
      const info = await roomService.getRoom(room);
      participants = info.participants || [];
    } catch (err) {
      // Room may not exist yet; allow connection
      participants = [];
    }

    if (participants.length >= maxParticipants) {
      return res.status(403).json({ error: 'Room is full. Please try again later.' });
    }

    // Create access token
    const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity,
      ttl: '1h',
    });

    // Grant permissions for the room
    at.addGrant({
      room,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const token = await at.toJwt();

    console.log(`✅ Token generated for ${identity} in room ${room} (participants: ${participants.length}/${maxParticipants})`);

    res.json({ token, roomName: room });
  } catch (error) {
    console.error('Error generating token:', error);
    res.status(500).json({ error: 'Failed to generate token' });
  }
});

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    configured: !!(LIVEKIT_API_KEY && LIVEKIT_API_SECRET)
  });
});
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const roomService = new RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET);

// Start server
app.listen(PORT, () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🚀 Nevira Token Server Started');
  console.log('═══════════════════════════════════════════════');
  console.log(`📡 Listening on: http://localhost:${PORT}`);
  console.log(`🔑 API Key configured: ${LIVEKIT_API_KEY ? '✅' : '❌'}`);
  console.log(`🔐 API Secret configured: ${LIVEKIT_API_SECRET ? '✅' : '❌'}`);
  console.log(`🌐 CORS origin: ${process.env.CORS_ORIGIN || 'http://localhost:5173'}`);
  console.log('═══════════════════════════════════════════════');
});
