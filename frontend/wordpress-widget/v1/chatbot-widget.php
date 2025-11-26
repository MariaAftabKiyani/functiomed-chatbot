<?php
/**
 * Plugin Name: Functiomed Chatbot Widget
 * Description: Multi-language RAG-powered medical chatbot (EN, DE, FR)
 * Version: 1.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

// Plugin settings with multi-language support
function chatbot_widget_settings() {
    add_option('chatbot_api_url', 'http://localhost:8000');
    add_option('chatbot_language', 'DE');
}
register_activation_hook(__FILE__, 'chatbot_widget_settings');

// Register settings
function chatbot_widget_register_settings() {
    register_setting('chatbot_settings', 'chatbot_api_url');
    register_setting('chatbot_settings', 'chatbot_language');
}
add_action('admin_init', 'chatbot_widget_register_settings');

// Enqueue assets with configuration
function chatbot_widget_enqueue_assets() {
    wp_enqueue_style(
        'chatbot-widget-style',
        plugins_url('chatbot-style.css', __FILE__),
        array(),
        '1.0.0',
        'all'
    );
    
    wp_enqueue_script(
        'chatbot-widget-script',
        plugins_url('chatbot-script.js', __FILE__),
        array(),
        '1.0.0',
        true
    );
    
    // Pass configuration to JavaScript
    wp_localize_script('chatbot-widget-script', 'chatbotConfig', array(
        'apiUrl' => get_option('chatbot_api_url', 'http://localhost:8000'),
        'language' => get_option('chatbot_language', 'DE'),
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('chatbot_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'chatbot_widget_enqueue_assets');

// Add chatbot HTML structure to footer
function chatbot_widget_add_html() {
    $language = get_option('chatbot_language', 'DE');
    
    $greetings = array(
        'EN' => 'Hello! 👋 Welcome to functiomed. How can I help you today?',
        'DE' => 'Hallo! 👋 Willkommen bei functiomed. Wie kann ich Ihnen heute helfen?',
        'FR' => 'Bonjour! 👋 Bienvenue chez functiomed. Comment puis-je vous aider aujourd\'hui?'
    );
    
    $placeholders = array(
        'EN' => 'Type your message...',
        'DE' => 'Geben Sie Ihre Nachricht ein...',
        'FR' => 'Tapez votre message...'
    );
    
    $greeting = isset($greetings[$language]) ? $greetings[$language] : $greetings['DE'];
    $placeholder = isset($placeholders[$language]) ? $placeholders[$language] : $placeholders['DE'];
    ?>
    <!-- Chat Button -->
    <div class="chat-button" id="chatButton">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
    </div>

    <!-- Chat Widget -->
    <div class="chat-widget" id="chatWidget">
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

        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div>
                    <div class="message-content"><?php echo esc_html($greeting); ?></div>
                    <div class="message-time" id="initialTime"></div>
                </div>
            </div>
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <span></span>
            <span></span>
            <span></span>
        </div>

        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="chatInput" 
                    placeholder="<?php echo esc_attr($placeholder); ?>"
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

// Admin settings page
function chatbot_widget_admin_menu() {
    add_options_page(
        'Chatbot Settings',
        'Chatbot',
        'manage_options',
        'chatbot-settings',
        'chatbot_widget_settings_page'
    );
}
add_action('admin_menu', 'chatbot_widget_admin_menu');

function chatbot_widget_settings_page() {
    ?>
    <div class="wrap">
        <h1>Functiomed Chatbot Settings</h1>
        <form method="post" action="options.php">
            <?php settings_fields('chatbot_settings'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row">API URL</th>
                    <td>
                        <input type="text" name="chatbot_api_url" 
                               value="<?php echo esc_attr(get_option('chatbot_api_url')); ?>" 
                               class="regular-text"
                               placeholder="http://localhost:8000">
                        <p class="description">Backend API URL (e.g., https://your-api.onrender.com)</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Default Language</th>
                    <td>
                        <select name="chatbot_language">
                            <option value="DE" <?php selected(get_option('chatbot_language'), 'DE'); ?>>🇩🇪 German (Deutsch)</option>
                            <option value="EN" <?php selected(get_option('chatbot_language'), 'EN'); ?>>🇬🇧 English</option>
                            <option value="FR" <?php selected(get_option('chatbot_language'), 'FR'); ?>>🇫🇷 French (Français)</option>
                        </select>
                        <p class="description">Users can still change language in the chat widget</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}
?>