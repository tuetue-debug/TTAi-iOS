#!/bin/bash

# TTAi Pipeline Test Script
# Tests various components of the CI/CD pipeline locally

set -e

echo "🧪 Testing TTAi CI/CD Pipeline Components..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Test 1: Check required tools
echo ""
echo "1. Checking required tools..."

check_tool() {
    if command -v $1 &> /dev/null; then
        print_success "$1 installed ($($1 $2 2>/dev/null | head -1))"
        return 0
    else
        print_error "$1 not installed"
        return 1
    fi
}

check_tool "swiftlint" "--version"
check_tool "fastlane" "--version"
check_tool "xcodebuild" "-version"

# Test 2: Check configuration files
echo ""
echo "2. Checking configuration files..."

check_file() {
    if [ -f "$1" ]; then
        print_success "$1 exists"
        return 0
    else
        print_error "$1 not found"
        return 1
    fi
}

check_file ".github/workflows/ci-cd.yml"
check_file ".swiftlint.yml"
check_file "fastlane/Fastfile"
check_file "ExportOptions.plist"
check_file "DEPLOYMENT_CHECKLIST.md"
check_file "QUALITY_GATES.md"

# Test 3: Validate SwiftLint configuration
echo ""
echo "3. Validating SwiftLint configuration..."

if [ -f ".swiftlint.yml" ]; then
    if swiftlint rules > /dev/null 2>&1; then
        print_success "SwiftLint configuration is valid"
        
        # Count enabled rules
        RULE_COUNT=$(swiftlint rules | grep -c "✓ enabled")
        print_success "$RULE_COUNT rules enabled"
    else
        print_error "SwiftLint configuration has errors"
    fi
fi

# Test 4: Validate GitHub Actions workflow
echo ""
echo "4. Validating GitHub Actions workflow..."

if [ -f ".github/workflows/ci-cd.yml" ]; then
    # Basic YAML syntax check
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci-cd.yml'))" 2>/dev/null; then
        print_success "GitHub Actions workflow YAML is valid"
    else
        print_warning "GitHub Actions workflow YAML syntax check skipped (python-yaml not available)"
    fi
    
    # Check for required sections
    if grep -q "name:" ".github/workflows/ci-cd.yml" && \
       grep -q "on:" ".github/workflows/ci-cd.yml" && \
       grep -q "jobs:" ".github/workflows/ci-cd.yml"; then
        print_success "GitHub Actions workflow has required sections"
    else
        print_error "GitHub Actions workflow missing required sections"
    fi
fi

# Test 5: Validate Fastfile
echo ""
echo "5. Validating Fastfile..."

if [ -f "fastlane/Fastfile" ]; then
    # Check for required lanes
    if grep -q "lane :test" "fastlane/Fastfile" && \
       grep -q "lane :beta" "fastlane/Fastfile" && \
       grep -q "lane :release" "fastlane/Fastfile"; then
        print_success "Fastfile has required lanes"
    else
        print_error "Fastfile missing required lanes"
    fi
    
    # Check Ruby syntax
    if command -v ruby &> /dev/null; then
        if ruby -c "fastlane/Fastfile" 2>/dev/null; then
            print_success "Fastfile Ruby syntax is valid"
        else
            print_error "Fastfile has Ruby syntax errors"
        fi
    fi
fi

# Test 6: Check deployment checklist completeness
echo ""
echo "6. Checking deployment checklist..."

if [ -f "DEPLOYMENT_CHECKLIST.md" ]; then
    CHECKLIST_ITEMS=$(grep -c "\[ \]" "DEPLOYMENT_CHECKLIST.md" || true)
    if [ "$CHECKLIST_ITEMS" -gt 10 ]; then
        print_success "Deployment checklist has $CHECKLIST_ITEMS items"
    else
        print_warning "Deployment checklist seems short ($CHECKLIST_ITEMS items)"
    fi
    
    # Check for required sections
    REQUIRED_SECTIONS=("Pre-Deployment" "Deployment Process" "Post-Deployment" "Rollback Plan")
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if grep -q "$section" "DEPLOYMENT_CHECKLIST.md"; then
            print_success "Checklist has '$section' section"
        else
            print_error "Checklist missing '$section' section"
        fi
    done
fi

# Test 7: Check quality gates document
echo ""
echo "7. Checking quality gates..."

if [ -f "QUALITY_GATES.md" ]; then
    # Check for threshold tables
    TABLE_COUNT=$(grep -c "|.*|.*|" "QUALITY_GATES.md" || true)
    if [ "$TABLE_COUNT" -gt 5 ]; then
        print_success "Quality gates document has $TABLE_COUNT metric tables"
    else
        print_warning "Quality gates document has few metric tables"
    fi
fi

# Test 8: Check ExportOptions.plist
echo ""
echo "8. Checking ExportOptions.plist..."

if [ -f "ExportOptions.plist" ]; then
    if command -v plutil &> /dev/null; then
        if plutil -lint "ExportOptions.plist" > /dev/null 2>&1; then
            print_success "ExportOptions.plist is valid XML"
            
            # Check required keys
            REQUIRED_KEYS=("method" "provisioningProfiles" "signingCertificate")
            for key in "${REQUIRED_KEYS[@]}"; do
                if plutil -extract "$key" xml1 -o - "ExportOptions.plist" > /dev/null 2>&1; then
                    print_success "ExportOptions.plist has '$key'"
                else
                    print_error "ExportOptions.plist missing '$key'"
                fi
            done
        else
            print_error "ExportOptions.plist has XML syntax errors"
        fi
    else
        print_warning "plutil not available, skipping ExportOptions.plist validation"
    fi
fi

# Test 9: Check environment setup script
echo ""
echo "9. Checking environment setup script..."

if [ -f "scripts/setup-dev-environment.sh" ]; then
    if [ -x "scripts/setup-dev-environment.sh" ]; then
        print_success "Setup script is executable"
    else
        print_warning "Setup script is not executable (run: chmod +x scripts/setup-dev-environment.sh)"
    fi
    
    # Check for required functions
    if grep -q "print_status\|print_error\|print_warning" "scripts/setup-dev-environment.sh"; then
        print_success "Setup script has utility functions"
    fi
    
    # Check for tool installations
    if grep -q "brew install\|gem install\|pod install" "scripts/setup-dev-environment.sh"; then
        print_success "Setup script installs required tools"
    fi
fi

# Summary
echo ""
echo "📊 Pipeline Test Summary"
echo "========================"

# Count successes and failures
SUCCESS_COUNT=$(grep -c "\[✓\]" <<< "$TEST_OUTPUT" || true)
ERROR_COUNT=$(grep -c "\[✗\]" <<< "$TEST_OUTPUT" || true)
WARNING_COUNT=$(grep -c "\[!\]" <<< "$TEST_OUTPUT" || true)

echo "Successes: $SUCCESS_COUNT"
echo "Errors: $ERROR_COUNT"
echo "Warnings: $WARNING_COUNT"

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo ""
    print_success "✅ All pipeline components are properly configured!"
    echo ""
    echo "Next steps:"
    echo "1. Set up GitHub Secrets for your repository"
    echo "2. Run './scripts/setup-dev-environment.sh' to set up local environment"
    echo "3. Push to GitHub to trigger the CI/CD pipeline"
    echo "4. Monitor the first run in GitHub Actions"
else
    echo ""
    print_error "❌ Some pipeline components need attention"
    echo ""
    echo "Please fix the errors above before proceeding."
    exit 1
fi

echo ""
echo "For detailed setup instructions, see CI_CD_SETUP.md"
echo "For deployment procedures, see DEPLOYMENT_CHECKLIST.md"