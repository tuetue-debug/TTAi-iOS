#!/bin/bash

# TTAi Development Environment Setup Script
# This script sets up a complete development environment for TTAi iOS app

set -e  # Exit on error

echo "🚀 Setting up TTAi development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check for macOS
if [[ "$(uname)" != "Darwin" ]]; then
    print_error "This script requires macOS for iOS development"
    exit 1
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    print_status "Homebrew installed"
else
    print_status "Homebrew already installed"
fi

# Update Homebrew
print_status "Updating Homebrew..."
brew update

# Install Xcode Command Line Tools
print_status "Checking for Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    print_warning "Xcode Command Line Tools not found. Installing..."
    xcode-select --install
    # Wait for installation
    until xcode-select -p &> /dev/null; do
        sleep 5
    done
    print_status "Xcode Command Line Tools installed"
else
    print_status "Xcode Command Line Tools already installed"
fi

# Install required tools
print_status "Installing development tools..."

# Ruby and Bundler (for fastlane)
if ! command -v ruby &> /dev/null || [[ "$(ruby -v)" != *"3."* ]]; then
    print_warning "Ruby 3.x not found. Installing..."
    brew install ruby
    echo 'export PATH="/usr/local/opt/ruby/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    print_status "Ruby installed"
fi

if ! command -v bundler &> /dev/null; then
    print_warning "Bundler not found. Installing..."
    gem install bundler
    print_status "Bundler installed"
fi

# SwiftLint
if ! command -v swiftlint &> /dev/null; then
    print_warning "SwiftLint not found. Installing..."
    brew install swiftlint
    print_status "SwiftLint installed"
fi

# fastlane
if ! command -v fastlane &> /dev/null; then
    print_warning "fastlane not found. Installing..."
    sudo gem install fastlane -NV
    print_status "fastlane installed"
fi

# CocoaPods (if needed)
if [ -f "Podfile" ]; then
    if ! command -v pod &> /dev/null; then
        print_warning "CocoaPods not found. Installing..."
        sudo gem install cocoapods
        pod setup
        print_status "CocoaPods installed"
    fi
fi

# Node.js (for any JavaScript tooling)
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found. Installing..."
    brew install node
    print_status "Node.js installed"
fi

# Install project dependencies
print_status "Installing project dependencies..."

# Install Ruby gems
if [ -f "Gemfile" ]; then
    print_status "Installing Ruby gems..."
    bundle install
fi

# Install CocoaPods dependencies
if [ -f "Podfile" ]; then
    print_status "Installing CocoaPods dependencies..."
    pod install
fi

# Install Swift Package Manager dependencies
if [ -f "Package.swift" ]; then
    print_status "Resolving Swift Package Manager dependencies..."
    swift package resolve
fi

# Setup Git hooks
print_status "Setting up Git hooks..."
if [ ! -d ".git/hooks" ]; then
    mkdir -p .git/hooks
fi

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# TTAi Pre-commit Hook
# Runs quality checks before allowing commit

echo "🔍 Running pre-commit checks..."

# Run SwiftLint on staged Swift files
STAGED_SWIFT_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.swift$')

if [[ -n "$STAGED_SWIFT_FILES" ]]; then
    echo "Running SwiftLint on staged Swift files..."
    swiftlint lint --strict --path $(echo "$STAGED_SWIFT_FILES" | tr '\n' ' ')
    
    if [ $? -ne 0 ]; then
        echo "❌ SwiftLint failed. Please fix the issues before committing."
        exit 1
    fi
fi

# Check for secrets in staged files
echo "Checking for secrets..."
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

for file in $STAGED_FILES; do
    # Skip binary files
    if [[ "$file" == *.png ]] || [[ "$file" == *.jpg ]] || [[ "$file" == *.pdf ]]; then
        continue
    fi
    
    # Check for potential secrets
    if grep -n "password\|secret\|token\|key\|private_key\|api_key" "$file" | grep -v "test\|mock\|example\|TODO"; then
        echo "⚠️  Potential secret found in $file"
        echo "Please review before committing."
        # Uncomment to block commits with potential secrets
        # exit 1
    fi
done

echo "✅ Pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit
print_status "Git hooks configured"

# Create post-checkout hook for Xcode project generation
cat > .git/hooks/post-checkout << 'EOF'
#!/bin/bash

# Regenerate Xcode project if needed
if [ -f "Package.swift" ] && [ ! -f "TTAi.xcodeproj" ]; then
    echo "Generating Xcode project..."
    swift package generate-xcodeproj
