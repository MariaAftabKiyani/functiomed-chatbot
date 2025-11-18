// Chat Widget State
let isOpen = false;
let conversationHistory = [];

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
    setInitialTime();
    setupEventListeners();
}

// Set initial message time
function setInitialTime() {
    const timeElement = document.getElementById('initialTime');
    timeElement.textContent = getCurrentTime();
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
        if (e.key === 'Enter') {
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

// Send message
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

    // Simulate bot response (replace with actual API call)
    setTimeout(() => {
        hideTypingIndicator();
        const response = generateBotResponse(message);
        addMessage(response, 'bot');
    }, 1000 + Math.random() * 1000);
}

// Add message to chat
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = getCurrentTime();
    
    messageDiv.innerHTML = `
        <div>
            <div class="message-content">${escapeHtml(text)}</div>
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
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
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

// Generate bot response (replace with actual API call)
function generateBotResponse(userMessage) {
    const message = userMessage.toLowerCase();

    // Simple response logic
    if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
        return "Hello! How can I assist you today? 😊";
    } else if (message.includes('help') || message.includes('support')) {
        return "I'm here to help! What do you need assistance with?";
    } else if (message.includes('price') || message.includes('cost')) {
        return "For pricing information, please visit our pricing page or contact our sales team.";
    } else if (message.includes('contact') || message.includes('email')) {
        return "You can reach us at contact@example.com or call +1-234-567-8900";
    } else if (message.includes('hours') || message.includes('open')) {
        return "We're available Monday-Friday, 9 AM - 5 PM EST. How can I help you?";
    } else if (message.includes('thank') || message.includes('thanks')) {
        return "You're welcome! Is there anything else I can help you with?";
    } else if (message.includes('bye') || message.includes('goodbye')) {
        return "Goodbye! Feel free to reach out anytime. Have a great day! 👋";
    } else {
        return `I understand you're asking about "${userMessage}". While I'm a demo bot, I'd be happy to help! What specific information do you need?`;
    }
}

// Initialize the chatbot
init();