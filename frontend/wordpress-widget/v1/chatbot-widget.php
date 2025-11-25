<?php
/**
 * Plugin Name: Chatbot Widget
 * Plugin URI: https://yourwebsite.com
 * Description: Adds a beautiful chatbot popup widget to your WordPress site
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://yourwebsite.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Enqueue chatbot styles and scripts
function chatbot_widget_enqueue_assets() {
    // Enqueue CSS
    wp_enqueue_style(
        'chatbot-widget-style',
        plugins_url('chatbot-style.css', __FILE__),
        array(),
        '1.0.0',
        'all'
    );
    
    // Enqueue JavaScript
    wp_enqueue_script(
        'chatbot-widget-script',
        plugins_url('chatbot-script.js', __FILE__),
        array(),
        '1.0.0',
        true // Load in footer
    );
}
add_action('wp_enqueue_scripts', 'chatbot_widget_enqueue_assets');

// Add chatbot HTML structure to footer
function chatbot_widget_add_html() {
    ?>
    <!-- Chat Button -->
    <div class="chat-button" id="chatButton">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
    </div>

    <!-- Chat Widget -->
    <div class="chat-widget" id="chatWidget">
        <!-- Chat Header -->
        <div class="chat-header">
            <div class="chat-header-content">
                <div class="chat-avatar">🤖</div>
                <div class="chat-header-text">
                    <h3>Support Assistant</h3>
                    <p>Online • We typically reply instantly</p>
                </div>
            </div>
            <button class="close-button" id="closeButton">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>

        <!-- Chat Messages -->
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div>
                    <div class="message-content">
                        Hello! 👋 Welcome to our website. How can I help you today?
                    </div>
                    <div class="message-time" id="initialTime"></div>
                </div>
            </div>
        </div>

        <!-- Typing Indicator -->
        <div class="typing-indicator" id="typingIndicator">
            <span></span>
            <span></span>
            <span></span>
        </div>

        <!-- Chat Input -->
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="chatInput" 
                    placeholder="Type your message..."
                    autocomplete="off"
                >
                <button class="send-button" id="sendButton">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    <?php
}
add_action('wp_footer', 'chatbot_widget_add_html');