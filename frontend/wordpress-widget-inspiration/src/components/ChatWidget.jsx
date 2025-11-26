import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import BookingFlow from './BookingFlow';
import ParkingFlow from './ParkingFlow';
import TranscriptUpload from './TranscriptUpload';
import QuickReplies from './QuickReplies';
import './ChatWidget.css';

const API_BASE = '/api';

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'bot',
      text: "Hi there! 👋 I'm Amali, your friendly assistant at Functiomed. I'm here to help you with anything you need - whether it's booking appointments, finding information about our services, or reserving parking. What can I help you with today?",
      timestamp: new Date()
    }
  ]);
  const [sessionId, setSessionId] = useState(null);
  const [bookingState, setBookingState] = useState(null);
  const [parkingState, setParkingState] = useState(null);
  const [showTranscriptUpload, setShowTranscriptUpload] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true); // Voice enabled by default
  const [hasPendingAudio, setHasPendingAudio] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false); // Track if bot is currently speaking
  const [userInteracted, setUserInteracted] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true); // Track if auto-scroll is enabled
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null); // Reference to the scrollable container
  const audioRef = useRef(null);
  const pendingAudioRef = useRef(null); // Track pending audio that couldn't play due to autoplay
  const isVoiceEnabledRef = useRef(true); // Track voice state with ref for immediate access - enabled by default
  const ttsCancelledRef = useRef(false); // Track if TTS should be cancelled
  const pendingTimeoutsRef = useRef([]); // Track pending timeouts to cancel them
  const welcomeSpokenRef = useRef(false); // Track if welcome message has been spoken
  const welcomeAudioUrlRef = useRef(null); // Pre-loaded welcome audio URL
  const isUserScrollingRef = useRef(false); // Track if user is actively scrolling

  useEffect(() => {
    // Initialize session
    if (!sessionId) {
      setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }
  }, [sessionId]);

  // Sync ref with state to ensure consistency
  useEffect(() => {
    isVoiceEnabledRef.current = isVoiceEnabled;
  }, [isVoiceEnabled]);

  // Smart auto-scroll: only scroll if user hasn't manually scrolled up
  useEffect(() => {
    if (shouldAutoScroll && !isUserScrollingRef.current) {
      scrollToBottom();
    }
  }, [messages, isTyping, shouldAutoScroll]);

  // Detect when user scrolls manually
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    const handleScroll = () => {
      // Prevent scroll detection during programmatic scrolling
      if (isUserScrollingRef.current) return;

      const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

      // If user is more than 100px away from bottom, disable auto-scroll
      // If user scrolls back to within 50px of bottom, re-enable auto-scroll
      if (distanceFromBottom > 100) {
        setShouldAutoScroll(false);
      } else if (distanceFromBottom < 50) {
        setShouldAutoScroll(true);
      }
    };

    scrollContainer.addEventListener('scroll', handleScroll);
    return () => scrollContainer.removeEventListener('scroll', handleScroll);
  }, []);

  // Pre-load welcome message audio when component mounts
  useEffect(() => {
    const welcomeMessage = messages.find(m => m.id === 'welcome') || messages[0];
    if (welcomeMessage && welcomeMessage.text && !welcomeAudioUrlRef.current) {
      console.log('📥 Pre-loading welcome message audio...');
      
      // Pre-load the audio in the background
      fetch(`${API_BASE}/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: welcomeMessage.text })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`TTS API error: ${response.status}`);
          }
          return response.blob();
        })
        .then(blob => {
          const audioUrl = URL.createObjectURL(blob);
          welcomeAudioUrlRef.current = audioUrl;
          console.log('✅ Welcome message audio pre-loaded and ready');
        })
        .catch(error => {
          console.error('Error pre-loading welcome audio:', error);
        });
    }
    
    // Cleanup on unmount
    return () => {
      if (welcomeAudioUrlRef.current) {
        URL.revokeObjectURL(welcomeAudioUrlRef.current);
        welcomeAudioUrlRef.current = null;
      }
    };
  }, [messages]);

  // Auto-speak welcome message when chatbot opens and voice is enabled
  useEffect(() => {
    if (isOpen && isVoiceEnabled && !welcomeSpokenRef.current) {
      // Unlock audio context when chatbot opens (opening counts as user interaction)
      const unlockAudio = () => {
        const silentAudio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=');
        silentAudio.volume = 0.01;
        silentAudio.play().then(() => {
          console.log('🔓 Audio context unlocked on chatbot open');
          silentAudio.pause();
          silentAudio.remove();
          setUserInteracted(true);
        }).catch(() => {
          console.log('Audio context unlock attempted');
          setUserInteracted(true);
        });
      };
      
      unlockAudio();
      
      // Use pre-loaded audio if available, otherwise fall back to TTS API
      if (welcomeAudioUrlRef.current) {
        welcomeSpokenRef.current = true;
        console.log('🎤 Playing pre-loaded welcome message instantly...');
        
        // Create a new audio instance from the pre-loaded blob URL
        const audio = new Audio(welcomeAudioUrlRef.current);
        audio.volume = 1.0;
        audioRef.current = audio;
        
        audio.onplay = () => {
          setIsSpeaking(true);
        };
        
        audio.onended = () => {
          console.log('Welcome audio playback ended');
          setIsSpeaking(false);
          audioRef.current = null;
        };
        
        audio.onpause = () => {
          setIsSpeaking(false);
        };
        
        audio.onerror = (error) => {
          console.error('Welcome audio error:', error);
          setIsSpeaking(false);
          audioRef.current = null;
        };
        
        // Play immediately (no delay needed for pre-loaded audio)
        audio.play()
          .then(() => {
            console.log('✅ Pre-loaded welcome audio started playing instantly');
          })
          .catch(err => {
            console.error('Could not play pre-loaded audio:', err);
            // Fallback to TTS API if pre-loaded audio fails
            const welcomeMessage = messages.find(m => m.id === 'welcome') || messages[0];
            if (welcomeMessage && welcomeMessage.text) {
              playTextToSpeech(welcomeMessage.text).catch(error => {
                console.error('Error speaking welcome message:', error);
              });
            }
          });
      } else {
        // Fallback: use TTS API if pre-loaded audio not ready
        const welcomeMessage = messages.find(m => m.id === 'welcome') || messages[0];
        if (welcomeMessage && welcomeMessage.text) {
          welcomeSpokenRef.current = true;
          console.log('🎤 Pre-loaded audio not ready, using TTS API...');
          setTimeout(() => {
            playTextToSpeech(welcomeMessage.text).catch(err => {
              console.error('Error speaking welcome message:', err);
            });
          }, 300);
        }
      }
    }
    
    // Reset welcome spoken flag when chat closes
    if (!isOpen) {
      welcomeSpokenRef.current = false;
    }
  }, [isOpen, isVoiceEnabled, messages]);

  // Track user interaction for audio autoplay
  useEffect(() => {
    // When voice is enabled, mark user interaction and try to play pending audio
    if (isVoiceEnabled && pendingAudioRef.current) {
      const { audio, audioUrl } = pendingAudioRef.current;
      audioRef.current = audio;
      pendingAudioRef.current = null;
      
      // User has interacted (enabled voice), so play should work
      audio.play()
        .then(() => {
          console.log('✅ Playing pending audio after enabling voice');
          setHasPendingAudio(false);
        })
        .catch(err => {
          console.error('❌ Could not play pending audio:', err);
          URL.revokeObjectURL(audioUrl);
          audioRef.current = null;
          setHasPendingAudio(false);
        });
    }
  }, [isVoiceEnabled]);

  // Cleanup audio when component unmounts
  useEffect(() => {
    return () => {
      // Cancel all pending timeouts
      pendingTimeoutsRef.current.forEach(timeoutId => clearTimeout(timeoutId));
      pendingTimeoutsRef.current = [];
      
      // Stop audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      // Clean up pending audio
      if (pendingAudioRef.current) {
        URL.revokeObjectURL(pendingAudioRef.current.audioUrl);
        pendingAudioRef.current = null;
      }
    };
  }, []);

  // Stop audio when voice is disabled
  useEffect(() => {
    if (!isVoiceEnabled && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsSpeaking(false);
    }
  }, [isVoiceEnabled]);

  const scrollToBottom = () => {
    if (!messagesEndRef.current) return;

    // Mark that we're programmatically scrolling
    isUserScrollingRef.current = true;

    messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });

    // Reset the flag after scroll animation completes (typically ~300-500ms for smooth scroll)
    setTimeout(() => {
      isUserScrollingRef.current = false;
    }, 600);
  };

  const addMessage = (text, type = 'user', sources = null, quickReplies = null, bookingStep = null, availableDates = null) => {
    const newMessage = {
      id: Date.now().toString(),
      type,
      text,
      sources,
      quickReplies,
      bookingStep,
      availableDates,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    
    // Note: TTS is now handled in handleSendMessage to start immediately
  };

  const playTextToSpeech = async (text) => {
    // Check if voice is still enabled before starting
    if (!isVoiceEnabledRef.current) {
      console.log('🔇 Voice disabled, cancelling TTS');
      return;
    }

    try {
      console.log('🎤 Starting TTS for text:', text.substring(0, 50) + '...');
      
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      // Clear cancellation flag
      ttsCancelledRef.current = false;

      console.log('📡 Calling TTS API (streaming)...');
      
      // Use fetch with streaming for faster playback
      const response = await fetch(`${API_BASE}/text-to-speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
      });

      // Check again if voice was disabled during API call
      if (!isVoiceEnabledRef.current || ttsCancelledRef.current) {
        console.log('🔇 Voice disabled during TTS, aborting');
        return;
      }

      if (!response.ok) {
        throw new Error(`TTS API error: ${response.status}`);
      }

      // Read ALL chunks first to ensure complete audio before playing
      // This prevents audio from stopping mid-sentence
      const reader = response.body.getReader();
      const chunks = [];
      let totalLength = 0;

      console.log('📥 Reading audio stream...');
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        // Check cancellation
        if (!isVoiceEnabledRef.current || ttsCancelledRef.current) {
          console.log('🔇 Voice disabled, cancelling stream');
          reader.cancel();
          return;
        }

        chunks.push(value);
        totalLength += value.length;
      }

      console.log('✅ All chunks received, total size:', totalLength, 'bytes');

      // Check cancellation after all chunks received
      if (!isVoiceEnabledRef.current || ttsCancelledRef.current) {
        console.log('🔇 Voice disabled, aborting');
        return;
      }

      // Create complete blob from all chunks
      const blob = new Blob(chunks, { type: 'audio/mpeg' });
      
      if (blob.size === 0) {
        console.error('Empty audio response');
        return;
      }
      
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.volume = 1.0;
      
      // Set up event handlers
      audio.onplay = () => {
        console.log('Audio playback started');
        setIsSpeaking(true);
      };

      audio.onended = () => {
        console.log('Audio playback ended');
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        pendingAudioRef.current = null;
        setHasPendingAudio(false);
      };

      audio.onpause = () => {
        console.log('Audio playback paused');
        setIsSpeaking(false);
      };

      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        pendingAudioRef.current = null;
        setHasPendingAudio(false);
      };
      
      // Try to play complete audio
      const attemptPlay = async () => {
        if (!isVoiceEnabledRef.current || ttsCancelledRef.current) {
          audio.pause();
          URL.revokeObjectURL(audioUrl);
          audioRef.current = null;
          return;
        }

        try {
          await audio.play();
          console.log('✅ Audio playback started (complete audio)');
          setIsSpeaking(true);
          pendingAudioRef.current = null;
          setHasPendingAudio(false);
        } catch (playError) {
          console.error('Audio play() failed:', playError);
          
          if (isVoiceEnabledRef.current && !ttsCancelledRef.current && 
              (playError.name === 'NotAllowedError' || playError.name === 'NotSupportedError')) {
            pendingAudioRef.current = { audio, audioUrl };
            setHasPendingAudio(true);
          } else {
            URL.revokeObjectURL(audioUrl);
            audioRef.current = null;
          }
        }
      };

      audio.load();
      if (audio.readyState >= 2) {
        attemptPlay();
      } else {
        const timeoutId = setTimeout(() => {
          const index = pendingTimeoutsRef.current.indexOf(timeoutId);
          if (index > -1) {
            pendingTimeoutsRef.current.splice(index, 1);
          }
          attemptPlay();
        }, 100);
        pendingTimeoutsRef.current.push(timeoutId);
        
        audio.addEventListener('canplay', () => {
          clearTimeout(timeoutId);
          const index = pendingTimeoutsRef.current.indexOf(timeoutId);
          if (index > -1) {
            pendingTimeoutsRef.current.splice(index, 1);
          }
          attemptPlay();
        }, { once: true });
      }

      console.log('✅ TTS streaming completed, total size:', totalLength, 'bytes');
    } catch (error) {
      console.error('Text-to-speech error:', error);
      
      if (error.message?.includes('API key')) {
        alert('ElevenLabs API key not configured. Please add ELEVENLABS_API_KEY to your backend .env file.');
      }
    }
  };

  const toggleVoice = () => {
    const newState = !isVoiceEnabled;
    setIsVoiceEnabled(newState);
    isVoiceEnabledRef.current = newState; // Update ref immediately
    setUserInteracted(true); // Mark that user has interacted
    
    console.log('🔊 Voice toggled:', newState);
    
    // Stop audio if disabling
    if (!newState) {
      // Set cancellation flag
      ttsCancelledRef.current = true;
      
      // Cancel all pending timeouts
      pendingTimeoutsRef.current.forEach(timeoutId => clearTimeout(timeoutId));
      pendingTimeoutsRef.current = [];
      
      // Stop and clean up current audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
        setIsSpeaking(false);
      }
      
      // Clean up pending audio
      if (pendingAudioRef.current) {
        URL.revokeObjectURL(pendingAudioRef.current.audioUrl);
        pendingAudioRef.current = null;
        setHasPendingAudio(false);
      }
    } else {
      // Clear cancellation flag when enabling
      ttsCancelledRef.current = false;
      // User clicked to enable voice - unlock audio context
      // Create a silent audio and play it to unlock the audio context
      const unlockAudio = () => {
        const silentAudio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=');
        silentAudio.volume = 0.01;
        silentAudio.play().then(() => {
          console.log('🔓 Audio context unlocked');
          silentAudio.pause();
          silentAudio.remove();
        }).catch(() => {
          console.log('Audio context unlock attempted');
        });
      };
      
      unlockAudio();
      
      // Try to play any pending audio that was blocked by autoplay
      if (pendingAudioRef.current) {
        const { audio, audioUrl } = pendingAudioRef.current;
        audioRef.current = audio;
        pendingAudioRef.current = null;
        
        // Since user just clicked, this should work now
        setTimeout(() => {
          audio.play()
            .then(() => {
              console.log('✅ Pending audio started playing after user interaction');
              setHasPendingAudio(false);
            })
            .catch(err => {
              console.error('❌ Could not play pending audio:', err);
              URL.revokeObjectURL(audioUrl);
              audioRef.current = null;
              setHasPendingAudio(false);
            });
        }, 100);
      } else if (audioRef.current && audioRef.current.paused) {
        // Try to play current audio if it's paused
        setTimeout(() => {
          if (isVoiceEnabledRef.current && !ttsCancelledRef.current) {
            audioRef.current?.play().catch(err => {
              console.error('Could not play current audio:', err);
            });
          }
        }, 100);
      }
      // Removed: Don't auto-speak last message when enabling voice
      // This was causing the issue where voice would speak after being disabled
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    // Re-enable auto-scroll when user sends a message
    setShouldAutoScroll(true);

    addMessage(text, 'user');

    // Check for parking intent
    if (text.toLowerCase().includes('parking') || text.toLowerCase().includes('park')) {
      setParkingState({ step: 'init' });
      addMessage("I'll help you reserve parking. Let me check availability...", 'bot');
      return;
    }

    // Check for transcript intent
    if (text.toLowerCase().includes('transcript') || text.toLowerCase().includes('audio')) {
      setShowTranscriptUpload(true);
      return;
    }

    // Check if user declined booking
    if (text.toLowerCase().includes('no, thanks') || text.toLowerCase().includes('no thanks') || 
        (text.toLowerCase().includes('no') && text.toLowerCase().includes('thank'))) {
      addMessage("No problem! Is there anything else I can help you with?", 'bot');
      return;
    }

    // Regular chat (includes intelligent booking handling)
    setIsTyping(true);
    try {
      const response = await axios.post(`${API_BASE}/v1/chat/`, {
        query: text,
        top_k: 5,
        min_score: 0.5,
        style: "standard"
      });

      // RAG response format
      const answer = response.data.answer;

      // Transform RAG sources to expected format
      const sources = response.data.sources?.map((source, idx) => ({
        title: `${source.document} (${source.category})`,
        url: `#source-${idx}`, // Placeholder since we don't have actual URLs
        document: source.document,
        score: source.score
      })) || [];

      addMessage(answer, 'bot', sources, null, null, null);

      // Start TTS immediately after response (non-blocking)
      // IMPORTANT: Use ref to check voice state immediately (not closure value)
      if (answer && isVoiceEnabledRef.current) {
        console.log('🎤 Voice enabled, starting TTS...', {
          isVoiceEnabled: isVoiceEnabledRef.current,
          responseLength: answer.length,
          hasResponse: !!answer
        });
        // Fire and forget - don't wait for TTS
        playTextToSpeech(answer).catch(err => {
          console.error('TTS error in handleSendMessage:', err);
        });
      } else if (answer) {
        console.log('🔇 Voice not enabled, skipping TTS:', {
          isVoiceEnabled: isVoiceEnabledRef.current,
          hasResponse: !!answer
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage("I'm sorry, I encountered an error. Please try again.", 'bot');
    } finally {
      setIsTyping(false);
    }
  };

  const handleBookingComplete = (reservation) => {
    // Don't close immediately - let the user see the completion screen
    // The booking flow will call onCancel when user clicks "Done"
    const reservationId = reservation?.reservationId || reservation?.id || 'Unknown';
    addMessage(
      `✅ Appointment confirmed! Reference Number: ${reservationId}. We'll send you a confirmation email shortly.`,
      'bot'
    );
  };

  const handleBookingCancel = () => {
    setBookingState(null);
    addMessage("No problem! Is there anything else I can help you with?", 'bot');
  };

  const handleParkingComplete = (reservation) => {
    setParkingState(null);
    addMessage(
      `✅ Parking reserved! Spot: ${reservation.spotIdentifier} (Zone: ${reservation.zone}). Reservation ID: ${reservation.reservationId}`,
      'bot'
    );
  };

  const handleParkingCancel = () => {
    setParkingState(null);
    addMessage("No problem! Is there anything else I can help you with?", 'bot');
  };

  const handleTranscriptComplete = (result) => {
    setShowTranscriptUpload(false);
    const summary = `📄 Transcript processed!\n\nSummary: ${result.summary}\n\nAttendees: ${result.attendees?.map(a => `${a.name} (${a.role})`).join(', ') || 'None'}\n\n${result.requiresReview ? '⚠️ This transcript requires clinician review.' : ''}`;
    addMessage(summary, 'bot');
  };

  return (
    <>
      {!isOpen && (
        <button className="chat-toggle" onClick={() => setIsOpen(true)}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {isOpen && (
        <div className="chat-widget">
          <div className="chat-header">
            <div className="chat-header-content">
              <h3>Functiomed Assistant</h3>
              <span className="status-indicator">● Online</span>
            </div>
            <div className="chat-header-actions">
              <button 
                className={`voice-toggle ${isVoiceEnabled ? 'active' : ''} ${hasPendingAudio ? 'has-pending' : ''} ${isSpeaking ? 'speaking' : ''}`}
                onClick={toggleVoice}
                title={hasPendingAudio ? 'Click to play pending audio' : isVoiceEnabled ? 'Disable AI Voice' : 'Enable AI Voice'}
              >
                {isVoiceEnabled ? (
                  <>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 5L6 9H2v6h4l5 4V5z" />
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                    </svg>
                    {isSpeaking && (
                      <div className="pitch-animation">
                        <span className="wave-bar"></span>
                        <span className="wave-bar"></span>
                        <span className="wave-bar"></span>
                        <span className="wave-bar"></span>
                      </div>
                    )}
                  </>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.6">
                    <path d="M11 5L6 9H2v6h4l5 4V5z" />
                    <line x1="23" y1="9" x2="17" y2="15" />
                    <line x1="17" y1="9" x2="23" y2="15" />
                  </svg>
                )}
                {hasPendingAudio && (
                  <span className="pending-indicator" title="Audio ready - click to play">
                    ●
                  </span>
                )}
              </button>
              <button className="chat-close" onClick={() => setIsOpen(false)}>
                ×
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            <button 
              className="quick-action-btn"
              onClick={() => {
                setBookingState({ step: 'init' });
                setParkingState(null);
                setShowTranscriptUpload(false);
              }}
            >
              📅 Book Appointment
            </button>
            <button 
              className="quick-action-btn"
              onClick={() => {
                setParkingState({ step: 'init' });
                setBookingState(null);
                setShowTranscriptUpload(false);
              }}
            >
              🚗 Reserve Parking
            </button>
          </div>

          <div className="chat-body" ref={scrollContainerRef}>
            {bookingState && (
              <BookingFlow
                sessionId={sessionId}
                onSessionIdUpdate={setSessionId}
                onComplete={handleBookingComplete}
                onCancel={handleBookingCancel}
              />
            )}

            {parkingState && (
              <ParkingFlow
                sessionId={sessionId}
                onComplete={handleParkingComplete}
                onCancel={handleParkingCancel}
              />
            )}

            {showTranscriptUpload && (
              <TranscriptUpload
                onComplete={handleTranscriptComplete}
                onCancel={() => setShowTranscriptUpload(false)}
              />
            )}

            {!bookingState && !parkingState && !showTranscriptUpload && (
              <>
                <MessageList
                  messages={messages}
                  isTyping={isTyping}
                  onQuickReply={handleSendMessage}
                  bookingStep={messages[messages.length - 1]?.bookingStep || null}
                  availableDates={messages[messages.length - 1]?.availableDates || null}
                />
                <div ref={messagesEndRef} />
                {/* Scroll to bottom button - appears when auto-scroll is disabled */}
                {!shouldAutoScroll && (
                  <button
                    className="scroll-to-bottom-btn"
                    onClick={() => {
                      setShouldAutoScroll(true);
                      scrollToBottom();
                    }}
                    title="Scroll to bottom"
                  >
                    ↓
                  </button>
                )}
              </>
            )}

            {!bookingState && !parkingState && !showTranscriptUpload && (
              <>
                <QuickReplies onSelect={handleSendMessage} />
                <MessageInput onSend={handleSendMessage} />
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default ChatWidget;

