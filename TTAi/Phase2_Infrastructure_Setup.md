 == true;
    }
    
    // Admin collections
    match /admin/{document} {
      allow read, write: if isAdmin();
    }
    
    // Config collection - public read, admin write
    match /config/{document} {
      allow read: if true;
      allow write: if isAdmin();
    }
  }
}
```

### 3.3. Cloud Functions for Business Logic

#### Token Tracking Function
```javascript
// Firebase Cloud Function to track token usage
exports.trackTokenUsage = functions.firestore
  .document('messages/{messageId}')
  .onCreate(async (snap, context) => {
    const message = snap.data();
    const userId = message.userId;
    const tokensUsed = message.tokensUsed || 0;
    const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    
    const userRef = admin.firestore().collection('users').doc(userId);
    const usageRef = admin.firestore().collection('token_usage')
      .doc(`${userId}_${date}`);
    
    // Run in transaction
    await admin.firestore().runTransaction(async (transaction) => {
      const userDoc = await transaction.get(userRef);
      const usageDoc = await transaction.get(usageRef);
      
      // Update user's daily tokens
      const userData = userDoc.data();
      const newTokensUsedToday = (userData.tokensUsedToday || 0) + tokensUsed;
      const newTotalTokensUsed = (userData.totalTokensUsed || 0) + tokensUsed;
      
      transaction.update(userRef, {
        tokensUsedToday: newTokensUsedToday,
        totalTokensUsed: newTotalTokensUsed,
        lastActivity: admin.firestore.FieldValue.serverTimestamp()
      });
      
      // Update daily usage record
      if (usageDoc.exists) {
        const usageData = usageDoc.data();
        transaction.update(usageRef, {
          tokensUsed: usageData.tokensUsed + tokensUsed,
          [`modelBreakdown.${message.model}`]: 
            (usageData.modelBreakdown?.[message.model] || 0) + tokensUsed,
          updatedAt: admin.firestore.FieldValue.serverTimestamp()
        });
      } else {
        transaction.set(usageRef, {
          userId: userId,
          date: date,
          tokensUsed: tokensUsed,
          modelBreakdown: {
            [message.model]: tokensUsed
          },
          createdAt: admin.firestore.FieldValue.serverTimestamp(),
          updatedAt: admin.firestore.FieldValue.serverTimestamp()
        });
      }
    });
    
    return null;
  });
```

#### Subscription Sync Function
```javascript
// Sync RevenueCat webhook to Firestore
exports.syncRevenueCatWebhook = functions.https.onRequest(async (req, res) => {
  // Verify webhook signature
  const signature = req.headers['revenuecat-signature'];
  const payload = req.rawBody.toString();
  
  if (!verifySignature(signature, payload)) {
    res.status(401).send('Unauthorized');
    return;
  }
  
  const event = req.body;
  const userId = event.app_user_id;
  const subscriptionId = event.product_id;
  
  const subscriptionRef = admin.firestore()
    .collection('subscriptions')
    .doc(`${userId}_${subscriptionId}`);
  
  const userRef = admin.firestore().collection('users').doc(userId);
  
  switch (event.type) {
    case 'INITIAL_PURCHASE':
    case 'RENEWAL':
      await subscriptionRef.set({
        userId: userId,
        productId: subscriptionId,
        purchaseDate: new Date(event.purchased_at_ms),
        expiryDate: new Date(event.expires_at_ms),
        status: 'active',
        renewalInfo: {
          willRenew: event.will_renew,
          autoRenewStatus: event.auto_renew_status
        },
        receiptData: event.receipt
      }, { merge: true });
      
      // Update user tier
      await userRef.update({
        tier: 'premium',
        subscriptionId: subscriptionId,
        subscriptionExpiry: new Date(event.expires_at_ms),
        dailyTokens: 1000 // Premium users get more tokens
      });
      break;
      
    case 'EXPIRATION':
      await subscriptionRef.update({
        status: 'expired',
        expiryDate: new Date(event.expires_at_ms)
      });
      
      // Downgrade user to free tier
      await userRef.update({
        tier: 'free',
        subscriptionId: null,
        subscriptionExpiry: null,
        dailyTokens: 100
      });
      break;
      
    case 'CANCELLATION':
      await subscriptionRef.update({
        status: 'cancelled',
        renewalInfo: {
          willRenew: false,
          autoRenewStatus: false
        }
      });
      break;
  }
  
  res.status(200).send('OK');
});
```

---

## 4. Architecture Diagrams

### 4.1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     TTAi iOS Application                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   UI     │  │  Auth    │  │ Payment  │  │  Data    │   │
│  │  Layer   │  │  Layer   │  │  Layer   │  │  Layer   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Firebase Services                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Firebase │  │ Firestore│  │ Cloud    │  │ Storage  │   │
│  │  Auth    │  │ Database │  │Functions │  │ (Buckets)│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │RevenueCat│  │App Store │  │CLIProxy  │  │ Analytics│   │
│  │(Payments)│  │ Connect  │  │(AI APIs) │  │  Tools   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2. Authentication Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │────▶│   iOS App    │────▶│ Firebase Auth│────▶│ Firestore DB │
└─────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     │                │                     │                     │
     │                │                     │                     │
     │                │                     ▼                     ▼
     │                │              ┌──────────────┐     ┌──────────────┐
     │                └──────────────│ Auth Token   │◀────│ Create/Update│
     │                               │   Returned   │     │ User Profile │
     │                               └──────────────┘     └──────────────┘
     │                                      │                     │
     │                                      ▼                     ▼
     │                               ┌──────────────┐     ┌──────────────┐
     └───────────────────────────────│  App State   │────▶│  Local Cache │
                                     │   Updated    │     │   Updated    │
                                     └──────────────┘     └──────────────┘
```

