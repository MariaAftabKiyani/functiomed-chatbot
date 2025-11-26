/**
 * useChat Hook - Manages chat state and streaming responses
 */
import { useState, useRef, useCallback } from 'react';
import { sendChatMessage, sendStreamingChatMessage } from '../services/chatService';
import { FEATURES, DEFAULT_LANGUAGE } from '../config/api';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);

  const abortControllerRef = useRef(null);
  const currentMessageIdRef = useRef(null);

  /**
   * Add a message to the chat
   */
  const addMessage = useCallback((text, type = 'user', metadata = {}) => {
    const newMessage = {
      id: Date.now().toString() + Math.random(),
      type,
      text,
      timestamp: new Date(),
      ...metadata,
    };

    setMessages((prev) => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  /**
   * Update a streaming message
   */
  const updateStreamingMessage = useCallback((text) => {
    setCurrentStreamingMessage(text);
  }, []);

  /**
   * Finalize a streaming message
   */
  const finalizeStreamingMessage = useCallback((fullText, metadata = {}) => {
    const messageId = currentMessageIdRef.current;

    if (messageId) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, text: fullText, isStreaming: false, ...metadata }
            : msg
        )
      );
    }

    setCurrentStreamingMessage('');
    currentMessageIdRef.current = null;
    setIsStreaming(false);
  }, []);

  /**
   * Process streaming response from backend
   */
  const processStreamingResponse = useCallback(
    async (response) => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullText = '';
      let metadata = {};

      // Create placeholder message for streaming
      const messageId = Date.now().toString() + Math.random();
      currentMessageIdRef.current = messageId;

      setMessages((prev) => [
        ...prev,
        {
          id: messageId,
          type: 'bot',
          text: '',
          timestamp: new Date(),
          isStreaming: true,
        },
      ]);

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode chunk
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'metadata') {
                // Store metadata (sources, confidence, etc.)
                metadata = {
                  sources: data.sources,
                  confidence_score: data.confidence_score,
                  detected_language: data.detected_language,
                };
              } else if (data.type === 'chunk') {
                // Append text chunk
                fullText += data.text;

                // Update the message in real-time
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, text: fullText }
                      : msg
                  )
                );
              } else if (data.type === 'done') {
                // Stream complete
                finalizeStreamingMessage(data.full_text || fullText, {
                  ...metadata,
                  metrics: data.metrics,
                });
              } else if (data.type === 'cancelled') {
                // Stream was cancelled
                finalizeStreamingMessage(data.partial_text || fullText, {
                  ...metadata,
                  wasCancelled: true,
                });
              } else if (data.type === 'error') {
                // Error occurred
                throw new Error(data.error);
              }
            }
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted by user');
          finalizeStreamingMessage(fullText, {
            ...metadata,
            wasCancelled: true,
          });
        } else {
          throw error;
        }
      }
    },
    [finalizeStreamingMessage]
  );

  /**
   * Send a message (with or without streaming)
   */
  const sendMessage = useCallback(
    async (text, options = {}) => {
      if (!text.trim()) return;

      // Add user message
      addMessage(text, 'user');

      try {
        if (FEATURES.STREAMING) {
          // Use streaming API
          setIsStreaming(true);
          abortControllerRef.current = new AbortController();

          const response = await sendStreamingChatMessage(
            text,
            language,
            options,
            abortControllerRef.current.signal
          );

          await processStreamingResponse(response);
        } else {
          // Use regular API
          const response = await sendChatMessage(text, language, options);

          addMessage(response.answer, 'bot', {
            sources: response.sources,
            confidence_score: response.confidence_score,
            detected_language: response.detected_language,
            metrics: response.metrics,
          });
        }
      } catch (error) {
        console.error('Send message error:', error);

        if (error.name !== 'AbortError') {
          addMessage(
            'Sorry, I encountered an error. Please try again.',
            'bot',
            { isError: true }
          );
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [language, addMessage, processStreamingResponse]
  );

  /**
   * Stop current streaming generation
   */
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      console.log('Stopping generation...');
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentStreamingMessage('');
    currentMessageIdRef.current = null;
  }, []);

  return {
    messages,
    isStreaming,
    currentStreamingMessage,
    language,
    setLanguage,
    sendMessage,
    stopGeneration,
    addMessage,
    clearMessages,
  };
};

export default useChat;
