/**
 * ChatWidgetIntegrated - Example of ChatWidget using the new API service
 *
 * This is an example showing how to integrate the new chat service
 * with streaming support and stop generation functionality.
 *
 * You can use this as a reference to update your existing ChatWidget.jsx
 */
import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { getAllFAQs } from '../services/chatService';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatWidget.css';

function ChatWidgetIntegrated() {
  const {
    messages,
    isStreaming,
    language,
    setLanguage,
    sendMessage,
    stopGeneration,
    addMessage,
  } = useChat();

  const [isOpen, setIsOpen] = useState(false);
  const [faqs, setFaqs] = useState([]);
  const [showFAQs, setShowFAQs] = useState(true);
  const messagesEndRef = useRef(null);

  // Load FAQs when component mounts
  useEffect(() => {
    loadFAQs();
  }, [language]);

  // Add welcome message on mount
  useEffect(() => {
    if (messages.length === 0) {
      addMessage(
        "Hallo! 👋 Willkommen bei functiomed. Wie kann ich Ihnen heute helfen?",
        'bot',
        { id: 'welcome' }
      );
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const loadFAQs = async () => {
    try {
      const data = await getAllFAQs(language);
      setFaqs(data.faqs || []);
    } catch (error) {
      console.error('Failed to load FAQs:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    // Hide FAQs after first message
    if (showFAQs) {
      setShowFAQs(false);
    }

    // Send message (handles streaming automatically)
    await sendMessage(text);
  };

  const handleFAQClick = (faq) => {
    // Add FAQ question as user message
    addMessage(faq.question[language], 'user');

    // Add FAQ answer as bot message (instant - no API call needed)
    addMessage(faq.answer[language], 'bot', {
      isFAQ: true,
      category: faq.category,
      confidence_score: 1.0,
    });

    // Hide FAQs
    setShowFAQs(false);
  };

  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
  };

  return (
    <>
      {/* Chat Toggle Button */}
      {!isOpen && (
        <button className="chat-toggle" onClick={() => setIsOpen(true)}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {/* Chat Widget */}
      {isOpen && (
        <div className="chat-widget">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-content">
              <h3>Support-Assistent</h3>
              <span className="status-indicator">● Online</span>
            </div>

            <div className="chat-header-actions">
              {/* Language Selector */}
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="language-select"
              >
                <option value="DE">German</option>
                <option value="EN">English</option>
                <option value="FR">French</option>
              </select>

              {/* Close Button */}
              <button className="chat-close" onClick={() => setIsOpen(false)}>
                ×
              </button>
            </div>
          </div>

          {/* Chat Body */}
          <div className="chat-body">
            {/* Messages */}
            <MessageList messages={messages} />

            {/* FAQ Quick Buttons - shown initially */}
            {showFAQs && faqs.length > 0 && (
              <div className="faq-container">
                <div className="faq-title">
                  {language === 'DE' && 'Häufig gestellte Fragen:'}
                  {language === 'EN' && 'Frequently Asked Questions:'}
                  {language === 'FR' && 'Questions fréquemment posées:'}
                </div>
                {faqs.slice(0, 4).map((faq) => (
                  <button
                    key={faq.id}
                    className="faq-button"
                    onClick={() => handleFAQClick(faq)}
                  >
                    <span className="faq-icon">
                      {faq.id === 'services' && '💼'}
                      {faq.id === 'pricing' && '💰'}
                      {faq.id === 'appointment' && '📅'}
                      {faq.id === 'location' && '📍'}
                    </span>
                    <span className="faq-text">{faq.question[language]}</span>
                  </button>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="chat-input-container">
            {/* Stop Button - shown during streaming */}
            {isStreaming && (
              <button
                className="stop-button visible"
                onClick={stopGeneration}
                title="Stop generating"
              >
                <svg viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1"/>
                </svg>
              </button>
            )}

            <MessageInput
              onSend={handleSendMessage}
              disabled={isStreaming}
            />
          </div>
        </div>
      )}
    </>
  );
}

export default ChatWidgetIntegrated;
