<?php
/**
 * sinvoice-proxy.php — Viettel S-Invoice reverse proxy
 * Deploy lên matbao.vn hosting (shared/VPS)
 * URL: https://sinvoice.tuetue.vn/sinvoice-proxy.php
 *
 * TTAi FastAPI gọi: https://sinvoice.tuetue.vn/sinvoice-proxy.php?path=auth/login
 * Script forward đến: https://api-vinvoice.viettel.vn/services/einvoiceapplication/api/auth/login
 *
 * Bảo mật: chỉ cho phép request từ TTAi server IP
 */

// ── Cấu hình ──────────────────────────────────────────────────────────────────

define('VIETTEL_BASE', 'https://api-vinvoice.viettel.vn/services/einvoiceapplication/api');
define('VIETTEL_SANDBOX_BASE', 'https://api-demo.viettel.vn/services/einvoiceapplication/api');

// IP của TTAi server (thay bằng IP thực của vannt-work-op hoặc server TTAi)
// Để trống mảng = cho phép tất cả (không khuyến nghị production)
$ALLOWED_IPS = [
    // 'xxx.xxx.xxx.xxx',   // IP TTAi server
];

$USE_SANDBOX = getenv('SINVOICE_SANDBOX') === '1' || false;

// ── Kiểm tra IP whitelist ─────────────────────────────────────────────────────

$client_ip = $_SERVER['HTTP_X_FORWARDED_FOR']
    ?? $_SERVER['HTTP_X_REAL_IP']
    ?? $_SERVER['REMOTE_ADDR']
    ?? '';

// Lấy IP đầu tiên nếu có multiple
$client_ip = trim(explode(',', $client_ip)[0]);

if (!empty($ALLOWED_IPS) && !in_array($client_ip, $ALLOWED_IPS, true)) {
    http_response_code(403);
    echo json_encode(['error' => 'Forbidden', 'ip' => $client_ip]);
    exit;
}

// ── Build target URL ─────────────────────────────────────────────────────────

$path = $_GET['path'] ?? '';
$path = ltrim($path, '/');
if (empty($path)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing ?path= parameter']);
    exit;
}

$base = $USE_SANDBOX ? VIETTEL_SANDBOX_BASE : VIETTEL_BASE;
$target_url = $base . '/' . $path;

// ── Forward request ───────────────────────────────────────────────────────────

$method  = $_SERVER['REQUEST_METHOD'];
$body    = file_get_contents('php://input');
$headers = [];

// Forward relevant headers
$forward_headers = ['Content-Type', 'Cookie', 'Authorization', 'Accept'];
foreach ($forward_headers as $h) {
    $key = 'HTTP_' . strtoupper(str_replace('-', '_', $h));
    if (!empty($_SERVER[$key])) {
        $headers[] = "$h: {$_SERVER[$key]}";
    } elseif ($h === 'Content-Type' && !empty($_SERVER['CONTENT_TYPE'])) {
        $headers[] = "Content-Type: {$_SERVER['CONTENT_TYPE']}";
    }
}
$headers[] = 'Host: ' . parse_url($base, PHP_URL_HOST);

$ctx_opts = [
    'http' => [
        'method'          => $method,
        'header'          => implode("\r\n", $headers),
        'content'         => $body ?: null,
        'timeout'         => 90,
        'ignore_errors'   => true,
        'follow_location' => false,
    ],
    'ssl' => [
        'verify_peer'       => true,
        'verify_peer_name'  => true,
    ],
];

$ctx  = stream_context_create($ctx_opts);
$resp = @file_get_contents($target_url, false, $ctx);

// ── Forward response ──────────────────────────────────────────────────────────

$status_line = $http_response_header[0] ?? 'HTTP/1.1 502 Bad Gateway';
preg_match('/HTTP\/\d\.\d (\d+)/', $status_line, $m);
$status_code = (int) ($m[1] ?? 502);
http_response_code($status_code);

// Forward Set-Cookie and Content-Type
foreach ($http_response_header as $h) {
    if (stripos($h, 'Set-Cookie:') === 0 ||
        stripos($h, 'Content-Type:') === 0) {
        header($h, false);
    }
}

echo $resp !== false ? $resp : json_encode(['error' => 'Upstream request failed']);
