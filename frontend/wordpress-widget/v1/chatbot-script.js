// Chat Widget State
let isOpen = false;
let conversationHistory = [];
let currentLanguage = 'EN'; // Default language
let faqCache = {}; // Cache for FAQ responses
let faqsHidden = false; // Track if FAQs are hidden
let currentAbortController = null; // For cancelling requests
let currentStreamingMessage = null; // Reference to the message being streamed
let isVoiceEnabled = false; // Voice toggle state
let recognition = null; // Speech recognition instance
let isListening = false; // Microphone listening state

// Configuration
const API_BASE_URL = 'http://localhost:8000';  // Change to your backend URL
const API_ENDPOINT = '/api/v1/chat/';
const STREAM_ENDPOINT = '/api/v1/chat/stream';
const FAQ_ENDPOINT = '/api/v1/faqs/';
const USE_STREAMING = true; // Toggle streaming vs regular

// Language-specific messages
const MESSAGES = {
    EN: {
        initialGreeting: "Hi there! 👋 I'm FIONA, your friendly assistant at Functiomed. I'm here to help you with anything you need - whether it's finding information about our services, doctors, or answering your questions. What can I help you with today?",
        placeholder: "Type your message or click mic to speak...",
        errorMessage: "Sorry, there was an error. Please try again.",
        typingIndicator: "Typing...",
        headerTitle: "FIONA",
        headerStatus: "● Online"
    },
    DE: {
        initialGreeting: "Hallo! 👋 Ich bin FIONA, Ihre freundliche Assistentin bei Functiomed. Ich bin hier, um Ihnen bei allem zu helfen, was Sie brauchen - ob es darum geht, Informationen über unsere Dienstleistungen, Ärzte zu finden oder Ihre Fragen zu beantworten. Womit kann ich Ihnen heute helfen?",
        placeholder: "Geben Sie Ihre Nachricht ein...",
        errorMessage: "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es erneut.",
        typingIndicator: "Tippt...",
        headerTitle: "FIONA",
        headerStatus: "● Online"
    },
    FR: {
        initialGreeting: "Bonjour ! 👋 Je suis FIONA, votre assistante amicale chez Functiomed. Je suis là pour vous aider avec tout ce dont vous avez besoin - que ce soit pour trouver des informations sur nos services, nos médecins ou répondre à vos questions. En quoi puis-je vous aider aujourd'hui ?",
        placeholder: "Tapez votre message...",
        errorMessage: "Désolé, une erreur s'est produite. Veuillez réessayer.",
        typingIndicator: "Écrit...",
        headerTitle: "FIONA",
        headerStatus: "● En ligne"
    }
};

// DOM Elements
const chatButton = document.getElementById('chatButton');
const chatWidget = document.getElementById('chatWidget');
const closeButton = document.getElementById('closeButton');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const stopButton = document.getElementById('stopButton');
const voiceToggle = document.getElementById('voiceToggle');
const micButton = document.getElementById('micButton');
const pitchAnimation = document.getElementById('pitchAnimation');

// Initialize
function init() {
    // Check if WordPress config exists, otherwise use defaults
    if (typeof chatbotConfig !== 'undefined') {
        currentLanguage = chatbotConfig.language || 'DE';
    }

    setInitialTime();
    updateLanguageUI();
    setupEventListeners();
    setupLanguageSelector();
    setupFAQButtons();
    loadFAQs(); // Pre-load FAQ data
}

// Setup language selector event listener
function setupLanguageSelector() {
    const languageSelect = document.getElementById('languageSelect');

    // Set initial value
    if (languageSelect) {
        languageSelect.value = currentLanguage;

        // Add event listener
        languageSelect.addEventListener('change', (e) => {
            currentLanguage = e.target.value;
            updateLanguageUI();
            loadFAQs(); // Reload FAQs in new language
        });
    }
}

// Update UI text based on selected language
function updateLanguageUI() {
    const messages = MESSAGES[currentLanguage];

    // Update placeholder
    chatInput.placeholder = messages.placeholder;

    // Update header
    const headerTitle = document.querySelector('.chat-header-content h3');
    const headerStatus = document.querySelector('.status-indicator');
    if (headerTitle) headerTitle.textContent = messages.headerTitle;
    if (headerStatus) headerStatus.textContent = messages.headerStatus;

    // Update initial message if it's the first message
    if (conversationHistory.length === 0) {
        const initialMessage = document.querySelector('.message.bot .message-content');
        if (initialMessage) {
            initialMessage.textContent = messages.initialGreeting;
        }
    }
}

// Set initial message time
function setInitialTime() {
    const timeElement = document.getElementById('initialTime');
    if (timeElement) {
        timeElement.textContent = getCurrentTime();
    }
}

// Get current time formatted
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

