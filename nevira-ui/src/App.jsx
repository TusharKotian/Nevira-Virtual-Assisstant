import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';
import './App.css';

const TOKEN_SERVER = 'http://localhost:3001/token';
const LIVEKIT_URL = 'wss://deskto-ai-zog435cw.livekit.cloud';
const ROOM_NAME = 'nevira-room';

function App() {
  const [room, setRoom] = useState(null);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [muted, setMuted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [error, setError] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [quality, setQuality] = useState('Unknown');
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [autoConnect, setAutoConnect] = useState(false);
  const [fontSize, setFontSize] = useState('16');
  const [theme, setTheme] = useState('dark');
  const [micDevices, setMicDevices] = useState([]);
  const [selectedMicId, setSelectedMicId] = useState('');
  const [micLevel, setMicLevel] = useState(0);
  const [showEmailPopup, setShowEmailPopup] = useState(false);
  const [showEmailSentPopup, setShowEmailSentPopup] = useState(false);
  const [emailForm, setEmailForm] = useState({
    to: '',
    subject: '',
    body: ''
  });
  const [emailSending, setEmailSending] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const tools = [
    { key: 'get_weather', label: 'Weather', desc: 'Get weather for a city', prompt: 'What is the weather in London?' },
    { key: 'search_web', label: 'Web Search', desc: 'Search the internet', prompt: 'Search the web for latest AI news' },
    { key: 'send_email', label: 'Send Email', desc: 'Compose and send an email', prompt: 'Send an email to hr saying I will be late by 15 minutes' },
    { key: 'open_application', label: 'Open App', desc: 'Open common applications', prompt: 'Open calculator' },
    { key: 'close_application', label: 'Close App', desc: 'Close an application', prompt: 'Close calculator' },
    { key: 'open_website', label: 'Open Website', desc: 'Open popular websites', prompt: 'Open YouTube' },
    { key: 'search_google', label: 'Google Search', desc: 'Search in browser', prompt: 'Search Google for LiveKit agents' },
    { key: 'get_system_status', label: 'System Status', desc: 'CPU, memory, disk, battery', prompt: 'What is my system status?' },
    { key: 'get_time_and_date', label: 'Time & Date', desc: 'Current time and date', prompt: 'What is the time and date?' },
    { key: 'take_screenshot', label: 'Screenshot', desc: 'Capture your screen', prompt: 'Take a screenshot' },
  ];
  
  const localAudioRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const levelRafRef = useRef(null);

  // Get access token from server
  const getToken = async (identity) => {
    try {
      const response = await fetch(TOKEN_SERVER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identity, roomName: ROOM_NAME }),
      });
      
      if (!response.ok) {
        throw new Error(`Token request failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.token;
    } catch (err) {
      console.error('Error getting token:', err);
      throw err;
    }
  };

  // Connect to LiveKit room
  const connectToRoom = async () => {
    setConnecting(true);
    setError(null);

    try {
      // Generate unique identity
      const identity = `user_${Math.floor(Math.random() * 10000)}`;
      
      // Get token from server
      const token = await getToken(identity);
      
      // Create room instance
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
        stopLocalTrackOnUnpublish: true,
        publishDefaults: { video: false, audioBitrate: 32000 },
      });

      // Set up event listeners
      setupRoomListeners(newRoom);

      // Connect to room
      await newRoom.connect(LIVEKIT_URL, token);
      
      // Enable microphone
      await newRoom.localParticipant.setMicrophoneEnabled(true, {
        noiseSuppression: true,
        echoCancellation: true,
        autoGainControl: true,
        deviceId: selectedMicId || undefined,
      });

      // Ensure audio context is running (required for autoplay)
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
      } catch (e) {
        console.warn('Audio context initialization failed:', e);
      }

      // Setup mic level analyser
      setupMicLevelAnalyser(newRoom);
      
      setRoom(newRoom);
      setConnected(true);
      console.log('✅ Connected to room:', ROOM_NAME);
      
    } catch (err) {
      console.error('Connection error:', err);
      setError(err.message);
    } finally {
      setConnecting(false);
    }
  };

  // Setup analyser for mic level visualization
  const setupMicLevelAnalyser = (roomInstance) => {
    try {
      const publications = roomInstance.localParticipant.getTrackPublications();
      const audioPub = Array.from(publications.values()).find((p) => (p.kind === Track.Kind.Audio) || (p.track && p.track.kind === Track.Kind.Audio));
      let mediaStream = null;
      if (audioPub && audioPub.track && audioPub.track.mediaStreamTrack) {
        mediaStream = new MediaStream([audioPub.track.mediaStreamTrack]);
      }
      // Fallback: open a lightweight getUserMedia stream for level metering only
      const setupWithStream = (ms) => {
        const audioCtx = audioCtxRef.current || new (window.AudioContext || window.webkitAudioContext)();
        audioCtxRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(ms);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        source.connect(analyser);
        analyserRef.current = analyser;
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          analyser.getByteTimeDomainData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            const v = (dataArray[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / dataArray.length);
          setMicLevel(Math.min(100, Math.max(0, Math.round(rms * 220))));
          levelRafRef.current = requestAnimationFrame(tick);
        };
        if (levelRafRef.current) cancelAnimationFrame(levelRafRef.current);
        levelRafRef.current = requestAnimationFrame(tick);
      };
      if (mediaStream) {
        setupWithStream(mediaStream);
      } else {
        navigator.mediaDevices.getUserMedia({ audio: { deviceId: selectedMicId || undefined } })
          .then(setupWithStream)
          .catch(() => {});
      }
    } catch (e) {
      // ignore analyser failures
    }
  };

  // Set up room event listeners
  const setupRoomListeners = (room) => {
    // Track subscribed (remote audio from agent)
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log('Track subscribed:', track.kind, 'from', participant.identity);
      setLogs((l) => [{ ts: Date.now(), msg: `Subscribed ${track.kind} from ${participant.identity}` }, ...l].slice(0, 50));
      
      if (track.kind === Track.Kind.Audio) {
        const audioElement = track.attach();
        audioElement.autoplay = true;
        audioElement.playsInline = true;
        audioElement.muted = false;
        audioElement.volume = 1.0;
        if (remoteAudioRef.current) {
          remoteAudioRef.current.innerHTML = '';
          remoteAudioRef.current.appendChild(audioElement);
        }
        
        // Detect agent speaking
        if (participant.identity.includes('agent') || participant.identity.includes('nevira')) {
          setAgentSpeaking(true);
          setTimeout(() => setAgentSpeaking(false), 3000);
        }
      }
    });

    // When local track is published, re-wire analyser (fix mic meter not moving)
    room.on(RoomEvent.LocalTrackPublished, (_pub, participant) => {
      try {
        if (participant && participant.isLocal) {
          setupMicLevelAnalyser(room);
        }
      } catch {}
    });

    // Participant connected
    room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log('Participant connected:', participant.identity);
      setLogs((l) => [{ ts: Date.now(), msg: `+ ${participant.identity}` }, ...l].slice(0, 50));
      updateParticipants(room);
    });

    // Participant disconnected
    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      console.log('Participant disconnected:', participant.identity);
      setLogs((l) => [{ ts: Date.now(), msg: `- ${participant.identity}` }, ...l].slice(0, 50));
      updateParticipants(room);
    });

    // Speaking changed
    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const isLocalSpeaking = speakers.some(s => s.isLocal);
      setSpeaking(isLocalSpeaking);
    });

    // Disconnected
    room.on(RoomEvent.Disconnected, () => {
      console.log('Disconnected from room');
      setLogs((l) => [{ ts: Date.now(), msg: `Disconnected from room` }, ...l].slice(0, 50));
      setConnected(false);
      setRoom(null);
      if (levelRafRef.current) cancelAnimationFrame(levelRafRef.current);
    });

    // Connection quality changed
    room.on(RoomEvent.ConnectionQualityChanged, (q, participant) => {
      console.log('Connection quality:', q, participant.identity);
      if (participant.isLocal) setQuality(String(q));
    });

    // Data received from agent
    room.on(RoomEvent.DataReceived, (payload, participant) => {
      try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        console.log('Data received:', data);
        
        if (data.type === 'email_popup_trigger') {
          console.log('Triggering email popup from voice command');
          setShowEmailPopup(true);
          setLogs((l) => [{ ts: Date.now(), msg: 'Email popup opened via voice command' }, ...l].slice(0, 50));
        } else if (data.type === 'assistant_message') {
          // Add assistant message to chat
          setMessages((prev) => [...prev, {
            id: Date.now(),
            sender: 'assistant',
            text: data.message || data.text,
            images: data.images || [],
            timestamp: Date.now()
          }]);
        }
      } catch (e) {
        // Try to add as text message if not JSON
        const text = new TextDecoder().decode(payload);
        if (text && text.trim()) {
          setMessages((prev) => [...prev, {
            id: Date.now(),
            sender: 'assistant',
            text: text,
            images: [],
            timestamp: Date.now()
          }]);
        }
      }
    });

  };

  // Update participants list
  const updateParticipants = (room) => {
    const allParticipants = Array.from(room.remoteParticipants.values()).map(p => ({
      identity: p.identity,
      isAgent: p.identity.includes('agent') || p.identity.includes('nevira'),
    }));
    setParticipants(allParticipants);
  };

  // Disconnect from room
  const disconnectFromRoom = async () => {
    if (room) {
      await room.disconnect();
      setRoom(null);
      setConnected(false);
      setParticipants([]);
      if (levelRafRef.current) cancelAnimationFrame(levelRafRef.current);
    }
  };

  // Toggle mute
  const toggleMute = async () => {
    if (room) {
      const newMuted = !muted;
      await room.localParticipant.setMicrophoneEnabled(!newMuted);
      setMuted(newMuted);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
      if (levelRafRef.current) cancelAnimationFrame(levelRafRef.current);
    };
  }, [room]);

  // Load and persist settings
  useEffect(() => {
    try {
      const prefs = JSON.parse(localStorage.getItem('nevira_prefs') || '{}');
      if (prefs.autoConnect !== undefined) setAutoConnect(!!prefs.autoConnect);
      if (prefs.fontSize) setFontSize(String(prefs.fontSize));
      if (prefs.theme) setTheme(prefs.theme);
      if (prefs.selectedMicId) setSelectedMicId(prefs.selectedMicId);
    } catch {}
  }, []);

  useEffect(() => {
    const prefs = { autoConnect, fontSize, theme, selectedMicId };
    try { localStorage.setItem('nevira_prefs', JSON.stringify(prefs)); } catch {}
    document.documentElement.style.fontSize = `${fontSize}px`;
    document.documentElement.setAttribute('data-theme', theme);
  }, [autoConnect, fontSize, theme, selectedMicId]);

  // Auto-connect based on setting
  useEffect(() => {
    if (autoConnect && !connected && !connecting) {
      connectToRoom();
    }
  }, [autoConnect]);

  // Enumerate audio input devices
  const refreshDevices = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      const devices = await navigator.mediaDevices.enumerateDevices();
      const mics = devices.filter((d) => d.kind === 'audioinput');
      setMicDevices(mics);
      if (!selectedMicId && mics[0]) setSelectedMicId(mics[0].deviceId);
    } catch (e) {
      // ignore
    }
  };
  // Trigger a tool by sending a command as a data message
  const triggerTool = async (t) => {
    if (!connected || !room) return;
    
    // Special handling for email tool - show popup instead of sending command
    if (t.key === 'send_email') {
      setShowEmailPopup(true);
      return;
    }
    
    try {
      const payload = { type: 'user_command', text: t.prompt, ts: Date.now() };
      const data = new TextEncoder().encode(JSON.stringify(payload));
      await room.localParticipant.publishData(data, true);
      setLogs((l) => [{ ts: Date.now(), msg: `Triggered tool: ${t.label}` }, ...l].slice(0, 50));
    } catch (e) {
      setError('Failed to send command to assistant. Please speak the request.');
    }
  };

  // Handle email form submission
  const handleEmailSubmit = async () => {
    if (!emailForm.to || !emailForm.subject || !emailForm.body) {
      setError('Please fill in all email fields');
      return;
    }

    if (!connected || !room) {
      setError('Not connected to assistant');
      return;
    }

    setEmailSending(true);
    try {
      const emailCommand = `Send an email to ${emailForm.to} with subject "${emailForm.subject}" and message "${emailForm.body}"`;
      const payload = { type: 'user_command', text: emailCommand, ts: Date.now() };
      const data = new TextEncoder().encode(JSON.stringify(payload));
      await room.localParticipant.publishData(data, true);
      
      setLogs((l) => [{ ts: Date.now(), msg: `Sending email to ${emailForm.to}` }, ...l].slice(0, 50));
      setShowEmailPopup(false);
      setEmailForm({ to: '', subject: '', body: '' });
      
      // Show success popup after a short delay
      setTimeout(() => {
        setShowEmailSentPopup(true);
        setEmailSending(false);
      }, 1000);
      
    } catch (e) {
      setError('Failed to send email command to assistant');
      setEmailSending(false);
    }
  };

  // Handle email popup close
  const handleEmailClose = () => {
    setShowEmailPopup(false);
    setEmailForm({ to: '', subject: '', body: '' });
  };

  // Handle email sent popup close
  const handleEmailSentClose = () => {
    setShowEmailSentPopup(false);
  };

  // Send text message
  const sendMessage = async () => {
    if (!inputMessage.trim() || !connected || !room) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputMessage,
      images: [],
      timestamp: Date.now()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');

    try {
      const payload = { type: 'user_command', text: inputMessage, ts: Date.now() };
      const data = new TextEncoder().encode(JSON.stringify(payload));
      await room.localParticipant.publishData(data, true);
    } catch (e) {
      setError('Failed to send message. Please speak the request.');
    }
  };

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    refreshDevices();
    
    // Handle user interaction to enable audio playback
    const handleUserInteraction = async () => {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
      } catch (e) {
        // ignore
      }
    };
    
    // Add event listeners for user interaction
    document.addEventListener('click', handleUserInteraction, { once: true });
    document.addEventListener('touchstart', handleUserInteraction, { once: true });
    document.addEventListener('keydown', handleUserInteraction, { once: true });
    
    return () => {
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('touchstart', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
    };
  }, []);

  return (
    <div className="app">
      <div className="shell">
        <aside className="sidebar">
          <div className="brand">
            <span className="logo-icon">🎙️</span>
            <h2>Nevira</h2>
          </div>
          <nav className="nav">
            <button className={`nav-btn ${activeTab==='Chat'?'active':''}`} onClick={() => setActiveTab('Chat')}>Chat</button>
            <button className={`nav-btn ${activeTab==='Dashboard'?'active':''}`} onClick={() => setActiveTab('Dashboard')}>Dashboard</button>
            <button className={`nav-btn ${activeTab==='Voice'?'active':''}`} onClick={() => setActiveTab('Voice')}>Voice</button>
            <button className={`nav-btn ${activeTab==='Tools'?'active':''}`} onClick={() => setActiveTab('Tools')}>Tools</button>
            <button className={`nav-btn ${activeTab==='Settings'?'active':''}`} onClick={() => setActiveTab('Settings')}>Settings</button>
          </nav>
          <div className="sidebar-footer">
            <div className="status-dot"></div>
            <span>{connected ? 'Online' : 'Offline'}</span>
          </div>
        </aside>

        <main className="main">
          <div className="toolbar">
            <div className="left">
              <div className="title">AI Voice Assistant</div>
            </div>
            <div className="right">
              <div className="metric"><span>Quality</span><strong>{quality}</strong></div>
            </div>
          </div>

          <div className="grid">
            <section className="panel">
              <div className="panel-header">Session</div>
              <div className="panel-body">
                <div className="card">
          {error && (
            <div className="error">
              <span>⚠️</span> {error}
            </div>
          )}

          {!connected ? (
            <div className="connect-section">
              <div className="status-badge offline">Offline</div>
              <p className="description">
                Connect to start talking with Nevira, your AI assistant powered by Google Gemini.
              </p>
              <button 
                className="btn btn-primary btn-large"
                onClick={connectToRoom}
                disabled={connecting}
              >
                {connecting ? (
                  <>
                    <span className="spinner"></span>
                    Connecting...
                  </>
                ) : (
                  <>
                    <span>🔗</span>
                    Connect to Nevira
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="connected-section">
              <div className="status-row">
                <div className="status-badge online">
                  <span className="pulse"></span>
                  Connected
                </div>
                <div className="status-metrics">
                  <span>Quality: {quality}</span>
                </div>
              </div>

              <div className="voice-indicator">
                {speaking && (
                  <div className="speaking-animation">
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                  </div>
                )}
                {agentSpeaking && (
                  <div className="agent-speaking">
                    <span>🤖</span> Nevira is speaking...
                  </div>
                )}
                {!speaking && !agentSpeaking && (
                  <p className="idle-text">Listening... speak to Nevira</p>
                )}
              </div>

              <div className="controls">
                <button 
                  className={`btn ${muted ? 'btn-danger' : 'btn-secondary'}`}
                  onClick={toggleMute}
                >
                  <span>{muted ? '🔇' : '🎤'}</span>
                  {muted ? 'Unmute' : 'Mute'}
                </button>
                
                <button 
                  className="btn btn-danger"
                  onClick={disconnectFromRoom}
                >
                  <span>📞</span>
                  Disconnect
                </button>
              </div>

              <div className="layout">
                <div className="panel">
                  <h3>Participants</h3>
                  <div className="participant-list">
                    {participants.map((p, i) => (
                      <div key={i} className="participant">
                        <span>{p.isAgent ? '🤖' : '👤'}</span>
                        <span>{p.identity}</span>
                      </div>
                    ))}
                    {participants.length === 0 && (
                      <div className="participant empty">No remote participants yet</div>
                    )}
                  </div>
                </div>
                <div className="panel">
                  <h3>Tips</h3>
                  <ul className="tips">
                    <li>Ask: "What’s the weather in London?"</li>
                    <li>Say: "Open calculator"</li>
                    <li>Try: "What’s my system status?"</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
                </div>
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">Participants</div>
              <div className="panel-body scroll">
                <div className="participant-list">
                  {participants.map((p, i) => (
                    <div key={i} className="participant">
                      <span>{p.isAgent ? '🤖' : '👤'}</span>
                      <span>{p.identity}</span>
                    </div>
                  ))}
                  {participants.length === 0 && (
                    <div className="participant empty">No remote participants yet</div>
                  )}
                </div>
              </div>
            </section>

            <section className="panel stretch">
              <div className="panel-header">{activeTab}</div>
              <div className="panel-body scroll">
                {activeTab === 'Chat' && (
                  <div className="chat-container">
                    <div className="chat-messages">
                      {messages.length === 0 && (
                        <div className="chat-empty">
                          <div className="chat-empty-icon">💬</div>
                          <p>Start a conversation with Nevira</p>
                          <p className="chat-empty-hint">Type a message or use voice commands</p>
                        </div>
                      )}
                      {messages.map((msg) => (
                        <div key={msg.id} className={`chat-message ${msg.sender === 'user' ? 'user' : 'assistant'}`}>
                          <div className="chat-message-header">
                            <span className="chat-avatar">{msg.sender === 'user' ? '👤' : '🤖'}</span>
                            <span className="chat-sender">{msg.sender === 'user' ? 'You' : 'Nevira'}</span>
                            <span className="chat-time">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <div className="chat-message-content">
                            {msg.text && (
                              <div className="chat-text" dangerouslySetInnerHTML={{ 
                                __html: msg.text.replace(/\n/g, '<br/>')
                                  .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
                              }} />
                            )}
                            {msg.images && msg.images.length > 0 && (
                              <div className="chat-images">
                                {msg.images.map((img, idx) => (
                                  <div key={idx} className="chat-image-container">
                                    <img 
                                      src={img.url || img} 
                                      alt={img.alt || `Image ${idx + 1}`}
                                      className="chat-image"
                                      onError={(e) => {
                                        e.target.style.display = 'none';
                                      }}
                                    />
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                    <div className="chat-input-container">
                      <input
                        type="text"
                        className="chat-input"
                        placeholder={connected ? "Type a message..." : "Connect to send messages"}
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            sendMessage();
                          }
                        }}
                        disabled={!connected}
                      />
                      <button 
                        className="chat-send-btn"
                        onClick={sendMessage}
                        disabled={!connected || !inputMessage.trim()}
                      >
                        <span>📤</span>
                      </button>
                    </div>
                  </div>
                )}
                {activeTab === 'Dashboard' && (
                  <div className="dashboard">
                    <div className="stat">
                      <div className="label">Connection Quality</div>
                      <div className="value accent">{quality}</div>
                    </div>
                    <div className="stat">
                      <div className="label">Participants</div>
                      <div className="value">{participants.length}</div>
                    </div>
                    <div className="stat">
                      <div className="label">Agent Speaking</div>
                      <div className="value">{agentSpeaking ? 'Yes' : 'No'}</div>
                    </div>
                    <div className="stat">
                      <div className="label">Local Speaking</div>
                      <div className="value">{speaking ? 'Yes' : 'No'}</div>
                    </div>
                    <div className="stat">
                      <div className="label">Recent Events</div>
                      <div className="value">{logs.length}</div>
                    </div>
                  </div>
                )}
                {activeTab === 'Voice' && (
                  <div>
                    <div className="meter">
                      <div className="meter-bar" style={{ width: `${micLevel}%` }}></div>
                      <div className="meter-label">Mic level: {micLevel}%</div>
                    </div>
                    <div className="settings-row">
                      <label>Microphone</label>
                      <select value={selectedMicId} onChange={async (e) => {
                        const id = e.target.value;
                        setSelectedMicId(id);
                        if (room) {
                          await room.localParticipant.setMicrophoneEnabled(true, { deviceId: id });
                          setupMicLevelAnalyser(room);
                        }
                      }}>
                        {micDevices.map((d) => (
                          <option key={d.deviceId} value={d.deviceId}>{d.label || 'Microphone'}</option>
                        ))}
                      </select>
                      <button className="btn btn-secondary" onClick={refreshDevices}>Refresh</button>
                    </div>
                    <div className="logs" style={{ marginTop: 16 }}>
                      {logs.length === 0 && <div className="muted">Waiting for activity…</div>}
                      {logs.map((l, i) => (
                        <div key={i} className="log-row">{new Date(l.ts).toLocaleTimeString()} — {l.msg}</div>
                      ))}
                    </div>
                  </div>
                )}
                {activeTab === 'Tools' && (
                  <div>
                    {!connected ? (
                      <div className="muted" style={{ padding: '8px 0', fontWeight: 700 }}>Connect to use tools</div>
                    ) : null}
                    <div className="tools-grid">
                      {tools.map((t) => (
                        <button key={t.key} className="tool-card" disabled={!connected} onClick={() => triggerTool(t)}>
                          <div className="tool-title">{t.label}</div>
                          <div className="tool-desc">{t.desc}</div>
                          <div className="tool-prompt">{t.prompt}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {activeTab === 'Settings' && (
                  <div className="settings">
                    <div className="settings-row">
                      <label>Auto-connect</label>
                      <input type="checkbox" checked={autoConnect} onChange={(e) => setAutoConnect(e.target.checked)} />
                    </div>
                    <div className="settings-row">
                      <label>Theme</label>
                      <select value={theme} onChange={(e) => setTheme(e.target.value)}>
                        <option value="dark">Dark</option>
                        <option value="light">Light</option>
                      </select>
                    </div>
                    <div className="settings-row">
                      <label>Base font size</label>
                      <input type="number" min="12" max="22" value={fontSize} onChange={(e) => setFontSize(e.target.value)} />
                    </div>
                    <div className="settings-row">
                      <label>Microphone</label>
                      <select value={selectedMicId} onChange={(e) => setSelectedMicId(e.target.value)}>
                        {micDevices.map((d) => (
                          <option key={d.deviceId} value={d.deviceId}>{d.label || 'Microphone'}</option>
                        ))}
                      </select>
                      <button className="btn btn-secondary" onClick={refreshDevices}>Refresh</button>
                    </div>
                  </div>
                )}
              </div>
            </section>
          </div>

          <footer className="footer">
            <p>💡 Make sure the Python agent is running: <code>python agent.py dev</code></p>
            <p>🔧 Token server: <code>{TOKEN_SERVER}</code></p>
          </footer>

          {/* Hidden audio elements for playback */}
          <div style={{ display: 'none' }}>
            <div ref={localAudioRef} id="local-audio"></div>
            <div ref={remoteAudioRef} id="remote-audio"></div>
          </div>
        </main>
      </div>

      {/* Email Compose Popup Modal */}
      {showEmailPopup && (
        <div className="email-popup-overlay">
          <div className="email-popup">
            <div className="email-popup-header">
              <h3>📧 Send Email</h3>
              <button className="close-btn" onClick={handleEmailClose}>×</button>
            </div>
            <div className="email-popup-body">
              <div className="form-group">
                <label htmlFor="email-to">To:</label>
                <input
                  id="email-to"
                  type="email"
                  placeholder="recipient@example.com"
                  value={emailForm.to}
                  onChange={(e) => setEmailForm({...emailForm, to: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label htmlFor="email-subject">Subject:</label>
                <input
                  id="email-subject"
                  type="text"
                  placeholder="Email subject"
                  value={emailForm.subject}
                  onChange={(e) => setEmailForm({...emailForm, subject: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label htmlFor="email-body">Message:</label>
                <textarea
                  id="email-body"
                  placeholder="Type your message here..."
                  rows="6"
                  value={emailForm.body}
                  onChange={(e) => setEmailForm({...emailForm, body: e.target.value})}
                />
              </div>
            </div>
            <div className="email-popup-footer">
              <button className="btn btn-secondary" onClick={handleEmailClose}>
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleEmailSubmit}
                disabled={emailSending}
              >
                {emailSending ? (
                  <>
                    <span className="spinner"></span>
                    Sending...
                  </>
                ) : (
                  'Send Email'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Sent Confirmation Popup */}
      {showEmailSentPopup && (
        <div className="email-popup-overlay">
          <div className="email-sent-popup">
            <div className="email-sent-content">
              <div className="success-icon">✅</div>
              <h3>Email Sent Successfully!</h3>
              <p>Your email has been sent to {emailForm.to || 'the recipient'}.</p>
              <button className="btn btn-primary" onClick={handleEmailSentClose}>
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