### 4.3. Subscription Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │────▶│   Paywall    │────▶│ RevenueCat   │────▶│ App Store    │
└─────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     │                │                     │                     │
     │                │                     │                     │
     │                │                     ▼                     ▼
     │                │              ┌──────────────┐     ┌──────────────┐
     │                └──────────────│  Purchase    │◀────│  Process     │
     │                               │  Completed   │     │  Payment     │
     │                               └──────────────┘     └──────────────┘
     │                                      │                     │
     │                                      ▼                     ▼
     │                               ┌──────────────┐     ┌──────────────┐
     │                               │ RevenueCat   │────▶│ Firebase     │
     │                               │   Webhook    │     │  Functions   │
     │                               └──────────────┘     └──────────────┘
     │                                      │                     │
     │                                      ▼                     ▼
     │                               ┌──────────────┐     ┌──────────────┐
     └───────────────────────────────│ Update User  │◀────│ Update DB &  │
                                     │   Tier in    │     │ Send Notif   │
                                     │     App      │     └──────────────┘
                                     └──────────────┘
```

### 4.4. Token Usage Tracking Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │────▶│ Send Message │────▶│ CLIProxy API │────▶│ AI Response  │
└─────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     │                │                     │                     │
     │                │                     │                     │
     │                │                     ▼                     ▼
     │                │              ┌──────────────┐     ┌──────────────┐
     │                └──────────────│ Count Tokens │◀────│ Parse Response│
     │                               │   Used       │     │   & Tokens   │
     │                               └──────────────┘     └──────────────┘
     │                                      │                     │
     │                                      ▼                     ▼
     │                               ┌──────────────┐     ┌──────────────┐
     │                               │ Save Message │────▶│ Cloud        │
     │                               │  to Firestore│     │  Function    │
     │                               └──────────────┘     └──────────────┘
     │                                      │                     │
     │                                      ▼                     ▼
     │                               ┌──────────────┐     ┌──────────────┐
     └───────────────────────────────│ Update Token │◀────│ Update User  │
                                     │   Counters   │     │  & Usage     │
                                     └──────────────┘     └──────────────┘
```

