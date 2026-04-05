<?php
/**
 * Plugin Name: TTAi Dashboard Control
 * Description: Hiển thị trạng thái collector / load balancer trực tiếp trong WordPress Admin.
 * Version: 0.1.0
 * Author: Tuệ Tuệ
 */

if (!defined('ABSPATH')) {
    exit;
}

class TTAI_Dashboard_Control {
    const OPTION_KEY = 'ttai_dashboard_control_settings';

    public function __construct() {
        add_action('admin_menu', array($this, 'register_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    public function register_menu() {
        add_menu_page(
            __('TTAi Dashboard', 'ttai-dashboard'),
            __('TTAi Dashboard', 'ttai-dashboard'),
            'manage_options',
            'ttai-dashboard-control',
            array($this, 'render_page'),
            'dashicons-chart-line',
            60
        );
    }

    public function register_settings() {
        register_setting(self::OPTION_KEY, self::OPTION_KEY, array($this, 'sanitize_settings'));
    }

    public function sanitize_settings($input) {
        return array(
            'collector_url'   => isset($input['collector_url']) ? esc_url_raw($input['collector_url']) : 'http://localhost:8090',
            'collector_token' => isset($input['collector_token']) ? sanitize_text_field($input['collector_token']) : '',
            'api_base_url'    => isset($input['api_base_url']) ? esc_url_raw($input['api_base_url']) : 'http://127.0.0.1:8000',
            'admin_token'     => isset($input['admin_token']) ? sanitize_text_field($input['admin_token']) : '',
        );
    }

    private function get_settings() {
        $defaults = array(
            'collector_url'   => 'http://localhost:8090',
            'collector_token' => '',
            'api_base_url'    => 'http://127.0.0.1:8000',
            'admin_token'     => '',
        );
        return wp_parse_args(get_option(self::OPTION_KEY, array()), $defaults);
    }

    private function decode_json_response($response, $error_code_prefix) {
        if (is_wp_error($response)) {
            return new WP_Error($error_code_prefix . '_error', $response->get_error_message());
        }
        $code = wp_remote_retrieve_response_code($response);
        if ($code !== 200) {
            return new WP_Error($error_code_prefix . '_error', sprintf('Endpoint trả về HTTP %d', $code));
        }
        $json = json_decode(wp_remote_retrieve_body($response), true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return new WP_Error($error_code_prefix . '_error', 'Endpoint trả về dữ liệu không hợp lệ');
        }
        return $json;
    }

    private function fetch_collector($path, $settings) {
        $url = trailingslashit($settings['collector_url']) . ltrim($path, '/');
        $args = array('timeout' => 5);
        if (!empty($settings['collector_token'])) {
            $args['headers'] = array('X-Control-Token' => $settings['collector_token']);
        }
        $response = wp_remote_get($url, $args);
        return $this->decode_json_response($response, 'collector');
    }

    private function fetch_api($path, $settings) {
        $url = trailingslashit($settings['api_base_url']) . ltrim($path, '/');
        $args = array('timeout' => 8);
        if (!empty($settings['admin_token'])) {
            $args['headers'] = array('Authorization' => 'Bearer ' . $settings['admin_token']);
        }
        $response = wp_remote_get($url, $args);
        return $this->decode_json_response($response, 'api');
    }

    public function render_page() {
        if (!current_user_can('manage_options')) {
            wp_die(__('Bạn không có quyền xem trang này.', 'ttai-dashboard'));
        }

        $settings = $this->get_settings();
        if (isset($_POST[self::OPTION_KEY])) {
            check_admin_referer('ttai_dashboard_control_save');
            $settings = $this->sanitize_settings($_POST[self::OPTION_KEY]);
            update_option(self::OPTION_KEY, $settings);
            echo '<div class="notice notice-success"><p>' . esc_html__('Đã lưu cấu hình.', 'ttai-dashboard') . '</p></div>';
        }

        $health    = $this->fetch_collector('/health-summary', $settings);
        $workload  = $this->fetch_collector('/workloads', $settings);
        $alerts    = $this->fetch_collector('/alerts', $settings);
        $overview  = $this->fetch_api('/api/v1/admin/overview?usage_limit=50&recent_events_limit=5', $settings);
        $errors    = $this->fetch_api('/api/v1/admin/errors/summary?limit=50&top_n=5', $settings);
        $quota     = $this->fetch_api('/api/v1/admin/quota/blocked?limit=50&recent_limit=5', $settings);
        ?>
        <div class="wrap">
            <h1><?php esc_html_e('TTAi Control Dashboard', 'ttai-dashboard'); ?></h1>

            <?php $collector_error = is_wp_error($health) || is_wp_error($workload) || is_wp_error($alerts); ?>
            <?php $api_error = is_wp_error($overview) || is_wp_error($errors) || is_wp_error($quota); ?>
            <?php if ($collector_error) : ?>
                <div class="notice notice-error">
                    <p><?php esc_html_e('Không thể kết nối collector. Kiểm tra URL/token và thử lại.', 'ttai-dashboard'); ?></p>
                </div>
            <?php endif; ?>
            <?php if ($api_error) : ?>
                <div class="notice notice-warning">
                    <p><?php esc_html_e('Không thể kết nối FastAPI admin endpoints. Kiểm tra API Base URL/admin token và thử lại.', 'ttai-dashboard'); ?></p>
                </div>
            <?php endif; ?>

            <?php if (!$api_error) : ?>
            <div style="margin:16px 0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;">
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <p style="margin:0;color:#64748b;font-size:12px;text-transform:uppercase;">Overview</p>
                    <h3 style="margin:8px 0 4px;">Health</h3>
                    <p style="font-size:28px;font-weight:700;margin:0;"><?php echo esc_html($overview['health']['summary']['status'] ?? '--'); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <p style="margin:0;color:#64748b;font-size:12px;text-transform:uppercase;">Usage</p>
                    <h3 style="margin:8px 0 4px;">Window Events</h3>
                    <p style="font-size:28px;font-weight:700;margin:0;"><?php echo intval($overview['usage']['window_event_count'] ?? 0); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <p style="margin:0;color:#64748b;font-size:12px;text-transform:uppercase;">Billing</p>
                    <h3 style="margin:8px 0 4px;">Billable Cost</h3>
                    <p style="font-size:28px;font-weight:700;margin:0;"><?php echo esc_html($overview['billing']['summary']['billable_estimated_cost'] ?? '--'); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <p style="margin:0;color:#64748b;font-size:12px;text-transform:uppercase;">Quota</p>
                    <h3 style="margin:8px 0 4px;">Blocked Events</h3>
                    <p style="font-size:28px;font-weight:700;margin:0;"><?php echo intval($quota['blocked_event_count'] ?? 0); ?></p>
                </div>
            </div>

            <div style="margin-top:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;">
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Billing Summary</h3>
                    <p><strong>Total Estimated Cost:</strong> <?php echo esc_html($overview['billing']['summary']['total_estimated_cost'] ?? '--'); ?></p>
                    <p><strong>Billable Events:</strong> <?php echo intval($overview['billing']['summary']['billable_events'] ?? 0); ?></p>
                    <p><strong>Top Provider:</strong> <?php echo esc_html(array_key_first($overview['billing']['summary']['provider_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Quota Watch</h3>
                    <p><strong>Blocked Events:</strong> <?php echo intval($quota['blocked_event_count'] ?? 0); ?></p>
                    <p><strong>Top Tenant:</strong> <?php echo esc_html(array_key_first($quota['tenant_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                    <p><strong>Top API Key:</strong> <?php echo esc_html(array_key_first($quota['api_key_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                    <p><strong>Top Reason:</strong> <?php echo esc_html(array_key_first($quota['reason_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Error Summary</h3>
                    <p><strong>Error Events:</strong> <?php echo intval($errors['error_event_count'] ?? 0); ?></p>
                    <p><strong>Top Status:</strong> <?php echo esc_html(array_key_first($errors['status_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                    <p><strong>Top HTTP Status:</strong> <?php echo esc_html(array_key_first($errors['http_status_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                    <p><strong>Top Provider:</strong> <?php echo esc_html(array_key_first($errors['provider_breakdown'] ?? array()) ?: 'N/A'); ?></p>
                </div>
            </div>
            <?php endif; ?>

            <?php if (!$collector_error) : ?>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;">
                <?php foreach ($health['nodes'] as $node) : ?>
                    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                        <p style="font-size:12px;color:#64748b;text-transform:uppercase;margin:0;"><?php echo esc_html($node['location']); ?></p>
                        <h3 style="margin:4px 0 8px;font-size:18px;"><?php echo esc_html($node['label']); ?></h3>
                        <p style="font-weight:600;color:#2563eb;margin-bottom:8px;">Status: <?php echo esc_html($node['status']); ?></p>
                        <ul style="margin:0;padding-left:16px;">
                            <?php foreach ($node['services'] as $service) : ?>
                                <li>
                                    <?php echo esc_html($service['name']); ?>
                                    <strong>(<?php echo esc_html($service['status']); ?>)</strong>
                                </li>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                <?php endforeach; ?>
            </div>

            <div style="margin-top:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;">
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Learn Queue</h3>
                    <p style="font-size:36px;margin:8px 0;"><?php echo intval($workload['learn_queue']['length']); ?></p>
                    <p class="description">Total pending entries</p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Datasets</h3>
                    <p><strong><?php echo intval($workload['datasets']['count']); ?></strong> datasets</p>
                    <p>Latest: <?php echo esc_html($workload['datasets']['latest'] ?: 'N/A'); ?></p>
                </div>
                <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">
                    <h3>Alerts</h3>
                    <?php if (empty($alerts['alerts'])) : ?>
                        <p>Không có cảnh báo.</p>
                    <?php else : ?>
                        <ul style="margin:0;padding-left:16px;">
                            <?php foreach ($alerts['alerts'] as $alert) : ?>
                                <li>
                                    <strong><?php echo esc_html(strtoupper($alert['severity'])); ?>:</strong>
                                    <?php echo esc_html($alert['message']); ?>
                                </li>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                </div>
            </div>
        <?php endif; ?>

        <form method="post" style="max-width:720px;margin:2rem 0;">
            <?php wp_nonce_field('ttai_dashboard_control_save'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="collector_url">Collector URL</label></th>
                    <td>
                        <input type="url" name="<?php echo esc_attr(self::OPTION_KEY); ?>[collector_url]" id="collector_url" value="<?php echo esc_attr($settings['collector_url']); ?>" class="regular-text" required />
                        <p class="description">Ví dụ: http://localhost:8090</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="collector_token">Collector Token</label></th>
                    <td>
                        <input type="text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[collector_token]" id="collector_token" value="<?php echo esc_attr($settings['collector_token']); ?>" class="regular-text" />
                        <p class="description">Để trống nếu collector không đặt token.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="api_base_url">API Base URL</label></th>
                    <td>
                        <input type="url" name="<?php echo esc_attr(self::OPTION_KEY); ?>[api_base_url]" id="api_base_url" value="<?php echo esc_attr($settings['api_base_url']); ?>" class="regular-text" required />
                        <p class="description">Ví dụ: http://127.0.0.1:8000</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="admin_token">Admin Token</label></th>
                    <td>
                        <input type="text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[admin_token]" id="admin_token" value="<?php echo esc_attr($settings['admin_token']); ?>" class="regular-text" />
                        <p class="description">Bearer token cho /api/v1/admin/*</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        </div>
        <?php
    }
}

new TTAI_Dashboard_Control();
