# TTAi Phase 2 Quick Start Guide

## Overview
This guide provides step-by-step instructions to implement Phase 2 infrastructure for TTAi iOS app.

## 1. Firebase Setup (Day 1)

### 1.1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" → Name: `TTAi` → Enable Analytics
3. Create project

### 1.2. Add iOS App
1. In project overview, click iOS icon
2. Bundle ID: `com.ttai.ios` (update as needed)
3. App nickname: `TTAi iOS`
4. Download `GoogleService-Info.plist`

### 1.3. Add to Xcode Project
```bash
# Add GoogleService-Info.plist to Xcode project root
# Don't add to any target groups
```

### 1.4. Add Firebase SDK
In Xcode:
1. File → Add Packages
2. Enter: `https://github.com/firebase/firebase-ios-sdk.git`
3. Add packages:
   - `FirebaseAuth`
   - `FirebaseFirestore`
   - `FirebaseAnalytics`
   - `FirebaseCrashlytics` (optional)

### 1.5. Configure Authentication
1. Firebase Console → Authentication → Sign-in method
2. Enable:
   - Email/Password
   - Google
   - Apple
   - Anonymous

### 1.6. Create Firestore Database
1. Firebase Console → Firestore Database → Create database
2. Start in production mode
3. Location: `asia-southeast1` (Singapore)
4. Copy security rules from `Phase2_Infrastructure_Setup.md`

## 2. RevenueCat Setup (Day 2)

