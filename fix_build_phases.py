#!/usr/bin/env python3
import os
import re
import uuid

def generate_uuid():
    return ''.join([format((uuid.uuid4().int >> (32 * i)) & 0xFFFFFFFF, '08X') for i in range(6)][::-1])

# Read project.pbxproj
with open('TTAi.xcodeproj/project.pbxproj', 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open('TTAi.xcodeproj/project.pbxproj.backup3', 'w', encoding='utf-8') as f:
    f.write(content)

# Find all Swift files in TTAi directory
swift_files = []
for root, dirs, files in os.walk('TTAi'):
    for file in files:
        if file.endswith('.swift'):
            rel_path = os.path.join(root, file)
            swift_files.append((file, rel_path))

print(f"Found {len(swift_files)} Swift files")

# Extract existing file references and build files
file_ref_pattern = r'(\s+)([A-F0-9]{24}) /\* ([^*]+) \*/ = \{isa = PBXFileReference;[^}]+lastKnownFileType = ([^;]+);[^}]+path = ([^;]+);[^}]+sourceTree = ([^;]+);'
file_refs = list(re.finditer(file_ref_pattern, content, re.DOTALL))

# Map filename to UUID
file_uuid_map = {}
for m in file_refs:
    filename = m.group(3)
    file_uuid = m.group(2)
    path = m.group(5)
    file_uuid_map[filename] = (file_uuid, path)

print(f"File UUID map: {len(file_uuid_map)} entries")

# Find main target sources build phase
sources_phase_match = re.search(r'(27E67B7A2F6FDFBF00232824 /\* Sources \*/ = \{[\s\S]*?files = \([\s\S]*?\);)', content)
if not sources_phase_match:
    print("Could not find main Sources build phase")
    exit(1)

sources_phase = sources_phase_match.group(1)
print(f"Current sources phase files: {sources_phase}")

# Extract current build files in sources phase
current_build_files = re.findall(r'([A-F0-9]{24}) /\* ([^*]+) \*/', sources_phase)
print(f"Current build files in sources: {len(current_build_files)}")

# Find PBXBuildFile section
build_file_section_match = re.search(r'(/\* Begin PBXBuildFile section \*/[\s\S]*?/\* End PBXBuildFile section \*/)', content)
if not build_file_section_match:
    print("Could not find PBXBuildFile section")
    exit(1)

build_file_section = build_file_section_match.group(1)

# Check which files already have build file entries
existing_build_files = {}
for filename, (file_uuid, path) in file_uuid_map.items():
    if filename in [bf[1] for bf in current_build_files]:
        existing_build_files[filename] = file_uuid

print(f"Files already in build phase: {len(existing_build_files)}")

# We need to add build file entries for missing files and add them to sources phase
# This is complex - for now, let's create a simple project from scratch
print("\nGiven the complexity, recommending to create a new Xcode project on macOS.")
print("Alternative: Use xcodegen with a project.yml file.")

# Write a simple project.yml for xcodegen
project_yml = """name: TTAi
targets:
  TTAi:
    type: application
    platform: iOS
    deploymentTarget: "17.2"
    sources:
      - path: TTAi
        excludes:
          - "*.xcodeproj"
          - "*.xcworkspace"
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: Minh-Tue-Trading-Investnent-Joint-Stock-Copany.TTAi
      configs:
        Debug:
          SWIFT_ACTIVE_COMPILATION_CONDITIONS: DEBUG
    dependencies:
      - sdk: SwiftUI.framework
      - sdk: Foundation.framework
      
  TTAiTests:
    type: bundle.unit-test
    platform: iOS
    sources: [TTAi/TTAiTests]
    dependencies:
      - target: TTAi
      
  TTAiUITests:
    type: bundle.ui-testing
    platform: iOS
    sources: [TTAi/TTAiUITests]
    dependencies:
      - target: TTAi
"""

with open('project.yml', 'w', encoding='utf-8') as f:
    f.write(project_yml)

print("Created project.yml for xcodegen. Install xcodegen (brew install xcodegen) and run: xcodegen generate")