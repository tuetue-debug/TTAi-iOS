# TTAi CI/CD Pipeline Setup

## Overview
This document describes the complete CI/CD pipeline setup for the TTAi iOS application. The pipeline automates testing, code quality checks, builds, and deployments to TestFlight and App Store.

## Architecture

### Pipeline Stages
```
1. Quality Gates → 2. Unit Tests → 3. UI Tests → 4. Build & Archive → 5. Deployment
      ↓                    ↓              ↓              ↓                  ↓
  SwiftLint           Xcode Test      UI Tests        IPA Export    TestFlight/App Store
  Code Coverage      Mock Testing    Snapshot Tests   Code Signing  Release Management
  Static Analysis    Performance     Accessibility    Size Check    Notifications
```

### Tools Stack
- **CI/CD**: GitHub Actions
- **Build**: Xcode Build System
- **Testing**: XCTest, XCUITest
- **Code Quality**: SwiftLint
- **Deployment**: fastlane
- **Monitoring**: Crashlytics, Analytics
- **Notifications**: Slack, Email

## Setup Instructions

### 1. Prerequisites

#### Development Machine
```bash
# Install required tools
brew install swiftlint
sudo gem install fastlane -NV
brew install cocoapods  # If using CocoaPods

# Verify installations
swiftlint version
fastlane --version
```

#### GitHub Repository
- Repository must be on GitHub
- Enable GitHub Actions
- Set up required secrets (see below)

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

#### Required Secrets
| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `BUILD_CERTIFICATE_BASE64` | Base64 encoded .p12 certificate | Export from Keychain Access |
| `P12_PASSWORD` | Password for .p12 certificate | Set during export |
| `BUILD_PROVISION_PROFILE_BASE64` | Base64 encoded .mobileprovision | Download from Apple Developer |
| `KEYCHAIN_PASSWORD` | Temporary keychain password | Generate random string |
| `APP_STORE_CONNECT_API_KEY` | App Store Connect API key | Generate in App Store Connect |
| `APP_STORE_CONNECT_API_ISSUER` | API key issuer ID | From App Store Connect |
| `APP_STORE_CONNECT_API_KEY_ID` | API key ID | From App Store Connect |

#### Optional Secrets (for notifications)
| Secret Name | Description |
|-------------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |
| `EMAIL_SMTP_PASSWORD` | SMTP password for email notifications |

### 3. Local Development Setup

Run the setup script:
```bash
# Make script executable
chmod +x scripts/setup-dev-environment.sh

# Run setup
./scripts/setup-dev-environment.sh
```

This will:
1. Install required tools (Homebrew, Xcode CLI, SwiftLint, fastlane)
2. Set up Git hooks for pre-commit checks
3. Create environment configuration files
4. Install project dependencies

### 4. Project Configuration

#### Xcode Project Settings
Ensure your Xcode project has:
- **Scheme**: Named "TTAi"
- **Configuration**: Debug and Release
- **Code Signing**: Automatic for development, manual for distribution
- **Versioning**: Use `$(CURRENT_PROJECT_VERSION)` for build number

#### Info.plist Configuration
```xml
<key>CFBundleShortVersionString</key>
<string>1.0.0</string>  <!-- Marketing version -->
<key>CFBundleVersion</key>
<string>1</string>      <!-- Build number -->
```

### 5. Pipeline Configuration Files

#### `.github/workflows/ci-cd.yml`
Main CI/CD workflow that runs on:
- Push to main/develop branches
- Pull requests
- Weekly security scans
- Manual triggers

#### `.swiftlint.yml`
Code quality rules with:
- 150 character line limit
- 80% test coverage requirement
- Custom rules for production code

#### `fastlane/Fastfile`
Automation scripts for:
- Testing (`fastlane test`)
- Building (`fastlane build`)
- Deployment (`fastlane beta`, `fastlane release`)

#### `ExportOptions.plist`
Export configuration for IPA creation.

## Pipeline Details

### Quality Gates
**Purpose**: Ensure code quality before testing
**Checks**:
- SwiftLint with strict rules
- Code coverage threshold (80% minimum)
- No critical static analysis issues
- Dependency security scan

**Failure Action**: Block merge/deployment