// Setup Event Listeners
function setupEventListeners() {
    chatButton.addEventListener('click', toggleChat);
    closeButton.addEventListener('click', toggleChat);
    sendButton.addEventListener('click', sendMessage);
    stopButton.addEventListener('click', stopGeneration);
    voiceToggle.addEventListener('click', toggleVoice);
    micButton.addEventListener('click', toggleMicrophone);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize input
    chatInput.addEventListener('input', () => {
        sendButton.disabled = chatInput.value.trim() === '';
    });

    // Initialize speech recognition
    initSpeechRecognition();
}

// Toggle chat widget
function toggleChat() {
    isOpen = !isOpen;
    chatWidget.classList.toggle('open');
    chatButton.classList.toggle('active');
    
    if (isOpen) {
        chatInput.focus();
        scrollToBottom();
    }
}

// Send message with API integration
async function sendMessage() {
    const message = chatInput.value.trim();

    if (message === '') return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    chatInput.value = '';
    sendButton.disabled = true;

    // Use streaming or regular API
    if (USE_STREAMING) {
        await sendMessageStreaming(message);
    } else {
        await sendMessageRegular(message);
    }
}

// Regular non-streaming message
async function sendMessageRegular(message) {
    showTypingIndicator();

    try {
        const response = await fetchBotResponse(message);

        hideTypingIndicator();
        addMessage(response.answer, 'bot');

    } catch (error) {
        console.error('Error fetching response:', error);
        hideTypingIndicator();

        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
    }
}

// Streaming message with stop capability
async function sendMessageStreaming(message) {
    // Create abort controller for this request
    currentAbortController = new AbortController();

    // Show stop button
    showStopButton();

    try {
        const response = await fetchBotResponseStreaming(message, currentAbortController.signal);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Request was cancelled by user');
        } else {
            console.error('Error fetching response:', error);
            const messages = MESSAGES[currentLanguage];
            addMessage(messages.errorMessage, 'bot');
        }
    } finally {
        hideStopButton();
        currentAbortController = null;
        currentStreamingMessage = null;
    }
}

// Fetch response from backend API (regular, non-streaming)
async function fetchBotResponse(query) {
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        const response = await fetch(`${apiUrl}${API_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                language: currentLanguage,
                top_k: 5,
                min_score: 0.3,
                style: 'standard'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Fetch streaming response from backend API
async function fetchBotResponseStreaming(query, signal) {
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        const response = await fetch(`${apiUrl}${STREAM_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                language: currentLanguage,
                top_k: 5,
                min_score: 0.3,
                style: 'standard'
            }),
            signal: signal  // Pass abort signal
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Create a streaming message container
        const messageDiv = createStreamingMessage();
        currentStreamingMessage = messageDiv;

        // Process the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                break;
            }

            // Decode the chunk
            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'metadata') {
                        // Store metadata (sources, confidence, etc.)
                        console.log('Metadata:', data);
                    } else if (data.type === 'chunk') {
                        // Append text chunk
                        fullText += data.text;
                        updateStreamingMessage(messageDiv, fullText);
                    } else if (data.type === 'done') {
                        // Stream complete
                        finalizeStreamingMessage(messageDiv, data.full_text);
                        console.log('Stream complete. Metrics:', data.metrics);
                    } else if (data.type === 'cancelled') {
                        // Stream was cancelled
                        finalizeStreamingMessage(messageDiv, data.partial_text || fullText, true);
                        console.log('Stream cancelled');
                    } else if (data.type === 'error') {
                        // Error occurred
                        throw new Error(data.error);
                    }
                }
            }
        }

    } catch (error) {
        if (currentStreamingMessage) {
            finalizeStreamingMessage(currentStreamingMessage, '', false, true);
        }
        throw error;
    }
}
// Comprehensive markdown to HTML converter
function markdownToHtml(text) {
    if (!text) return '';

    // First pass: Handle bold text **text**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Split into lines for processing
    const lines = text.split('\n');
    const output = [];
    let inList = false;
    let inParagraph = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        const nextLine = i < lines.length - 1 ? lines[i + 1] : '';
        const isBlank = line.trim() === '';

        // Handle bullet points (•, -, or *)
        const bulletMatch = line.match(/^[\s]*[•\-\*]\s+(.+)$/);

        if (bulletMatch) {
            // Start list if needed
            if (!inList) {
                if (inParagraph) {
                    output.push('</p>');
                    inParagraph = false;
                }
                output.push('<ul>');
                inList = true;
            }

            // Process bold within list item
            const content = bulletMatch[1];
            output.push(`<li>${content}</li>`);

        } else if (isBlank) {
            // Blank line - close any open tags
            if (inList) {
                output.push('</ul>');
                inList = false;
            }
            if (inParagraph) {
                output.push('</p>');
                inParagraph = false;
            }

        } else {
            // Regular text line
            if (inList) {
                output.push('</ul>');
                inList = false;
            }

            // Check if next line is blank or bullet (paragraph boundary)
            const nextIsBlank = nextLine.trim() === '';
            const nextIsBullet = nextLine.match(/^[\s]*[•\-\*]\s+/);

            if (!inParagraph) {
                output.push('<p>');
                inParagraph = true;
            }

            output.push(line);

            // Add line break if not end of paragraph
            if (!nextIsBlank && !nextIsBullet && i < lines.length - 1) {
                output.push('<br>');
            }

            // Close paragraph at boundary
            if (nextIsBlank || nextIsBullet || i === lines.length - 1) {
                output.push('</p>');
                inParagraph = false;
            }
        }
    }

    // Close any remaining open tags
    if (inList) output.push('</ul>');
    if (inParagraph) output.push('</p>');

    return output.join('');
}