### 2.1. Create RevenueCat Account
1. Sign up at [revenuecat.com](https://www.revenuecat.com/)
2. Create project: `TTAi iOS`
3. Platform: `iOS`
4. Bundle ID: `com.ttai.ios`

### 2.2. Configure App Store Connect
1. App Store Connect → My Apps → TTAi
2. Features → In-App Purchases → Create
3. Products:
   - Monthly: `ttai_monthly` (Subscription)
   - Yearly: `ttai_yearly` (Subscription)
   - Lifetime: `ttai_lifetime` (Non-Consumable)
4. Set pricing and submit for review

### 2.3. Configure RevenueCat Dashboard
1. Products → Add products matching App Store Connect
2. Entitlements → Create:
   - `premium` (maps to all paid products)
3. Offerings → Create default offering

### 2.4. Add RevenueCat SDK
In Xcode:
1. File → Add Packages
2. Enter: `https://github.com/RevenueCat/purchases-ios.git`
3. Add `RevenueCat` package

## 3. iOS Implementation (Days 3-5)

### 3.1. Project Structure
```
TTAi/
├── Sources/
│   ├── Models/
│   │   ├── User.swift
│   │   ├── Chat.swift
│   │   ├── Message.swift
│   │   └── Subscription.swift
│   ├── Services/
│   │   ├── AuthManager.swift
│   │   ├── RevenueCatManager.swift
│   │   ├── DatabaseService.swift
│   │   └── APIService.swift
│   ├── ViewModels/
│   │   ├── AuthViewModel.swift
│   │   ├── ChatViewModel.swift
│   │   └── SubscriptionViewModel.swift
│   └── Views/
│       ├── Authentication/
│       ├── Paywall/
│       └── Profile/
```

### 3.2. Core Files to Create

#### AuthManager.swift
```swift
// Copy from Phase2_Infrastructure_Setup.md section 1.3
```

#### RevenueCatManager.swift
```swift
// Copy from Phase2_Infrastructure_Setup.md section 2.3
```

#### AppDelegate.swift
```swift
import UIKit
import Firebase

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Configure Firebase
        FirebaseApp.configure()
        
        // Enable Firestore offline persistence
        let settings = Firestore.firestore().settings
        settings.isPersistenceEnabled = true
        Firestore.firestore().settings = settings
        
        // Configure RevenueCat
        #if DEBUG
        Purchases.configure(withAPIKey: "appl_DEBUG_API_KEY")
        #else
        Purchases.configure(withAPIKey: "appl_PROD_API_KEY")
        #endif
        
        return true
    }
}
```

### 3.3. Environment Configuration
Create `Config.xcconfig` files:

#### Debug.xcconfig
```
FIREBASE_PLIST = GoogleService-Info-Debug.plist
REVENUECAT_API_KEY = appl_DEBUG_API_KEY
```

#### Release.xcconfig
```
FIREBASE_PLIST = GoogleService-Info.plist
REVENUECAT_API_KEY = appl_PROD_API_KEY
```

## 4. Cloud Functions Setup (Day 6)

### 4.1. Initialize Firebase Cloud Functions
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize project
firebase init functions
# Select TypeScript
# Enable ESLint
# Install dependencies
```

### 4.2. Create Core Functions
Create `functions/src/index.ts`:

```typescript
// Token tracking function
export const trackTokenUsage = functions.firestore
  .document('messages/{messageId}')
  .onCreate(async (snap, context) => {
    // Implementation from Phase2_Infrastructure_Setup.md
  });

// RevenueCat webhook handler
export const revenueCatWebhook = functions.https.onRequest(async (req, res) => {
  // Implementation from Phase2_Infrastructure_Setup.md
});

// Daily token reset
export const resetDailyTokens = functions.pubsub
  .schedule('0 0 * * *') // Midnight daily
  .timeZone('Asia/Bangkok')
  .onRun(async (context) => {
    // Reset all users' tokensUsedToday to 0
  });
```

### 4.3. Deploy Functions
```bash
cd functions
npm run build
firebase deploy --only functions
```

## 5. Testing Checklist

### 5.1. Authentication Testing
- [ ] Email sign up and login
- [ ] Google sign in
- [ ] Apple sign in
- [ ] Anonymous authentication
- [ ] Logout functionality
- [ ] Password reset

### 5.2. Subscription Testing
- [ ] Fetch offerings (sandbox)
- [ ] Purchase monthly subscription
- [ ] Purchase yearly subscription
- [ ] Restore purchases
- [ ] Check trial eligibility
- [ ] Handle failed purchases

### 5.3. Database Testing
- [ ] Create user profile on sign up
- [ ] Update user data
- [ ] Save and load chats
- [ ] Token tracking
- [ ] Offline persistence

### 5.4. Integration Testing
- [ ] Token limits enforce subscription tier
- [ ] Premium features unlocked after purchase
- [ ] Webhook updates user tier
- [ ] Analytics events fire correctly

## 6. Deployment Checklist

### 6.1. Pre-Deployment
- [ ] Update app version and build number
- [ ] Test with TestFlight internal testers
- [ ] Verify all API keys are for production
- [ ] Update Firebase to production project
- [ ] Switch RevenueCat to production mode
- [ ] Configure App Store Connect metadata

### 6.2. App Store Submission
- [ ] Create new app version in App Store Connect
- [ ] Upload build via Xcode or Transporter
- [ ] Fill out submission information
- [ ] Set pricing and availability
- [ ] Submit for review

### 6.3. Post-Deployment
- [ ] Monitor Crashlytics for errors
- [ ] Track revenue in RevenueCat dashboard
- [ ] Monitor Firebase usage and costs
- [ ] Set up alerts for critical issues
- [ ] Prepare marketing materials

## 7. Troubleshooting Common Issues

### 7.1. Firebase Issues
**Problem**: `GoogleService-Info.plist` not found
**Solution**: Ensure file is added to project and target membership is checked

**Problem**: Authentication not working
**Solution**: 
1. Verify sign-in methods are enabled in Firebase Console
2. Check bundle ID matches Firebase configuration
3. Ensure internet connectivity

### 7.2. RevenueCat Issues
**Problem**: Purchases not working in sandbox
**Solution**:
1. Verify StoreKit configuration in Xcode
2. Check RevenueCat API key
3. Ensure products are approved in App Store Connect

**Problem**: Webhooks not firing
**Solution**:
1. Check RevenueCat webhook configuration
2. Verify Firebase Functions are deployed
3. Check function logs in Firebase Console

### 7.3. Database Issues
**Problem**: Security rule errors
**Solution**: Test rules in Firebase Console Rules Playground

**Problem**: Offline data not syncing
**Solution**: Ensure `isPersistenceEnabled = true` in Firestore settings

## 8. Monitoring & Maintenance

### 8.1. Daily Checks
- Review Firebase Console for errors
- Check RevenueCat dashboard for revenue
- Monitor token usage patterns
- Review Crashlytics for new issues

### 8.2. Weekly Tasks
- Analyze user engagement metrics
- Review subscription churn rate
- Check database storage usage
- Update dependencies if needed

### 8.3. Monthly Tasks
- Review and optimize Firestore indexes
- Analyze cost breakdown
- Plan feature updates
- Backup critical data

## 9. Support Resources

### 9.1. Documentation
- [Firebase iOS SDK Documentation](https://firebase.google.com/docs/ios/setup)
- [RevenueCat iOS SDK Documentation](https://docs.revenuecat.com/docs/ios)
- [Firestore Security Rules Guide](https://firebase.google.com/docs/firestore/security/get-started)

### 9.2. Community
- [Firebase Community Slack](https://firebase.community/)
- [RevenueCat Community](https://community.revenuecat.com/)
- [iOS Dev Discord](https://discord.gg/ios)

### 9.3. Tools
- [Firebase Console](https://console.firebase.google.com/)
- [RevenueCat Dashboard](https://app.revenuecat.com/)
- [App Store Connect](https://appstoreconnect.apple.com/)

---

**Next Steps**: After completing Phase 2, proceed to Phase 3: Advanced features like team collaboration, advanced analytics, and web dashboard.