### 4.5. Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Firestore Database                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────┐     1:N    ┌────────────┐     N:1     ┌────────────┐  │
│  │   users    │◄───────────│   chats    │────────────►│   users    │  │
│  ├────────────┤            ├────────────┤             ├────────────┤  │
│  │ • userId   │            │ • chatId   │             │ • userId   │  │
│  │ • email    │            │ • userId   │             │ • email    │  │
│  │ • tier     │            │ • title    │             │ • tier     │  │
│  │ • tokens   │            │ • messages │             │ • tokens   │  │
│  │ • subs...  │            │ • tags     │             │ • subs...  │  │
│  └────────────┘            └────────────┘             └────────────┘  │
│         │                           │                                  │
│         │ 1:N                       │ 1:N                              │
│         ▼                           ▼                                  │
│  ┌────────────┐            ┌────────────┐                             │
│  │subscriptions│           │  messages  │                             │
│  ├────────────┤            ├────────────┤                             │
│  │ • subId    │            │ • msgId    │                             │
│  │ • userId   │            │ • chatId   │                             │
│  │ • productId│            │ • userId   │                             │
│  │ • status   │            │ • content  │                             │
│  │ • dates    │            │ • tokens   │                             │
│  └────────────┘            └────────────┘                             │
│                                                                         │
│  ┌────────────┐                                                        │
│  │token_usage │                                                        │
│  ├────────────┤                                                        │
│  │ • usageId  │                                                        │
│  │ • userId   │                                                        │
│  │ • date     │                                                        │
│  │ • tokens   │                                                        │
│  │ • breakdown│                                                        │
│  └────────────┘                                                        │
│                                                                         │
│  ┌────────────┐                                                        │
│  │analytics   │                                                        │
│  ├────────────┤                                                        │
│  │ • eventId  │                                                        │
│  │ • userId   │                                                        │
│  │ • eventName│                                                        │
│  │ • props    │                                                        │
│  └────────────┘                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Checklist

### 5.1. Phase 2A: Firebase Setup (Week 1)
- [ ] Create Firebase project
- [ ] Register iOS app in Firebase
- [ ] Download and add `GoogleService-Info.plist` to Xcode
- [ ] Add Firebase SDK via Swift Package Manager
- [ ] Configure Firebase Auth (Email/Password, Google, Apple)
- [ ] Set up Firestore database with initial security rules
- [ ] Implement basic AuthManager in iOS app
- [ ] Test authentication flow end-to-end

### 5.2. Phase 2B: RevenueCat Setup (Week 2)
- [ ] Create RevenueCat account and project
- [ ] Configure App Store Connect with in-app purchases
  - [ ] Create monthly subscription product
  - [ ] Create yearly subscription product  
  - [ ] Create lifetime purchase product
  - [ ] Submit products for review
- [ ] Configure RevenueCat products and entitlements
- [ ] Add RevenueCat SDK to iOS project
- [ ] Implement RevenueCatManager
- [ ] Create basic paywall UI
- [ ] Test purchase flow in sandbox

### 5.3. Phase 2C: Database Implementation (Week 3)
- [ ] Design and implement Firestore collections structure
- [ ] Create User model and Firestore integration
- [ ] Implement chat and message data models
- [ ] Create token usage tracking system
- [ ] Set up subscription data model
- [ ] Implement local caching with Core Data/UserDefaults
- [ ] Write comprehensive security rules
- [ ] Test all CRUD operations

### 5.4. Phase 2D: Cloud Functions (Week 4)
- [ ] Set up Firebase Cloud Functions project
- [ ] Implement token tracking function
- [ ] Create RevenueCat webhook handler
- [ ] Set up daily token reset function
- [ ] Implement analytics event processing
- [ ] Create admin functions for user management
- [ ] Test all cloud functions locally
- [ ] Deploy to Firebase

### 5.5. Phase 2E: Integration & Testing (Week 5)
- [ ] Integrate auth with existing chat functionality
- [ ] Connect token limits to API calls
- [ ] Implement tier-based feature gating
- [ ] Add subscription status checks throughout app
- [ ] Implement offline support and sync
- [ ] Add comprehensive error handling
- [ ] Write unit tests for all new components
- [ ] Perform end-to-end testing

### 5.6. Phase 2F: Monitoring & Analytics (Week 6)
- [ ] Set up Firebase Analytics events
- [ ] Configure Crashlytics for error tracking
- [ ] Create RevenueCat dashboard for revenue tracking
- [ ] Set up Firebase Performance Monitoring
- [ ] Implement user behavior analytics
- [ ] Create admin dashboard for user management
- [ ] Set up alerts and notifications
- [ ] Document monitoring procedures

### 5.7. Deployment Checklist
- [ ] Update app version and build number
- [ ] Test with TestFlight internal testers
- [ ] Submit app update to App Store Connect
- [ ] Configure production Firebase project
- [ ] Switch RevenueCat to production mode
- [ ] Update API endpoints to production
- [ ] Perform final security audit
- [ ] Prepare release notes and documentation

## 6. Cost Estimation

### 6.1. Monthly Costs
- **Firebase Spark Plan**: Free (up to certain limits)
  - Authentication: 10K monthly active users free
  - Firestore: 1GB storage, 50K reads/day free
  - Cloud Functions: 2M