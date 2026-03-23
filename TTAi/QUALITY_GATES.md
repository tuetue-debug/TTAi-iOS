# TTAi Quality Gates

## Overview
Quality gates are automated checks that must pass before code can be merged or deployed. They ensure code quality, security, and reliability.

## Gate 1: Code Quality

### SwiftLint Rules
| Rule Category | Threshold | Action |
|--------------|-----------|--------|
| **Critical Errors** | 0 | Block merge |
| **Warnings** | < 10 | Warn, review required |
| **Code Style** | Must follow style guide | Auto-fix where possible |

### Code Metrics
| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **Test Coverage** | > 80% | 70-80% | < 70% |
| **Cyclomatic Complexity** | < 15 | 15-25 | > 25 |
| **Function Length** | < 50 lines | 50-100 | > 100 |
| **File Length** | < 500 lines | 500-1000 | > 1000 |
| **Nested Depth** | < 3 levels | 3-4 | > 4 |

### Automatic Fixes
- Trailing whitespace removal
- Unused import removal
- Formatting fixes (where safe)

## Gate 2: Testing

### Unit Tests
| Requirement | Threshold | Verification |
|-------------|-----------|--------------|
| **Test Pass Rate** | 100% | Required for merge |
| **Critical Path Tests** | Must exist | Authentication, payment, core features |
| **Mock Usage** | Required for external dependencies | Network, database, services |
| **Test Naming** | Follow convention | `test[Method]_[Scenario]_[Expected]` |

### UI Tests
| Requirement | Threshold | Notes |
|-------------|-----------|-------|
| **Smoke Tests** | 100% pass | Login, main navigation |
| **Feature Tests** | > 90% pass | New features must have tests |
| **Flaky Tests** | 0 | Retry logic allowed, but must be stable |

### Performance Tests
| Metric | Target | Measurement |
|--------|--------|-------------|
| **App Launch** | < 2 seconds | Cold start on iPhone 15 |
| **Screen Load** | < 1 second | From tap to content visible |
| **Memory Usage** | < 100MB peak | During heavy usage |
| **Battery Impact** | < 20% per hour | Typical usage |

## Gate 3: Security

### Static Analysis
| Check | Requirement | Tool |
|-------|-------------|------|
| **Secret Detection** | No secrets in code | GitHub Secret Scanning |
| **Insecure APIs** | No deprecated/unsafe APIs | Xcode Analyze |
| **Input Validation** | All user input validated | Manual review |
| **SSL Pinning** | Enabled for production | Configuration check |

### Dependency Security
| Check | Frequency | Action |
|-------|-----------|--------|
| **Vulnerability Scan** | Weekly | Block if critical |
| **Outdated Dependencies** | Monthly | Warn if > 6 months |
| **License Compliance** | On add | Must be OSI-approved |

### Data Protection
| Aspect | Requirement | Verification |
|--------|-------------|--------------|
| **Sensitive Data** | Encrypted at rest | Keychain usage |
| **Network Traffic** | TLS 1.2+ | Certificate validation |
| **User Data** | GDPR/CCPA compliant | Privacy manifest |

## Gate 4: Build & Deployment

### Build Requirements
| Requirement | Check | Failure Action |
|-------------|-------|----------------|
| **Compilation** | Zero warnings | Block deployment |
| **Archive Size** | < 100MB | Optimize if exceeded |
| **Bitcode** | Disabled | Configuration check |
| **Code Signing** | Valid for 30+ days | Renew if expiring |

### App Store Requirements
| Requirement | Check | Notes |
|-------------|-------|-------|
| **Metadata Complete** | All fields filled | Screenshots for all devices |
| **Demo Account** | Working credentials | For review |
| **Age Rating** | Accurate | Based on content |
| **Export Compliance** | Updated | For encryption |

## Gate 5: Monitoring & Analytics

### Crash Reporting
| Metric | Target | Action |
|--------|--------|--------|
| **Crash-free Users** | > 99.9% | Investigate if < 99% |
| **Top Crashes** | < 5 occurrences/day | Fix within 24 hours |
| **ANR Rate** | < 0.1% | Optimize if higher |

### Performance Monitoring
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **API Response Time** | < 2 seconds | > 5 seconds |
| **Error Rate** | < 1% | > 5% |
| **User Engagement** | Stable or increasing | > 20% drop |

## Implementation

### GitHub Actions Workflow
```yaml
# Quality gates are implemented in .github/workflows/ci-cd.yml
# They run in this order:
# 1. Quality Gates (SwiftLint, coverage)
# 2. Unit Tests
# 3. UI Tests
# 4. Build & Archive
# 5. Security Scan (weekly)
```

### Local Pre-commit Hooks
```bash
# Install pre-commit hooks
./scripts/setup-hooks.sh

# Hooks include:
# - SwiftLint
# - Tests (affected files only)
# - Secret detection
```

### Fastlane Integration
```ruby
# Quality gates in Fastfile
lane :quality_gate do
  swiftlint
  run_tests
  check_coverage
  security_scan
end
```

## Exceptions Process

### Requesting an Exception
1. **Create Issue**: Document why gate cannot be met
2. **Risk Assessment**: Evaluate impact
3. **Mitigation Plan**: Temporary workaround
4. **Timeline**: Date when will be fixed
5. **Approval**: Requires tech lead + product manager

### Temporary Exceptions
| Gate | Max Duration | Approval Required |
|------|-------------|-------------------|
| Test Coverage | 2 weeks | Tech Lead |
| Performance | 1 week | CTO |
| Security | 0 days | Security Team |
| Crash Rate | 48 hours | Engineering Manager |

## Continuous Improvement

### Metrics Tracking
| Metric | Frequency | Owner |
|--------|-----------|-------|
| Gate Pass Rate | Weekly | DevOps |
| False Positives | Monthly | QA |
| Feedback Cycle | Quarterly | Engineering |

### Process Updates
- Review quality gates quarterly
- Update thresholds based on historical data
- Incorporate team feedback
- Automate manual checks where possible

## Tools & Configuration

### Required Tools
```yaml
swiftlint: 0.54.0+
xcodebuild: 16.0+
fastlane: 2.220.0+
slather: 2.7.1+  # For coverage
```

### Configuration Files
- `.swiftlint.yml` - Code style rules
- `.github/workflows/ci-cd.yml` - CI/CD pipeline
- `fastlane/Fastfile` - Deployment automation
- `scripts/quality-gates.sh` - Local validation

### Integration Points
- **GitHub**: PR checks, status updates
- **Slack**: Notifications, alerts
- **App Store Connect**: Build processing
- **Crashlytics**: Crash monitoring
- **Analytics**: Usage tracking

## Training & Documentation

### Onboarding
1. Read this document
2. Complete SwiftLint tutorial
3. Run local quality checks
4. Submit test PR

### Reference Materials
- [Swift Style Guide](link-to-guide)
- [Testing Best Practices](link-to-guide)
- [Security Guidelines](link-to-guide)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)

### Support Channels
- #engineering-help - General questions
- #devops-support - Pipeline issues
- #security - Security concerns
- #quality-assurance - Testing questions