// Add message to chat
function addMessage(text, sender, sources = null, confidence = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const time = getCurrentTime();

    // Convert markdown to HTML for bot messages
    const formattedText = sender === 'bot' ? markdownToHtml(text) : escapeHtml(text);

    messageDiv.innerHTML = `
        <div class="message-content">${formattedText}</div>
        <div class="message-time">${time}</div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    // Store in conversation history
    conversationHistory.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString()
    });
}

// Show typing indicator
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    sendButton.disabled = true;
    chatInput.disabled = true;
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
    sendButton.disabled = false;
    chatInput.disabled = false;
}

// Scroll to bottom of messages
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Streaming Message Functions
// ============================================================================

// Create a new streaming message container
function createStreamingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot streaming';

    const time = getCurrentTime();

    messageDiv.innerHTML = `
        <div class="message-content"></div>
        <div class="message-time">${time}</div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// Update streaming message with new text
function updateStreamingMessage(messageDiv, text) {
    const contentDiv = messageDiv.querySelector('.message-content');
    if (contentDiv) {
        const formattedText = markdownToHtml(text);
        contentDiv.innerHTML = formattedText;
        scrollToBottom();
    }
}

// Finalize streaming message (remove streaming class)
function finalizeStreamingMessage(messageDiv, text, wasCancelled = false, hasError = false) {
    messageDiv.classList.remove('streaming');

    const contentDiv = messageDiv.querySelector('.message-content');
    if (contentDiv) {
        if (hasError) {
            const messages = MESSAGES[currentLanguage];
            contentDiv.innerHTML = messages.errorMessage;
        } else if (text) {
            const formattedText = markdownToHtml(text);
            contentDiv.innerHTML = formattedText;

            // Add cancelled indicator if needed
            if (wasCancelled) {
                const cancelledNote = document.createElement('div');
                cancelledNote.style.cssText = 'font-size: 11px; color: #999; margin-top: 8px; font-style: italic;';
                cancelledNote.textContent = currentLanguage === 'DE' ? '(Abgebrochen)' :
                                           currentLanguage === 'FR' ? '(Annulé)' :
                                           '(Stopped)';
                contentDiv.appendChild(cancelledNote);
            }
        }
    }

    scrollToBottom();

    // Store in conversation history
    conversationHistory.push({
        text: text,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        wasCancelled: wasCancelled
    });
}

// ============================================================================
// Stop Button Functions
// ============================================================================

// Show stop button
function showStopButton() {
    if (stopButton) {
        console.log('Showing stop button');
        stopButton.classList.add('visible');
        sendButton.classList.add('hidden');
    } else {
        console.error('Stop button element not found!');
    }
}

// Hide stop button
function hideStopButton() {
    if (stopButton) {
        stopButton.classList.remove('visible');
        sendButton.classList.remove('hidden');
    }
}

// Stop the current generation
function stopGeneration() {
    if (currentAbortController) {
        console.log('Stopping generation...');
        currentAbortController.abort();
        hideStopButton();
    }
}

// ============================================================================
// FAQ Functions
// ============================================================================

// Load all FAQs and cache them
async function loadFAQs() {
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        const response = await fetch(`${apiUrl}${FAQ_ENDPOINT}?language=${currentLanguage}`);

        if (!response.ok) {
            console.error('Failed to load FAQs:', response.status);
            return;
        }

        const data = await response.json();

        // Cache all FAQs by ID
        data.faqs.forEach(faq => {
            faqCache[faq.id] = faq;
        });

        console.log(`Loaded ${data.total} FAQs into cache`);
        updateFAQButtonTexts();

    } catch (error) {
        console.error('Error loading FAQs:', error);
    }
}

