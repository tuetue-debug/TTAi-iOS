<?php
/**
 * Plugin Name: TTAi Dashboard Control
 * Description: Hiển thị Control Dashboard của TTAi trong WordPress Admin.
 * Version: 0.2.0
 * Author: Tuệ Tuệ
 */

if (!defined('ABSPATH')) {
    exit;
}

class TTAI_Dashboard_Control {
    const OPTION_KEY = 'ttai_dashboard_control_settings';
    const PAGE_SLUG = 'ttai-dashboard-control';

    public function __construct() {
        add_action('admin_menu', array($this, 'register_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    public function register_menu() {
        add_menu_page(
            __('TTAi Dashboard', 'ttai-dashboard'),
            __('TTAi Dashboard', 'ttai-dashboard'),
            'manage_options',
            self::PAGE_SLUG,
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

    private function get_active_tab() {
        $allowed_tabs = array('overview', 'usage', 'billing', 'quota', 'models', 'system', 'settings');
        $tab = isset($_GET['tab']) ? sanitize_key($_GET['tab']) : 'overview';
        return in_array($tab, $allowed_tabs, true) ? $tab : 'overview';
    }

    private function get_tabs() {
        return array(
            'overview' => __('Overview', 'ttai-dashboard'),
            'usage'    => __('Usage', 'ttai-dashboard'),
            'billing'  => __('Billing', 'ttai-dashboard'),
            'quota'    => __('Quota', 'ttai-dashboard'),
            'models'   => __('Models', 'ttai-dashboard'),
            'system'   => __('System', 'ttai-dashboard'),
            'settings' => __('Settings', 'ttai-dashboard'),
        );
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

    private function render_nav_tabs($active_tab) {
        $tabs = $this->get_tabs();
        echo '<nav class="nav-tab-wrapper" style="margin-bottom:20px;">';
        foreach ($tabs as $tab_key => $tab_label) {
            $class = ($tab_key === $active_tab) ? 'nav-tab nav-tab-active' : 'nav-tab';
            $url = admin_url('admin.php?page=' . self::PAGE_SLUG . '&tab=' . $tab_key);
            echo '<a href="' . esc_url($url) . '" class="' . esc_attr($class) . '">' . esc_html($tab_label) . '</a>';
        }
        echo '</nav>';
    }

    private function render_notice_from_error($error, $fallback_message, $type = 'warning') {
        if (!is_wp_error($error)) {
            return;
        }
        $message = $error->get_error_message() ?: $fallback_message;
        echo '<div class="notice notice-' . esc_attr($type) . '"><p>' . esc_html($message) . '</p></div>';
    }

    private function render_kpi_cards($cards) {
        echo '<div style="margin:16px 0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;">';
        foreach ($cards as $card) {
            echo '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">';
            echo '<p style="margin:0;color:#64748b;font-size:12px;text-transform:uppercase;">' . esc_html($card['eyebrow']) . '</p>';
            echo '<h3 style="margin:8px 0 4px;">' . esc_html($card['title']) . '</h3>';
            echo '<p style="font-size:28px;font-weight:700;margin:0;">' . esc_html($card['value']) . '</p>';
            echo '</div>';
        }
        echo '</div>';
    }

    private function render_info_panels($panels) {
        echo '<div style="margin-top:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;">';
        foreach ($panels as $panel) {
            echo '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">';
            echo '<h3>' . esc_html($panel['title']) . '</h3>';
            if (!empty($panel['rows'])) {
                foreach ($panel['rows'] as $row) {
                    echo '<p><strong>' . esc_html($row['label']) . ':</strong> ' . esc_html($row['value']) . '</p>';
                }
            } else {
                echo '<p>' . esc_html__('Chưa có dữ liệu.', 'ttai-dashboard') . '</p>';
            }
            echo '</div>';
        }
        echo '</div>';
    }

    private function render_overview_tab($settings) {
        $overview = $this->fetch_api('/api/v1/admin/overview?usage_limit=50&recent_events_limit=5', $settings);
        $errors   = $this->fetch_api('/api/v1/admin/errors/summary?limit=50&top_n=5', $settings);
        $quota    = $this->fetch_api('/api/v1/admin/quota/blocked?limit=50&recent_limit=5', $settings);

        $this->render_notice_from_error($overview, __('Không thể tải overview từ FastAPI.', 'ttai-dashboard'));
        $this->render_notice_from_error($errors, __('Không thể tải errors summary từ FastAPI.', 'ttai-dashboard'));
        $this->render_notice_from_error($quota, __('Không thể tải quota summary từ FastAPI.', 'ttai-dashboard'));

        if (is_wp_error($overview) || is_wp_error($errors) || is_wp_error($quota)) {
            return;
        }

        $this->render_kpi_cards(array(
            array('eyebrow' => 'Overview', 'title' => 'Health', 'value' => $overview['health']['summary']['status'] ?? '--'),
            array('eyebrow' => 'Usage', 'title' => 'Window Events', 'value' => intval($overview['usage']['window_event_count'] ?? 0)),
            array('eyebrow' => 'Billing', 'title' => 'Billable Cost', 'value' => $overview['billing']['summary']['billable_estimated_cost'] ?? '--'),
            array('eyebrow' => 'Quota', 'title' => 'Blocked Events', 'value' => intval($quota['blocked_event_count'] ?? 0)),
        ));

        $this->render_info_panels(array(
            array(
                'title' => 'Billing Summary',
                'rows'  => array(
                    array('label' => 'Total Estimated Cost', 'value' => $overview['billing']['summary']['total_estimated_cost'] ?? '--'),
                    array('label' => 'Billable Events', 'value' => intval($overview['billing']['summary']['billable_events'] ?? 0)),
                    array('label' => 'Top Provider', 'value' => array_key_first($overview['billing']['summary']['provider_breakdown'] ?? array()) ?: 'N/A'),
                ),
            ),
            array(
                'title' => 'Quota Watch',
                'rows'  => array(
                    array('label' => 'Blocked Events', 'value' => intval($quota['blocked_event_count'] ?? 0)),
                    array('label' => 'Top Tenant', 'value' => array_key_first($quota['tenant_breakdown'] ?? array()) ?: 'N/A'),
                    array('label' => 'Top API Key', 'value' => array_key_first($quota['api_key_breakdown'] ?? array()) ?: 'N/A'),
                    array('label' => 'Top Reason', 'value' => array_key_first($quota['reason_breakdown'] ?? array()) ?: 'N/A'),
                ),
            ),
            array(
                'title' => 'Error Summary',
                'rows'  => array(
                    array('label' => 'Error Events', 'value' => intval($errors['error_event_count'] ?? 0)),
                    array('label' => 'Top Status', 'value' => array_key_first($errors['status_breakdown'] ?? array()) ?: 'N/A'),
                    array('label' => 'Top HTTP Status', 'value' => array_key_first($errors['http_status_breakdown'] ?? array()) ?: 'N/A'),
                    array('label' => 'Top Provider', 'value' => array_key_first($errors['provider_breakdown'] ?? array()) ?: 'N/A'),
                ),
            ),
        ));
    }

    private function render_placeholder_tab($title, $description, $notes = array()) {
        echo '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;background:#fff;max-width:900px;">';
        echo '<h2 style="margin-top:0;">' . esc_html($title) . '</h2>';
        echo '<p>' . esc_html($description) . '</p>';
        if (!empty($notes)) {
            echo '<ul style="padding-left:18px;">';
            foreach ($notes as $note) {
                echo '<li>' . esc_html($note) . '</li>';
            }
            echo '</ul>';
        }
        echo '</div>';
    }

    private function render_system_tab($settings) {
        $health   = $this->fetch_collector('/health-summary', $settings);
        $workload = $this->fetch_collector('/workloads', $settings);
        $alerts   = $this->fetch_collector('/alerts', $settings);

        $this->render_notice_from_error($health, __('Không thể kết nối collector health.', 'ttai-dashboard'));
        $this->render_notice_from_error($workload, __('Không thể tải workloads từ collector.', 'ttai-dashboard'));
        $this->render_notice_from_error($alerts, __('Không thể tải alerts từ collector.', 'ttai-dashboard'));

        if (is_wp_error($health) || is_wp_error($workload) || is_wp_error($alerts)) {
            return;
        }

        echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;">';
        foreach ($health['nodes'] as $node) {
            echo '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;background:#fff;">';
            echo '<p style="font-size:12px;color:#64748b;text-transform:uppercase;margin:0;">' . esc_html($node['location']) . '</p>';
            echo '<h3 style="margin:4px 0 8px;font-size:18px;">' . esc_html($node['label']) . '</h3>';
            echo '<p style="font-weight:600;color:#2563eb;margin-bottom:8px;">Status: ' . esc_html($node['status']) . '</p>';
            echo '<ul style="margin:0;padding-left:16px;">';
            foreach ($node['services'] as $service) {
                echo '<li>' . esc_html($service['name']) . ' <strong>(' . esc_html($service['status']) . ')</strong></li>';
            }
            echo '</ul>';
            echo '</div>';
        }
        echo '</div>';

        $alerts_rows = array();
        if (!empty($alerts['alerts'])) {
            foreach ($alerts['alerts'] as $alert) {
                $alerts_rows[] = array(
                    'label' => strtoupper($alert['severity'] ?? 'info'),
                    'value' => $alert['message'] ?? '',
                );
            }
        }

        $this->render_info_panels(array(
            array(
                'title' => 'Learn Queue',
                'rows'  => array(
                    array('label' => 'Pending Entries', 'value' => intval($workload['learn_queue']['length'] ?? 0)),
                ),
            ),
            array(
                'title' => 'Datasets',
                'rows'  => array(
                    array('label' => 'Count', 'value' => intval($workload['datasets']['count'] ?? 0)),
                    array('label' => 'Latest', 'value' => $workload['datasets']['latest'] ?? 'N/A'),
                ),
            ),
            array(
                'title' => 'Collector Alerts',
                'rows'  => !empty($alerts_rows) ? $alerts_rows : array(
                    array('label' => 'Status', 'value' => __('Không có cảnh báo.', 'ttai-dashboard')),
                ),
            ),
        ));
    }

    private function render_settings_tab($settings) {
        ?>
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
        <?php
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

        $active_tab = $this->get_active_tab();
        ?>
        <div class="wrap">
            <h1><?php esc_html_e('TTAi Control Dashboard', 'ttai-dashboard'); ?></h1>
            <?php $this->render_nav_tabs($active_tab); ?>

            <?php
            switch ($active_tab) {
                case 'overview':
                    $this->render_overview_tab($settings);
                    break;
                case 'usage':
                    $this->render_placeholder_tab(
                        __('Usage', 'ttai-dashboard'),
                        __('Tab này sẽ hiển thị usage events, usage summary và user drilldowns từ FastAPI admin APIs.', 'ttai-dashboard'),
                        array(
                            '/api/v1/admin/usage/events',
                            '/api/v1/admin/usage/summary',
                            '/api/v1/admin/usage/users/{target_user_id}',
                        )
                    );
                    break;
                case 'billing':
                    $this->render_placeholder_tab(
                        __('Billing', 'ttai-dashboard'),
                        __('Tab này sẽ hiển thị billing summary, tenant/API key breakdown và billing config read-only.', 'ttai-dashboard'),
                        array(
                            '/api/v1/admin/usage/billing-summary',
                            '/api/v1/admin/billing/config',
                        )
                    );
                    break;
                case 'quota':
                    $this->render_placeholder_tab(
                        __('Quota', 'ttai-dashboard'),
                        __('Tab này sẽ hiển thị quota lookup, remaining allowance và blocked quota summaries.', 'ttai-dashboard'),
                        array(
                            '/api/v1/admin/quota/status',
                            '/api/v1/admin/quota/status/users/{target_user_id}',
                            '/api/v1/admin/quota/blocked',
                        )
                    );
                    break;
                case 'models':
                    $this->render_placeholder_tab(
                        __('Models', 'ttai-dashboard'),
                        __('Tab này sẽ hiển thị model status, provider state, Ollama health và load balancer metrics.', 'ttai-dashboard'),
                        array(
                            '/api/v1/models/status',
                            '/api/v1/system/loadbalancer/metrics',
                            '/api/v1/system/loadbalancer/providers',
                            '/api/v1/ollama/health',
                            '/api/v1/ollama/models',
                        )
                    );
                    break;
                case 'system':
                    $this->render_system_tab($settings);
                    break;
                case 'settings':
                    $this->render_settings_tab($settings);
                    break;
                default:
                    $this->render_overview_tab($settings);
                    break;
            }
            ?>
        </div>
        <?php
    }
}

new TTAI_Dashboard_Control();