fi

if [ -f "Podfile" ] && [ ! -f "TTAi.xcworkspace" ]; then
    echo "Generating Xcode workspace..."
    pod install
fi
EOF

chmod +x .git/hooks/post-checkout

# Setup environment variables
print_status "Setting up environment variables..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# TTAi Environment Variables
# Copy this to .env.local and fill in your values

# API Keys (for development)
# FIREBASE_API_KEY=your_firebase_api_key
# REVENUECAT_API_KEY=your_revenuecat_api_key
# ANALYTICS_API_KEY=your_analytics_key

# Development Flags
DEBUG=true
ENABLE_LOGGING=true
ENABLE_ANALYTICS=false

# Server URLs
API_BASE_URL=https://api.dev.ttai.com
WEBSOCKET_URL=wss://ws.dev.ttai.com

# Feature Flags
FEATURE_CHAT=true
FEATURE_PAYMENTS=false
FEATURE_ANALYTICS=false
EOF
    print_status ".env template created"
    print_warning "Please copy .env to .env.local and fill in your values"
fi

# Create .env.local template if it doesn't exist
if [ ! -f ".env.local" ]; then
    cp .env .env.local
    print_status ".env.local created (please update with your values)"
fi

# Create Xcode configuration if needed
print_status "Setting up Xcode configurations..."

if [ ! -d "TTAi.xcodeproj" ]; then
    print_warning "Xcode project not found. Creating basic structure..."
    
    # Create basic project structure
    mkdir -p TTAi/Sources
    mkdir -p TTAi/Resources
    mkdir -p TTAiTests
    mkdir -p TTAiUITests
    
    # Create basic Info.plist
    cat > TTAi/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>$(DEVELOPMENT_LANGUAGE)</string>
	<key>CFBundleDisplayName</key>
	<string>TTAi</string>
	<key>CFBundleExecutable</key>
	<string>$(EXECUTABLE_NAME)</string>
	<key>CFBundleIdentifier</key>
	<string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>$(PRODUCT_NAME)</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>LSRequiresIPhoneOS</key>
	<true/>
	<key>UIApplicationSceneManifest</key>
	<dict>
		<key>UIApplicationSupportsMultipleScenes</key>
		<false/>
	</dict>
	<key>UIApplicationSupportsIndirectInputEvents</key>
	<true/>
	<key>UILaunchStoryboardName</key>
	<string>LaunchScreen</string>
	<key>UIRequiredDeviceCapabilities</key>
	<array>
		<string>armv7</string>
	</array>
	<key>UISupportedInterfaceOrientations</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
	</array>
	<key>UISupportedInterfaceOrientations~ipad</key>
	<array>
		<string>UIInterfaceOrientationPortrait</string>
		<string>UIInterfaceOrientationPortraitUpsideDown</string>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
</dict>
</plist>
EOF
    
    print_warning "Basic project structure created. Please open in Xcode to complete setup."
fi

# Verify setup
print_status "Verifying setup..."

# Check tools
echo "Installed tools:"
echo "  Xcode CLI: $(xcode-select -p)"
echo "  Ruby: $(ruby -v)"
echo "  SwiftLint: $(swiftlint version)"
echo "  fastlane: $(fastlane --version | head -1)"
if command -v pod &> /dev/null; then
    echo "  CocoaPods: $(pod --version)"
fi
if command -v node &> /dev/null; then
    echo "  Node.js: $(node --version)"
fi

# Check project files
echo ""
echo "Project files:"
if [ -f "Package.swift" ]; then
    echo "  ✅ Package.swift"
else
    echo "  ❌ Package.swift (not found)"
fi
if [ -f "Podfile" ]; then
    echo "  ✅ Podfile"
else
    echo "  ⚠️  Podfile (not found, using SPM)"
fi
if [ -f "TTAi.xcodeproj" ] || [ -f "TTAi.xcworkspace" ]; then
    echo "  ✅ Xcode project/workspace"
else
    echo "  ⚠️  Xcode project (not found, run 'swift package generate-xcodeproj')"
fi

print_status "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Open TTAi.xcworkspace (or TTAi.xcodeproj) in Xcode"
echo "2. Update .env.local with your API keys"
echo "3. Run 'fastlane test' to verify everything works"
echo "4. Check out DEPLOYMENT_CHECKLIST.md for deployment guidelines"
echo ""
echo "Happy coding! 🚀"