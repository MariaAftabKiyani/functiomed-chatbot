/**
 * API Configuration for Functiomed Chatbot
 */

// Get API base URL from environment variable or use default
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // Chat endpoints
  CHAT: '/api/v1/chat/',
  CHAT_STREAM: '/api/v1/chat/stream',
  CHAT_QUICK: '/api/v1/chat/quick',
  CHAT_HEALTH: '/api/v1/chat/health',

  // FAQ endpoints
  FAQS: '/api/v1/faqs/',
  FAQ_BY_ID: (id) => `/api/v1/faqs/${id}`,
  FAQ_BY_CATEGORY: (category) => `/api/v1/faqs/category/${category}`,
  FAQ_RELOAD: '/api/v1/faqs/reload',
};

// Feature flags
export const FEATURES = {
  STREAMING: import.meta.env.VITE_ENABLE_STREAMING === 'true',
  TTS: import.meta.env.VITE_ENABLE_TTS === 'true',
};

// Request timeout (in milliseconds)
export const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10);

// Default language
export const DEFAULT_LANGUAGE = 'DE';

// Supported languages
export const SUPPORTED_LANGUAGES = ['DE', 'EN', 'FR'];
