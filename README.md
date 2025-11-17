# Nevira  - Your Personal AI Voice Assistant

<div align="center">

**An intelligent, voice-powered AI assistant built with LiveKit and Google Gemini**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LiveKit](https://img.shields.io/badge/LiveKit-Agents-green.svg)](https://livekit.io/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Features

Nevira is a sophisticated AI assistant that can:

- 🎙️ **Wake Word Detection** - Activate with "Hey Google", "Alexa", "Jarvis" or custom wake words (24/7 background listening)
- ⌨️ **Global Hotkey** - Press Ctrl+Alt+N from anywhere to trigger Nevira instantly
- 🖱️ **Desktop Shortcuts** - One-click activation with batch scripts
- 🚀 **Auto-Start** - Runs on Windows startup for always-available assistance
-  **Voice Interaction** - Natural, real-time voice conversations using Google Gemini's Realtime API
- 🌐 **Web Search** - Search the internet using DuckDuckGo integration
-  **Weather Updates** - Get current weather information for any city
- 📧 **Email Management** - Send emails through Gmail SMTP
- 🤵 **Personality** - Speaks like a classy, slightly sarcastic butler
-  **Noise Cancellation** - Built-in noise suppression for clear audio
-  **Console Mode** - Text-based interaction for testing
- 🖥️ **Web Interface** - Visual interface with camera support (via LiveKit)

---


Nevira is built on the **LiveKit Agents** framework and uses **Google Gemini's Realtime API** for natural voice conversations.

### Workflow:

1. **User speaks** into microphone
2. **Audio captured** by configured audio input device
3. **Streamed to LiveKit** room via WebRTC with noise cancellation
4. **Nevira agent** receives audio in the LiveKit room
5. **Google Gemini** processes voice input in real-time
6. **LLM decides** if tool usage is needed (weather, search, email)
7. **Tools execute** and return results to the LLM
8. **Gemini generates** voice response with Aoede voice
9. **Audio streamed back** through LiveKit to user's speakers

---

## 🚀 Quick Start

### Standard Mode (Voice Interaction)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run in console mode
python agent.py console
```

### 🎙️ Wake Word Mode (24/7 Activation)

**NEW!** Trigger Nevira hands-free with voice commands or keyboard shortcuts!

```powershell
# Install wake word dependencies
pip install pvporcupine pyaudio pynput pywin32

# Get free Picovoice key from: https://console.picovoice.ai/
# Add to .env: PICOVOICE_ACCESS_KEY=your_key

# Start wake word service
.\start_wake_service.bat
# Say "Hey Google" or "Alexa" to activate!
```

**📚 Full wake word setup guide:** [`WAKE_WORD_SETUP.md`](WAKE_WORD_SETUP.md) | [`QUICK_START.md`](QUICK_START.md)

---

##  Installation

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Core packages:**
- `livekit-agents` - Agent framework
- `livekit-plugins-google` - Google Gemini integration
- `livekit-plugins-noise-cancellation` - Audio enhancement
- `ddgs` - DuckDuckGo search

**Wake word packages (optional):**
- `pvporcupine` - Wake word detection engine
- `pyaudio` - Audio input capture
- `pynput` - Global keyboard shortcuts
- `pywin32` - Windows service support
- `requests` - HTTP requests for weather
- `python-dotenv` - Environment variable management
- `sounddevice` - Audio device control

---

## Configuration

### Step 1: Create `.env` File

Copy the example environment file or create a new `.env` file with this content:

```env
# LiveKit Configuration (Required)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Google Gemini API (Required)
GOOGLE_API_KEY=your_google_api_key

# Gmail Configuration (Optional - for email tool)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Audio Device Configuration (Optional)
# Find device indices by running: python -c "import sounddevice; print(sounddevice.query_devices())"
AUDIO_INPUT_DEVICE_INDEX=1
AUDIO_INPUT_DEVICE_NAME=Microphone (Realtek(R) Audio)
AUDIO_OUTPUT_DEVICE_INDEX=3
AUDIO_OUTPUT_DEVICE_NAME=Speakers (Realtek(R) Audio)
```

### Step 2: Get LiveKit Credentials

1. Go to [LiveKit Cloud](https://cloud.livekit.io/)
2. Sign up for a free account
3. Create a new project
4. Copy the **URL**, **API Key**, and **API Secret**
5. Paste them into your `.env` file


### Step 3: Get Google API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy the key and paste it into `.env` as `GOOGLE_API_KEY`

### Step 4: Configure Gmail (Optional)

If you want to use the email sending feature:

1. Enable 2-Factor Authentication on your Gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Create a new app password for "Mail"
4. Copy the generated password
5. Add to `.env`:
   ```env
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_app_password
   ```



### Console Mode (Text & Voice)

Perfect for local testing:

```bash
python agent.py console
```

**Controls:**
- Press `[Ctrl+B]` to toggle between Text/Audio mode
- Press `[Q]` to quit
- Speak naturally when in Audio mode
- Type messages when in Text mode

**Example conversation:**
```
You: "What's the weather in London?"
Nevira: "Checking the weather for you now, sir. London: ⛅️ Partly cloudy, 15°C."

You: "Search the web for Python tutorials"
Nevira: "Roger Boss, searching now. I found several Python tutorials for beginners..."
```

### Development Mode (LiveKit Dashboard)

For web-based interaction with video:

```bash
python agent.py dev
```

### Run Everything at Once

To start the token server, web UI, and Python agent with a single command:

```bash
python run_all.py
```

This launcher spawns all three processes and streams their logs in one terminal. Press `Ctrl+C` to stop every service together.

This will:
1. Start the agent worker
2. Connect to your LiveKit cloud project
3. Wait for connections

**To interact:**
1. Open [LiveKit Dashboard](https://cloud.livekit.io/)
2. Go to your project
3. Click "Test Connection" or use the LiveKit Playground
4. Join the room and start speaking

### Production Deployment

Deploy to a server:

```bash
python agent.py start
```

---

## Project Structure

```
friday_jarvis/
│
├── agent.py                 # Main agent entry point
├── prompts.py              # AI personality & instructions
├── tools.py                # Function tools (weather, search, email)
├── requirements.txt        # Python dependencies
├── .env                    
├── .gitignore             
├── README.md             
│
├── venv/                  


### File Descriptions

#### `agent.py`
The main entry point that:
- Loads environment variables
- Configures audio devices
- Creates the Assistant class with Google Gemini LLM
- Sets up LiveKit session with noise cancellation
- Manages the agent lifecycle

#### `prompts.py`
Defines Nevira's personality:
- `AGENT_INSTRUCTION` - Personality traits and speaking style
- `SESSION_INSTRUCTION` - Greeting and task instructions

#### `tools.py`
Contains three function tools:
- `get_weather(city)` - Fetches weather from wttr.in
- `search_web(query)` - Searches using DuckDuckGo
- `send_email(to, subject, message)` - Sends email via Gmail

---

## Tools & Functions

Nevira has access to three powerful tools:

### 1. Weather Tool 

**Function:** `get_weather(city: str)`

**What it does:** Fetches current weather for any city

**API Used:** [wttr.in](https://wttr.in/)

**Example:**
```
User: "What's the weather in Tokyo?"
Nevira: "Tokyo: ☀️ Clear, 22°C"
```

### 2. Web Search Tool 

**Function:** `search_web(query: str)`

**What it does:** Searches the web and returns top 5 results

**API Used:** DuckDuckGo (via `ddgs` package)

**Example:**
```
User: "Search for the latest AI news"
Nevira: "I found several results: 1. Breaking AI News from CNN..."
```

**Returns:** Title, description, and URL for each result

### 3. Email Tool 

**Function:** `send_email(to_email: str, subject: str, message: str, cc_email: Optional[str])`

**What it does:** Sends emails through Gmail SMTP

**Requirements:** Gmail credentials in `.env`

**Example:**
```
User: "Send an email to john@example.com saying 'Meeting at 3pm'"
Nevira: "Email sent successfully to john@example.com, sir."
```












