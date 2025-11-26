/**
 * Chat Service - Handles all chat-related API calls
 */
import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS, API_TIMEOUT, DEFAULT_LANGUAGE } from '../config/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat message to the backend
 * @param {string} query - User's message
 * @param {string} language - Language code (DE, EN, FR)
 * @param {object} options - Additional options
 * @returns {Promise<object>} - Chat response
 */
export const sendChatMessage = async (query, language = DEFAULT_LANGUAGE, options = {}) => {
  try {
    const response = await api.post(API_ENDPOINTS.CHAT, {
      query,
      language,
      top_k: options.top_k || 5,
      min_score: options.min_score || 0.3,
      style: options.style || 'standard',
      category: options.category || null,
      source_type: options.source_type || null,
    });

    return response.data;
  } catch (error) {
    console.error('Chat API error:', error);
    throw handleApiError(error);
  }
};

/**
 * Send a streaming chat message
 * @param {string} query - User's message
 * @param {string} language - Language code
 * @param {object} options - Additional options
 * @param {AbortSignal} signal - Abort signal for cancellation
 * @returns {Promise<ReadableStream>} - Streaming response
 */
export const sendStreamingChatMessage = async (query, language = DEFAULT_LANGUAGE, options = {}, signal = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT_STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        language,
        top_k: options.top_k || 5,
        min_score: options.min_score || 0.3,
        style: options.style || 'standard',
        category: options.category || null,
        source_type: options.source_type || null,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error('Streaming chat error:', error);
    throw error;
  }
};

/**
 * Check chat service health
 * @returns {Promise<object>} - Health status
 */
export const checkChatHealth = async () => {
  try {
    const response = await api.get(API_ENDPOINTS.CHAT_HEALTH);
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw handleApiError(error);
  }
};

/**
 * Get all FAQs
 * @param {string} language - Language code
 * @returns {Promise<object>} - FAQ list
 */
export const getAllFAQs = async (language = DEFAULT_LANGUAGE) => {
  try {
    const response = await api.get(`${API_ENDPOINTS.FAQS}?language=${language}`);
    return response.data;
  } catch (error) {
    console.error('Get FAQs error:', error);
    throw handleApiError(error);
  }
};

/**
 * Get a specific FAQ by ID
 * @param {string} faqId - FAQ identifier
 * @param {string} language - Language code
 * @returns {Promise<object>} - FAQ data
 */
export const getFAQById = async (faqId, language = DEFAULT_LANGUAGE) => {
  try {
    const response = await api.get(`${API_ENDPOINTS.FAQ_BY_ID(faqId)}?language=${language}`);
    return response.data;
  } catch (error) {
    console.error('Get FAQ error:', error);
    throw handleApiError(error);
  }
};

/**
 * Handle API errors and return user-friendly messages
 * @param {Error} error - Axios error object
 * @returns {Error} - Formatted error
 */
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.detail || error.response.data?.message || 'Server error';

    switch (status) {
      case 400:
        return new Error(`Invalid request: ${message}`);
      case 404:
        return new Error(`Not found: ${message}`);
      case 500:
        return new Error(`Server error: ${message}`);
      case 503:
        return new Error('Service unavailable. Please try again later.');
      default:
        return new Error(`Error: ${message}`);
    }
  } else if (error.request) {
    // Request made but no response
    return new Error('No response from server. Please check your connection.');
  } else {
    // Error in request setup
    return new Error(error.message || 'An unexpected error occurred');
  }
};

export default {
  sendChatMessage,
  sendStreamingChatMessage,
  checkChatHealth,
  getAllFAQs,
  getFAQById,
};
