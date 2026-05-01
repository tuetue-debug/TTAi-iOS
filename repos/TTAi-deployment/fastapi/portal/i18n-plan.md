# i18n Plan — console.tuetue.vn

## 1. Mục tiêu

Đa ngôn ngữ cho developer portal console.tuetue.vn, phục vụ expansion sang:
- **Thị trường gốc:** Việt Nam (tiếng Việt)
- **Thị trường mở rộng:** Mỹ/Anh (English), Pháp (Français), Trung Quốc (中文), Hàn Quốc (한국어), Nhật (日本語)

**Cơ chế:** Auto-detect qua `Accept-Language` + GeoIP, cho phép override bằng dropdown.

---

## 2. Phân tích hiện trạng

### Stack
- **Vue 3** (^3.5.32) + **Vue Router 4** (^4.5.1) + **Vite 8**
- **SPA thuần** — mọi text là hardcoded trong 26 `.vue` files (~2049 text segments)
- **Không có i18n library hiện tại**
- **Không có backend API endpoint cho locale** — FastAPI chỉ serve SPA + API

### Điểm cần xử lý
- Template text: titles, labels, buttons, descriptions, legal pages (Terms, Privacy ~2000+ words mỗi page)
- Dynamic content: API response text (login errors, validation messages, pricing table)
- Route titles: Vue Router meta titles
- SEO: `<title>`, `<meta>` tags

---

## 3. Chiến lược đề xuất: **vue-i18n** (tiêu chuẩn ngành)

### Ưu điểm
- **Chuẩn Vue ecosystem** — plugin chính thức, maintenance tốt, community lớn
- **Lazy-loading** — mỗi locale file riêng, chỉ tải locale cần thiết
- **Số ít (pluralization)** — quan trọng cho pricing/usage text
- **ICU message format** — hỗ trợ biến, số nhiều, ngữ cảnh
- **Composable `useI18n()`** — gọn, type-safe
- **Tích hợp Vue Router** — locale prefix routing optional

### Nhược điểm
- Bundle size: vue-i18n ~5KB gzipped
- Cần refactor ~2049 segments — effort lớn

---

## 4. So sánh 3 approaches

### Option A: vue-i18n (Recommend)
| Tiêu chí | Điểm |
|---|---|
| Effort setup | ⭐⭐⭐⭐ (thấp — chỉ cần `npm i`) |
| Effort refactor | ⭐⭐ (cao — sửa 26 files) |
| Runtime perf | ⭐⭐⭐⭐⭐ (lazy chunks) |
| Pluralization | ⭐⭐⭐⭐⭐ (built-in) |
| Lazy loading | ⭐⭐⭐⭐⭐ |
| Community/Support | ⭐⭐⭐⭐⭐ |
| TypeScript support | ⭐⭐⭐⭐⭐ |
| Auto locale detect | ⭐⭐⭐⭐ (browser API) |

**Tổng:** 28/30

### Option B: vue3-gettext
| Tiêu chí | Điểm |
|---|---|
| Effort setup | ⭐⭐⭐ |
| Effort refactor | ⭐⭐ (gettext annotation) |
| Extraction tool | ⭐⭐⭐⭐ (xgettext) |
| Pluralization | ⭐⭐⭐⭐ |
| Lazy loading | ⭐⭐⭐ |
| Community | ⭐⭐⭐ |

**Tổng:** 20/30 — không phổ biến bằng vue-i18n.

### Option C: Custom i18n (lightweight)
| Tiêu chí | Điểm |
|---|---|
| Effort setup | ⭐⭐⭐⭐⭐ |
| Effort refactor | ⭐⭐ |
| Bundle size | ⭐⭐⭐⭐⭐ (~1KB) |
| Pluralization | ⭐⭐ (tự code) |
| Lazy loading | ⭐⭐ (tự code) |
| Maintenability | ⭐⭐ |
| TypeScript | ⭐⭐ |

**Tổng:** 20/30 — ổn nếu chỉ cần mini, nhưng không scale được.

