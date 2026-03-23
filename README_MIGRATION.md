# TTAi-Xcode Migration Notes (2026-03-22)

Các thu m?c sau dã du?c copy vào G:\Shared drives\tuetue\TTAi-Xcode\TTAi\TTAi:

- App/
- Core/
- Features/
- Resources/ (bao g?m Assets.xcassets, AppIcon placeholder)

## Vi?c b?n c?n làm trong Xcode (khi quay l?i Mac)
1. M? TTAi-Xcode/TTAi/TTAi.xcodeproj.
2. Trong Project Navigator, t?o các group tuong ?ng (App, Core, Features, Resources).
3. Chu?t ph?i m?i group ? **Add Files to "TTAi"…** ? tr? vào thu m?c cùng tên trong TTAi/TTAi/ ? nh? tick "Create groups" và target TTAi.
4. V?i Resources, sau khi thêm Assets.xcassets/AppIcon m?i, xóa asset template cu n?u còn.
5. Xóa ContentView.swift và Preview Content n?u Xcode v?n li?t kê (mình dã xóa file v?t lý).
6. Ð?m b?o TTAiApp.swift dang dùng file t? thu m?c App (mình dã copy dè s?n).
7. Clean build (Shift+?+K) r?i ch?y simulator (?R).

## Ghi chú khác
- B? AppIcon placeholder: Resources/AppIcon.appiconset.
- N?u c?n test target, b?n có th? kéo thu m?c Tests/ t? repo cu vào group TTAiTests.
- Các scripts/branding/docs v?n n?m trong G:\Shared drives\tuetue\Tests\TTAiTests\TTAi-iOS d? tham chi?u.

C?n mình b? sung file nào n?a c? nh?n nhé!
