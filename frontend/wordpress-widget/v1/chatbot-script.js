// Chat Widget State
let isOpen = false;
let conversationHistory = [];
let currentLanguage = 'DE'; // Default language
let faqCache = {}; // Cache for FAQ responses
let faqsHidden = false; // Track if FAQs are hidden

// Configuration
const API_BASE_URL = 'http://localhost:8000';  // Change to your backend URL
const API_ENDPOINT = '/api/v1/chat/';
const FAQ_ENDPOINT = '/api/v1/faqs/';

// Language-specific messages
const MESSAGES = {
    EN: {
        initialGreeting: "Hello! 👋 Welcome to functiomed. How can I help you today?",
        placeholder: "Type your message...",
        errorMessage: "Sorry, there was an error. Please try again.",
        typingIndicator: "Typing...",
        headerTitle: "Support Assistant",
        headerStatus: "Online • We typically reply instantly"
    },
    DE: {
        initialGreeting: "Hallo! 👋 Willkommen bei functiomed. Wie kann ich Ihnen heute helfen?",
        placeholder: "Geben Sie Ihre Nachricht ein...",
        errorMessage: "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es erneut.",
        typingIndicator: "Tippt...",
        headerTitle: "Support-Assistent",
        headerStatus: "Online • Wir antworten normalerweise sofort"
    },
    FR: {
        initialGreeting: "Bonjour! 👋 Bienvenue chez functiomed. Comment puis-je vous aider aujourd'hui?",
        placeholder: "Tapez votre message...",
        errorMessage: "Désolé, une erreur s'est produite. Veuillez réessayer.",
        typingIndicator: "Écrit...",
        headerTitle: "Assistant Support",
        headerStatus: "En ligne • Nous répondons généralement instantanément"
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

// Initialize
function init() {
    // Check if WordPress config exists, otherwise use defaults
    if (typeof chatbotConfig !== 'undefined') {
        currentLanguage = chatbotConfig.language || 'DE';
    }

    setInitialTime();
    updateLanguageUI();
    setupEventListeners();
    addLanguageSelector();
    setupFAQButtons();
    loadFAQs(); // Pre-load FAQ data
}

// Add language selector to chat header
function addLanguageSelector() {
    const headerContent = document.querySelector('.chat-header-content');
    
    const languageSelector = document.createElement('div');
    languageSelector.className = 'language-selector';
    languageSelector.innerHTML = `
        <select id="languageSelect" class="language-select">
            <option value="DE" ${currentLanguage === 'DE' ? 'selected' : ''}>German</option>
            <option value="EN" ${currentLanguage === 'EN' ? 'selected' : ''}>English</option>
            <option value="FR" ${currentLanguage === 'FR' ? 'selected' : ''}>French</option>
        </select>
    `;
    
    // Insert before close button
    const chatHeader = document.querySelector('.chat-header');
    chatHeader.insertBefore(languageSelector, closeButton);
    
    // Add event listener
    document.getElementById('languageSelect').addEventListener('change', (e) => {
        currentLanguage = e.target.value;
        updateLanguageUI();
        loadFAQs(); // Reload FAQs in new language
    });
}

// Update UI text based on selected language
function updateLanguageUI() {
    const messages = MESSAGES[currentLanguage];
    
    // Update placeholder
    chatInput.placeholder = messages.placeholder;
    
    // Update header
    const headerTitle = document.querySelector('.chat-header-text h3');
    const headerStatus = document.querySelector('.chat-header-text p');
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

    // Show typing indicator
    showTypingIndicator();

    try {
        // Call backend API
        const response = await fetchBotResponse(message);
        
        hideTypingIndicator();
        addMessage(response.answer, 'bot', response.sources, response.confidence_score);
        
    } catch (error) {
        console.error('Error fetching response:', error);
        hideTypingIndicator();
        
        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
    }
}

// Fetch response from backend API
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
        <div>
            <div class="message-content">${formattedText}</div>
            <div class="message-time">${time}</div>
        </div>
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
            const textSpan = button.querySelector('.faq-text');
            if (textSpan) {
                textSpan.textContent = faq.question[currentLanguage];
            }
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
        faqTitle.textContent = titles[currentLanguage] || titles.DE;
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
            hideFAQs(); // Hide FAQs after first interaction
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

        hideFAQs();

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
        const faqContainer = document.getElementById('faqContainer');
        if (faqContainer) {
            faqContainer.classList.add('hidden');
            faqsHidden = true;
        }
    }
}

// Show FAQ buttons again (optional - for reset)
function showFAQs() {
    const faqContainer = document.getElementById('faqContainer');
    if (faqContainer) {
        faqContainer.classList.remove('hidden');
        faqsHidden = false;
    }
}

// Initialize the chatbot
init();