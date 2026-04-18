<?php
/**
 * Plugin Name: TTAi Chat Interface
 * Description: AI Chat Interface for TTAi Super Model Hybrid
 * Version: 1.2.3
 * Author: Tuệ Tuệ
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class TTAi_Chat_Plugin {
    
    private $control_api_base;
    private $control_token;
    private $chat_api_url;
    
    public function __construct() {
        $this->control_api_base = getenv('TTAI_CONTROL_API') ?: 'http://localhost:8090';
        $this->control_token = getenv('TTAI_CONTROL_TOKEN') ?: 'ttai-control-token';
        
        $stored_chat_api = get_option('ttai_chat_api_endpoint');
        $this->chat_api_url = $stored_chat_api ?: (getenv('TTAI_CHAT_API') ?: 'http://host.docker.internal:8015/api/chat');
        $this->chat_api_url = untrailingslashit($this->chat_api_url);
        
        // Register shortcode
        add_shortcode('ttai_chat', array($this, 'render_chat_interface'));
        
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_assets'));
        
        // AJAX endpoint for chat
        add_action('wp_ajax_ttai_chat', array($this, 'handle_chat_request'));
        add_action('wp_ajax_nopriv_ttai_chat', array($this, 'handle_chat_request'));
        
        // AJAX for model management
        add_action('wp_ajax_ttai_get_models', array($this, 'handle_get_models'));
        add_action('wp_ajax_nopriv_ttai_get_models', array($this, 'handle_get_models'));
        add_action('wp_ajax_ttai_select_model', array($this, 'handle_select_model'));
        add_action('wp_ajax_nopriv_ttai_select_model', array($this, 'handle_select_model'));
    }
    
    public function enqueue_assets() {
        wp_enqueue_style(
            'ttai-chat-style',
            plugin_dir_url(__FILE__) . 'css/chat-style.css',
            array(),
            '1.2.3'
        );
        
        wp_enqueue_script(
            'ttai-chat-script',
            plugin_dir_url(__FILE__) . 'js/chat-script.js',
            array('jquery'),
            '1.2.3',
            true
        );
        
        // Localize script with AJAX URL
        wp_localize_script('ttai-chat-script', 'ttai_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('ttai_chat_nonce')
        ));
    }
    
    private function call_control_api($path, $method = 'GET', $body = null) {
        $url = trailingslashit($this->control_api_base) . ltrim($path, '/');
        $args = array(
            'method' => $method,
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-Control-Token' => $this->control_token
            ),
        );
        if (!empty($body)) {
            $args['body'] = wp_json_encode($body);
        }
        $response = wp_remote_request($url, $args);
        if (is_wp_error($response)) {
            throw new Exception($response->get_error_message());
        }
        $status = wp_remote_retrieve_response_code($response);
        if ($status < 200 || $status >= 300) {
            throw new Exception('API request failed with status ' . $status);
        }
        $data = json_decode(wp_remote_retrieve_body($response), true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON response');
        }
        return $data;
    }
    
    public function handle_get_models() {
        check_ajax_referer('ttai_chat_nonce', 'nonce');
        try {
            $data = $this->call_control_api('models');
            wp_send_json_success($data);
        } catch (Exception $e) {
            wp_send_json_error($e->getMessage(), 500);
        }
    }
    
    public function handle_select_model() {
        check_ajax_referer('ttai_chat_nonce', 'nonce');
        $host_id = sanitize_text_field($_POST['host_id'] ?? '');
        $model_id = sanitize_text_field($_POST['model_id'] ?? '');
        if (!$host_id || !$model_id) {
            wp_send_json_error('Thiếu tham số host/model', 400);
        }
        try {
            $payload = array(
                'host_id' => $host_id,
                'model_id' => $model_id
            );
            $data = $this->call_control_api('models/select', 'POST', $payload);
            wp_send_json_success($data);
        } catch (Exception $e) {
            wp_send_json_error($e->getMessage(), 500);
        }
    }
    
    public function render_chat_interface() {
        ob_start();
        ?>
        <section class="ttai-shell">
            <div class="ttai-stage">
                <div class="ttai-chat-card" data-theme="auto">
                    <header class="ttai-chat-header">
                        <div class="ttai-status ttai-status-only" aria-label="Tình trạng kết nối">
                            <span class="status-dot"></span>
                        </div>
                    </header>
                    <div class="ttai-chat-messages" id="ttai-messages">
                        <div class="message ai-message">
                            <div class="message-body">
                                <span class="message-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3l2.472 4.968L20 9.27l-4 3.858.944 5.5L12 16.9 7.056 18.628 8 12.87 4 9.27l5.528-1.302z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></span>
                                <div class="message-content">
                                    Xin chào! Tôi là TTAi Assistant, trợ lý AI của bạn. Tôi có thể giúp gì cho bạn hôm nay? 😊
                                </div>
                            </div>
                            <div class="message-meta">
                                <span class="message-actor">Tuệ Tuệ AI</span>
                                <span class="meta-dot">•</span>
                                <span class="message-time"><?php echo current_time('H:i'); ?></span>
                            </div>
                        </div>
                    </div>
                    <div class="ttai-chat-input">
                        <textarea 
                            id="ttai-user-input" 
                            placeholder="Nhập câu hỏi của bạn... (Enter để gửi, Shift+Enter để xuống dòng)"
                            rows="2"
                        ></textarea>
                        <button id="ttai-send-button" class="send-button" aria-label="Gửi tin nhắn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round"/>
                                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                    <footer class="ttai-chat-footer">
                        <p>💬 Miễn phí cho người dùng thử nghiệm · ⚡ Hybrid router tự chọn mô hình</p>
                    </footer>
                </div>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }
    
    public function handle_chat_request() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'ttai_chat_nonce')) {
            wp_die('Security check failed');
        }
        
        $user_message = sanitize_text_field($_POST['message']);
        $user_id = isset($_POST['user_id']) ? sanitize_text_field($_POST['user_id']) : 'free_user_' . uniqid();
        
        if (empty($user_message)) {
            wp_send_json_error('Message cannot be empty');
        }
        
        try {
            // Call TTAi FastAPI
            $api_response = $this->call_ttai_api($user_message, $user_id);
            
            // Log interaction for analytics
            $this->log_interaction($user_id, $user_message, $api_response);
            
            wp_send_json_success(array(
                'response' => $api_response['response'],
                'processing_time' => $api_response['processing_time'],
                'model_used' => $api_response['model_used'],
                'timestamp' => current_time('mysql')
            ));
            
        } catch (Exception $e) {
            wp_send_json_error('Error: ' . $e->getMessage());
        }
    }
    
    private function call_ttai_api($message, $user_id) {
        $api_url = $this->chat_api_url;
        
        $args = array(
            'timeout' => 60,
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'body' => json_encode(array(
                'message' => $message,
                'user_id' => $user_id,
                'use_memory' => false
            ))
        );
        
        $response = wp_remote_post($api_url, $args);
        
        if (is_wp_error($response)) {
            throw new Exception('API connection failed: ' . $response->get_error_message());
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (!$data || !isset($data['response'])) {
            throw new Exception('Invalid API response');
        }
        
        return $data;
    }
    
    private function log_interaction($user_id, $question, $response) {
        // Simple file logging - will be replaced with database
        $log_entry = sprintf(
            "[%s] User: %s | Q: %s | A: %s chars | Time: %.2fs | Model: %s\n",
            current_time('Y-m-d H:i:s'),
            $user_id,
            substr($question, 0, 100),
            strlen($response['response']),
            $response['processing_time'],
            $response['model_used']
        );
        
        $log_file = plugin_dir_path(__FILE__) . 'logs/interactions.log';
        file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
    }
}

// Initialize plugin
new TTAi_Chat_Plugin();
?>