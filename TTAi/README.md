# TTAi iOS Application

![iOS CI](https://github.com/tuetue-debug/TTAi-iOS/actions/workflows/ios.yml/badge.svg)

## 🚀 Overview
TTAi iOS app - AI-powered coding assistant with real-time code generation and intelligent assistance.

## 📱 Features
- **AI Chat Interface**: Interactive chat with TTAi AI assistant
- **Code Generation**: Real-time Swift/Objective-C code generation
- **Project Integration**: Works with Xcode projects
- **Local API Support**: Connects to local TTAi backend
- **Offline Capabilities**: Core functionality works offline

## 🛠️ Tech Stack
- **Language**: Swift 5.9+
- **Framework**: SwiftUI + Combine
- **Minimum iOS**: 17.0+
- **Architecture**: MVVM + Clean Architecture
- **Dependency Management**: Swift Package Manager

## 🏗️ Project Structure
```
TTAi/
├── Sources/           # Main application source code
├── Tests/            # Unit and UI tests
├── Resources/        # Assets, icons, localization
├── fastlane/         # CI/CD automation
└── .github/          # GitHub Actions workflows
```

## 🚦 Getting Started

### Prerequisites
- Xcode 15.0+
- iOS 17.0+ simulator or device
- Git

### Installation
1. Clone the repository:
```bash
git clone https://github.com/tuetue-debug/TTAi-iOS.git
cd TTAi-iOS
```

2. Open in Xcode:
```bash
open TTAi.xcworkspace
```

3. Build and run (Command + R)

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
xcodebuild test -scheme TTAi -destination 'platform=iOS Simulator,name=iPhone 15'
```

### UI Tests
```bash
# Run UI tests
xcodebuild test -scheme TTAiUITests -destination 'platform=iOS Simulator,name=iPhone 15'
```

## 🔄 CI/CD Pipeline

### GitHub Actions
Automated workflow runs on:
- **Push to main/develop**: Build, test, and quality checks
- **Pull requests**: Validate changes before merge
- **Scheduled**: Daily builds and tests

### Pipeline Stages:
1. **Build**: Compile app and dependencies
2. **Test**: Run unit and UI tests
3. **Quality**: SwiftLint, code coverage
4. **Deploy**: App Store Connect (when configured)

## 📊 Code Quality
- **SwiftLint**: Enforces Swift style and conventions
- **Code Coverage**: >80% test coverage target
- **Static Analysis**: Xcode built-in analyzer

## 🚀 Deployment

### Development
- Automatic TestFlight distribution on main branch merge
- Manual builds for feature branches

### Production
- App Store releases via fastlane
- Versioned releases with release notes

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

### Commit Convention
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test updates
- `chore:` Maintenance tasks

## 📄 License
This project is proprietary software.

## 📞 Support
- **Issues**: [GitHub Issues](https://github.com/tuetue-debug/TTAi-iOS/issues)
- **Documentation**: In-code documentation and README files

---

**Built with ❤️ by the TTAi Team**