### Option D: i18next (framework-agnostic)
| Tiêu chí | Điểm |
|---|---|
| Effort setup | ⭐⭐⭐ |
| Effort refactor | ⭐⭐ |
| React heritage | ⭐⭐⭐ |
| Cache/Backend | ⭐⭐⭐⭐⭐ |
| Lazy loading | ⭐⭐⭐⭐⭐ |
| Vue integration | ⭐⭐ (vue-i18next wrapper) |

**Tổng:** 22/30 — mạnh nhưng quá nặng cho Vue project.

---

## 5. Kế hoạch triển khai (2 phases)

### Phase 1: Foundation (ước tính 3-4h)
1. `npm install vue-i18n@latest`
2. Tạo `src/i18n/`:
   - `index.js` — VueI18n instance setup
   - `locales/en.json` — English (base, 100%)
   - `locales/vi.json` — Vietnamese (copy từ bản dịch thực tế)
   - `locales/fr.json` — French (placeholder)
   - `locales/zh.json` — Chinese (placeholder)
   - `locales/ko.json` — Korean (placeholder)
   - `locales/ja.json` — Japanese (placeholder)
3. `main.js` — `app.use(i18n)` + locale auto-detect
4. `App.vue` — inject `$t()`, watch locale changes
5. **Auto-detect logic:**
   - Check `navigator.language`
   - Fallback `Accept-Language` từ server (nếu FastAPI pass header)
   - Save preference → `localStorage`
   - Dropdown override trong TopNav

### Phase 2: Translation (ước tính 6-10h)
1. **English (EN)** — base, đã có sẵn (100%)
2. **Vietnamese (VI)** — hiện tại text đã là tiếng Anh, cần translate từ đầu
3. **French (FR)**, **Chinese (ZH)**, **Korean (KO)**, **Japanese (JA)** — dịch theo batch
4. Refactor từng `.vue`:
   ```
   Before: <h1>Welcome to Tue Tue Console</h1>
   After:  <h1>{{ $t('welcome.title') }}</h1>
   ```
5. **Lazy load locale chunks** — Vite dynamic import cho locale files

### Riêng rẽ: Legal pages
- Terms, Privacy, About → nhiều text (~3000 words mỗi page)
- Nên dịch bằng **AI batch translation** (dùng Gemini/DeepSeek API), không làm tay
- Mỗi locale 1 JSON chunk riêng

---

## 6. Auto-detect flow

```
Browser request → Caddy → FastAPI
                              │
                              ├─ Serve index.html (SPA)
                              └─ pass Accept-Language header (khi proxy)
                                   │
                          SPA load → JS check:
                          1. localStorage.getItem('locale')
                          2. navigator.language → match ['en','vi','fr','zh','ko','ja']
                          3. GeoIP (nếu implement sau)
                          4. Fallback: 'en'
```

---

## 7. Recommended

👉 **Option A: vue-i18n + lazy loading**

Đây là lộ trình chuẩn. Tất cả SaaS platform đa ngôn ngữ (GitLab, Vue core team, Laravel Spark) đều dùng.

Deviation chỉ nên nếu:
- Bundle size cực kỳ quan trọng → Option C
- Team có sẵn i18next expertise → Option D

---

## 8. Phụ thuộc & Risks

### Dependencies
- Vue i18n v10 (Vue 3 compatible): 0 dependencies ngoài vue core

### Risks
1. **Locale detection từ server side (FastAPI)** — hiện FastAPI chỉ serve static HTML, không parse Accept-Language. Giải pháp: detect trên client (navigator.language) là đủ cho phase 1.
2. **SEO impact** — SPA không pre-render nên Google xử lý JS. Xem xét thêm <link rel="alternate" hreflang="..."> trong <head>.
3. **Legal content complexity** — Terms/Privacy có cấu trúc pháp lý phức tạp, cần review per-locale.

---

## 9. Timeline ước tính

| Step | Effort | Dependencies |
|---|---|---|
| Setup + integrate | 30 phút | npm |
| Refactor TopNav + LandingPage + common components | 1h | — |
| Refactor remaining pages | 2h | — |
| Vietnamese translation (full) | 2h | AI translator |
| English → French / Chinese / Korean / Japanese | 3-4h | AI translator |
| Test auto-detect + dropdown | 30 phút | — |
| Test full flow | 30 phút | — |

**Tổng: ~10-12 giờ làm việc thực tế**
**Có thể chia làm 2-3 phiên**