// Update FAQ button texts based on current language
function updateFAQButtonTexts() {
    const faqButtons = document.querySelectorAll('.faq-button');

    faqButtons.forEach(button => {
        const faqId = button.getAttribute('data-faq-id');
        const faq = faqCache[faqId];

        if (faq && faq.question && faq.question[currentLanguage]) {
            button.textContent = faq.question[currentLanguage];
        }
    });

    // Update FAQ title based on language
    const faqTitle = document.querySelector('.faq-title');
    if (faqTitle) {
        const titles = {
            DE: 'Häufig gestellte Fragen:',
            EN: 'Frequently Asked Questions:',
            FR: 'Questions fréquemment posées:'
        };
        faqTitle.textContent = titles[currentLanguage] || titles.EN;
    }
}

// Setup FAQ button click handlers
function setupFAQButtons() {
    const faqButtons = document.querySelectorAll('.faq-button');

    faqButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const faqId = button.getAttribute('data-faq-id');
            await handleFAQClick(faqId);
        });
    });
}

// Handle FAQ button click - instant response from cache
async function handleFAQClick(faqId) {
    // Check cache first for instant response
    if (faqCache[faqId]) {
        const faq = faqCache[faqId];
        const question = faq.question[currentLanguage];
        const answer = faq.answer[currentLanguage];

        // Add user question
        addMessage(question, 'user');

        // Add instant cached answer (no API call needed!)
        setTimeout(() => {
            addMessage(answer, 'bot');
            // Don't hide FAQs - keep them visible like inspiration widget
        }, 100);

        return;
    }

    // Fallback: Fetch from API if not in cache
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        showTypingIndicator();

        const response = await fetch(`${apiUrl}${FAQ_ENDPOINT}${faqId}?language=${currentLanguage}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const faqData = await response.json();

        // Cache it
        faqCache[faqId] = {
            id: faqData.id,
            question: { [currentLanguage]: faqData.question },
            answer: { [currentLanguage]: faqData.answer },
            category: faqData.category
        };

        // Add question and answer
        addMessage(faqData.question, 'user');
        hideTypingIndicator();
        addMessage(faqData.answer, 'bot');

        // Don't hide FAQs - keep them visible like inspiration widget

    } catch (error) {
        console.error('Error fetching FAQ:', error);
        hideTypingIndicator();

        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
    }
}

// Hide FAQ buttons after first interaction
function hideFAQs() {
    if (!faqsHidden) {
        const faqSection = document.getElementById('faqSection');
        if (faqSection) {
            faqSection.classList.add('hidden');
            faqsHidden = true;
        }
    }
}

// Show FAQ buttons again (optional - for reset)
function showFAQs() {
    const faqSection = document.getElementById('faqSection');
    if (faqSection) {
        faqSection.classList.remove('hidden');
        faqsHidden = false;
    }
}

// ============================================================================
// Voice and Speech Recognition Functions
// ============================================================================

// Toggle voice output
function toggleVoice() {
    isVoiceEnabled = !isVoiceEnabled;

    if (isVoiceEnabled) {
        voiceToggle.classList.add('active');
    } else {
        voiceToggle.classList.remove('active');
        voiceToggle.classList.remove('speaking');
        voiceToggle.classList.add('muted');
        if (pitchAnimation) {
            pitchAnimation.style.display = 'none';
        }
        setTimeout(() => voiceToggle.classList.remove('muted'), 300);
    }

    console.log('Voice output:', isVoiceEnabled ? 'enabled' : 'disabled');
}

// Show speaking animation
function showSpeakingAnimation() {
    if (isVoiceEnabled && voiceToggle && pitchAnimation) {
        voiceToggle.classList.add('speaking');
        pitchAnimation.style.display = 'flex';
    }
}

// Hide speaking animation
function hideSpeakingAnimation() {
    if (voiceToggle && pitchAnimation) {
        voiceToggle.classList.remove('speaking');
        pitchAnimation.style.display = 'none';
    }
}

// Initialize speech recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.log('Speech recognition not supported');
        micButton.style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // Can be changed based on currentLanguage

    recognition.onstart = () => {
        isListening = true;
        micButton.classList.add('listening');
        console.log('Speech recognition started');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendButton.disabled = false;

        // Auto-send after a short delay
        setTimeout(() => {
            if (transcript.trim()) {
                sendMessage();
            }
        }, 500);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        micButton.classList.remove('listening');

        if (event.error === 'no-speech') {
            alert('No speech detected. Please try again.');
        } else if (event.error === 'not-allowed') {
            alert('Microphone permission denied. Please enable it in your browser settings.');
        }
    };

    recognition.onend = () => {
        isListening = false;
        micButton.classList.remove('listening');
        console.log('Speech recognition ended');
    };
}

// Toggle microphone for speech input
function toggleMicrophone() {
    if (!recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
        }
    }
}

// Initialize the chatbot
init();