### Testing Stage
#### Unit Tests
- Runs all XCTest cases
- Measures code coverage
- Generates HTML and JUnit reports
- Artifacts uploaded for review

#### UI Tests
- Runs XCUITest cases
- Supports snapshot testing
- Runs on iPhone 15 simulator
- Artifacts include screenshots and videos

### Build & Archive
**Process**:
1. Increment build number
2. Import certificates and profiles
3. Build Release configuration
4. Create .xcarchive
5. Export .ipa with App Store settings

**Validation**:
- IPA size < 100MB
- Valid code signing
- No build warnings

### Deployment

#### TestFlight Deployment
**Trigger**: Push to main branch or manual trigger
**Process**:
1. Upload IPA to TestFlight
2. Skip waiting for processing (async)
3. Notify testers (optional)
4. Send deployment notification

#### App Store Deployment
**Trigger**: Manual trigger only
**Process**:
1. Verify on main branch
2. Run all tests
3. Increment version if needed
4. Upload to App Store Connect
5. Submit for review (optional)

## Monitoring & Notifications

### Pipeline Notifications
- **Success**: Green check in GitHub, Slack message
- **Failure**: Red X in GitHub, Slack alert with error details
- **Manual Approval**: Required for production deployment

### App Monitoring
- **Crash Reporting**: Crashlytics integration
- **Performance**: Xcode Metrics, custom analytics
- **User Feedback**: App Store reviews, in-app feedback

## Quality Gates Configuration

### Code Quality Thresholds
| Metric | Warning | Error | Action |
|--------|---------|-------|--------|
| Test Coverage | 70% | 80% | Block deployment |
| SwiftLint Warnings | 5 | 10 | Block merge |
| Build Warnings | 1 | 5 | Block deployment |
| Crash Rate | 0.5% | 1% | Block release |

### Security Gates
- Weekly dependency vulnerability scans
- Secret detection in code
- SSL certificate validation
- API security testing

## Troubleshooting

### Common Issues

#### 1. Code Signing Failures
```bash
# Check certificates
security find-identity -v -p codesigning

# Clean derived data
rm -rf ~/Library/Developer/Xcode/DerivedData
```

#### 2. SwiftLint Errors
```bash
# Run SwiftLint with auto-correct
swiftlint --fix

# Check specific file
swiftlint lint --path File.swift
```

#### 3. Test Failures
```bash
# Run tests locally
fastlane test

# Run specific test class
xcodebuild test -scheme TTAi -only-testing:TTAiTests/ClassName
```

#### 4. Build Size Issues
```bash
# Analyze IPA size
du -sh TTAi.ipa
unzip -l TTAi.ipa | sort -nr

# Check asset catalogs
assetutil -I Assets.car
```

### GitHub Actions Debugging
```yaml
# Enable debug logging
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

## Maintenance

### Regular Updates
| Task | Frequency | Responsible |
|------|-----------|-------------|
| Update dependencies | Monthly | DevOps |
| Review quality gates | Quarterly | Engineering |
| Security audit | Monthly | Security Team |
| Pipeline optimization | As needed | DevOps |

### Backup & Recovery
- **Configuration**: Version controlled in repository
- **Secrets**: Stored in GitHub Secrets
- **Artifacts**: Retained for 90 days
- **Backup**: Regular exports of fastlane match

## Cost Optimization

### GitHub Actions
- Use macOS runners only when needed
- Cache dependencies between runs
- Limit artifact retention period
- Use scheduled jobs during off-hours

### Apple Developer
- Manage certificate expiration
- Clean up old provisioning profiles
- Archive old builds periodically

## Support

### Documentation
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step deployment guide
- [QUALITY_GATES.md](QUALITY_GATES.md) - Quality gate specifications
- [Fastlane Documentation](https://docs.fastlane.tools/) - Deployment automation

### Contact
- **DevOps**: devops@yourcompany.com
- **Engineering**: engineering@yourcompany.com
- **Security**: security@yourcompany.com

### Emergency
For pipeline emergencies:
1. Check GitHub Actions status
2. Review error logs
3. Contact on-call engineer
4. Manual deployment if needed

---

**Last Updated**: March 22, 2026  
**Version**: 1.0.0  
**Maintainer**: DevOps Team