# Nevira Token Server

Secure token minting server for LiveKit authentication.

## Setup

```bash
# Install dependencies
npm install

# Copy .env.example to .env and configure
cp .env.example .env

# Edit .env with your LiveKit credentials
```

## Run

```bash
npm start
```

Server will start on http://localhost:3001

## Endpoints

### POST /token
Generate a LiveKit access token.

**Request:**
```json
{
  "identity": "user_123",
  "roomName": "nevira-room"
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "roomName": "nevira-room"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-12T...",
  "configured": true
}
```
