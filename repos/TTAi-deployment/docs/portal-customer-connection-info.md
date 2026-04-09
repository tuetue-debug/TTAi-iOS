# TTAi API – Thông tin kết nối cho khách hàng

## 1. Developer Console
- URL: `https://console.tuetue.vn/`
- Dùng để đăng ký, đăng nhập, tạo API key, xem usage, billing, limits, và đọc docs.

## 2. API Base URL
- Base URL: `https://api.tuetue.vn`

## 3. Authentication
Gửi API key qua header:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## 4. Endpoint khởi đầu
### Chat endpoint
```http
POST https://api.tuetue.vn/chat
```

## 5. Ví dụ request
### cURL
```bash
curl -X POST https://api.tuetue.vn/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from client"}'
```

### JavaScript
```js
const res = await fetch('https://api.tuetue.vn/chat', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ message: 'Hello from client' }),
})
```

### Python
```python
import requests

res = requests.post(
    'https://api.tuetue.vn/chat',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json',
    },
    json={'message': 'Hello from client'},
)
```

## 6. Ghi nhớ nhanh
- `console.tuetue.vn` = nơi con người quản lý tài khoản và API keys
- `api.tuetue.vn` = nơi ứng dụng/SDK gọi API
