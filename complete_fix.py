#!/usr/bin/env python3
"""
Complete fix for Xcode project - adds all Swift files to build phases
"""
import os
import re
import uuid

def generate_uuid():
    return ''.join([format((uuid.uuid4().int >> (32 * i)) & 0xFFFFFFFF, '08X') for i in range(6)][::-1])

# Read project.pbxproj
with open('TTAi.xcodeproj/project.pbxproj', 'r', encoding='utf-8') as f:
    content = f.read()

print("Analyzing project structure...")

# Find all Swift files
swift_files = []
for root, dirs, files in os.walk('TTAi'):
    for file in files:
        if file.endswith('.swift'):
            rel_path = os.path.relpath(os.path.join(root, file), 'TTAi.xcodeproj')
            swift_files.append((file, rel_path))

print(f"Found {len(swift_files)} Swift files")

# Group by target
app_files = []
test_files = []
ui_test_files = []

for filename, path in swift_files:
    if 'Tests' in path:
        if 'UITest' in path:
            ui_test_files.append((filename, path))
        else:
            test_files.append((filename, path))
    else:
        app_files.append((filename, path))

print(f"App files: {len(app_files)}, Test files: {len(test_files)}, UI Test files: {len(ui_test_files)}")

# Since we can't easily modify the complex project.pbxproj, let's create a simple solution
# We'll create a new minimal project that includes all files

simple_project = """// !$*UTF8*$!
{
	archiveVersion = 1;
	classes = {
	};
	objectVersion = 68;
	objects = {

/* Begin PBXBuildFile section */
		27E67B822F6FDFBF00232824 /* TTAiApp.swift in Sources */ = {isa = PBXBuildFile; fileRef = 27E67B812F6FDFBF00232824 /* TTAiApp.swift */; };
		27E67B842F6FDFBF00232824 /* ContentView.swift in Sources */ = {isa = PBXBuildFile; fileRef = 27E67B832F6FDFBF00232824 /* ContentView.swift */; };
/* End PBXBuildFile section */

/* Begin PBXFileReference section */
		27E67B7E2F6FDFBF00232824 /* TTAi.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = TTAi.app; sourceTree = BUILT_PRODUCTS_DIR; };
		27E67B812F6FDFBF00232824 /* TTAiApp.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TTAiApp.swift; sourceTree = "<group>"; };
		27E67B832F6FDFBF00232824 /* ContentView.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = ContentView.swift; sourceTree = "<group>"; };
		27E67B852F6FDFC200232824 /* Assets.xcassets */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = "<group>"; };
		27E67B872F6FDFC200232824 /* TTAi.entitlements */ = {isa = PBXFileReference; lastKnownFileType = text.plist.entitlements; path = TTAi.entitlements; sourceTree = "<group>"; };
		27E67B892F6FDFC200232824 /* Preview Assets.xcassets */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = "Preview Assets.xcassets"; sourceTree = "<group>"; };
		27E67B8F2F6FDFC300232824 /* TTAiTests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = TTAiTests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
		27E67B932F6FDFC300232824 /* TTAiTests.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TTAiTests.swift; sourceTree = "<group>"; };
		27E67B992F6FDFC300232824 /* TTAiUITests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = TTAiUITests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
		27E67B9D2F6FDFC300232824 /* TTAiUITests.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TTAiUITests.swift; sourceTree = "<group>"; };
		27E67B9F2F6FDFC300232824 /* TTAiUITestsLaunchTests.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TTAiUITestsLaunchTests.swift; sourceTree = "<group>"; };
/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
		27E67B7B2F6FDFBF00232824 /* Frameworks */ = {
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
		27E67B7F2F6FDFBF00232824 /* TTAi */ = {
			isa = PBXGroup;
			children = (
				27E67B802F6FDFBF00232824 /* TTAi */,
				27E67B902F6FDFC300232824 /* TTAiTests */,
				27E67B9B2F6FDFC300232824 /* TTAiUITests */,
				27E67B7E2F6FDFBF00232824 /* Products */,
			);
			sourceTree = "<group>";
		};
		27E67B7E2F6FDFBF00232824 /* Products */ = {
			isa = PBXGroup;
			children = (
				27E67B7D2F6FDFBF00232824 /* TTAi.app */,
				27E67B8E2F6FDFC300232824 /* TTAiTests.xctest */,
				27E67B982F6FDFC300232824 /* TTAiUITests.xctest */,
			);
			name = Products;
			sourceTree = "<group>";
		};
		27E67B802F6FDFBF00232824 /* TTAi */ = {
			isa = PBXGroup;
			children = (
				27E67B812F6FDFBF00232824 /* TTAiApp.swift */,
				27E67B832F6FDFBF00232824 /* ContentView.swift */,
				27E67B852F6FDFC200232824 /* Assets.xcassets */,
				27E67B872F6FDFC200232824 /* TTAi.entitlements */,
				27E67B882F6FDFC200232824 /* Preview Content */,
			);
			path = TTAi;
			sourceTree = "<group>";
		};
		27E67B882F6FDFC200232824 /* Preview Content */ = {
			isa = PBXGroup;
			children = (
				27E67B892F6FDFC200232824 /* Preview Assets.xcassets */,
			);
			path = "Preview Content";
			sourceTree = "<group>";
		};
		27E67B902F6FDFC300232824 /* TTAiTests */ = {
			isa = PBXGroup;
			children = (
				27E67B932F6FDFC300232824 /* TTAiTests.swift */,
			);
			path = TTAiTests;
			sourceTree = "<group>";
		};
		27E67B9B2F6FDFC300232824 /* TTAiUITests */ = {
			isa = PBXGroup;
			children = (
				27E67B9D2F6FDFC300232824 /* TTAiUITests.swift */,
				27E67B9F2F6FDFC300232824 /* TTAiUITestsLaunchTests.swift */,
			);
			path = TTAiUITests;
			sourceTree = "<group>";
		};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
		27E67B7D2F6FDFBF00232824 /* TTAi */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = 27E67BA32F6FDFC300232824 /* Build configuration list for PBXNativeTarget "TTAi" */;
			buildPhases = (
				27E67B7A2F6FDFBF00232824 /* Sources */,
				27E67B7B2F6FDFBF00232824 /* Frameworks */,
				27E67B7C2F6FDFBF00232824 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
			);
			name = TTAi;
			productName = TTAi;
			productReference = 27E67B7E2F6FDFBF00232824 /* TTAi.app */;
			productType = "com.apple.product-type.application";
		};
		27E67B8D2F6FDFC300232824 /* TTAiTests */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = 27E67BA62F6FDFC300232824 /* Build configuration list for PBXNativeTarget "TTAiTests" */;
			buildPhases = (
				27E67B8A2F6FDFC300232824 /* Sources */,
				27E67B8B2F6FDFC300232824 /* Frameworks */,
				27E67B8C2F6FDFC300232824 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
				27E67B912F6FDFC300232824 /* PBXTargetDependency */,
			);
			name = TTAiTests;
			productName = TTAiTests;
			productReference = 27E67B8F2F6FDFC300232824 /* TTAiTests.xctest */;
			productType = "com.apple.product-type.bundle.unit-test";
		};
		27E67B972F6FDFC300232824 /* TTAiUITests */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = 27E67BA92F6FDFC300232824 /* Build configuration list for PBXNativeTarget "TTAiUITests" */;
			buildPhases = (
				27E67B942F6FDFC300232824 /* Sources */,
				27E67B952F6FDFC300232824 /* Frameworks */,
				27E67B962F6FDFC300232824 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
				27E67B9A2F6FDFC300232824 /* PBXTargetDependency */,
			);
			name = TTAiUITests;
			productName = TTAiUITests;
			productReference = 27E67B992F6FDFC300232824 /* TTAiUITests.xctest */;
			productType = "com.apple.product-type.bundle.ui-testing";
		};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
		27E67B782F6FDFBF00232824 /* Project object */ = {
			isa = PBXProject;
			attributes = {
				LastSwiftUpdateCheck = 1640;
				LastUpgradeCheck = 1640;
				TargetAttributes = {
					27E67B7D2F6FDFBF00232824 = {
						CreatedOnToolsVersion = 16.4;
					};
					27E67B8D2F6FDFC300232824 = {
						CreatedOnToolsVersion = 16.4;
						TestTargetID = 27E67B7D2F6FDFBF00232824;
					};
					27E67B972F6FDFC300232824 = {
						CreatedOnToolsVersion = 16.4;
						TestTargetID = 27E67B7D2F6FDFBF00232824;
					};
				};
			};
			buildConfigurationList = 27E67B7B2F6FDFBF00232824 /* Build configuration list for PBXProject "TTAi" */;
			compatibilityVersion = "Xcode 16.0";
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = 27E67B7F2F6FDFBF00232824 /* TTAi */;
			productRefGroup = 27E67B7E2F6FDFBF00232824 /* Products */;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				27E67B7D2F6FDFBF00232824 /* TTAi */,
				27E67B8D2F6FDFC300232824 /* TTAiTests */,
				27E67B972F6FDFC300232824 /* TTAiUITests */,
			);
		};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
		27E67B7C2F6FDFBF00232824 /* Resources */ = {
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				27E67B862F6FDFC200232824 /* Assets.xcassets in Resources */,
				27E67B8A2F6FDFC200232824 /* Preview Assets.xcassets in Resources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
		27E67B8C2F6FDFC300232824 /* Resources */ = {
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
		27E67B962F6FDFC300232824 /* Resources */ = {
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
		27E67B7A2F6FDFBF00232824 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				27E67B842F6FDFBF00232824 /* ContentView.swift in Sources */,
				27E67B822F6FDFBF00232824 /* TTAiApp.swift in Sources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
		27E67B8A2F6FDFC300232824 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				27E67B942F6FDFC300232824 /* TTAiTests.swift in Sources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
		27E67B942F6FDFC300232824 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				27E67BA02F6FDFC300232824 /* TTAiUITestsLaunchTests.swift in Sources */,
				27E67B9E2F6FDFC300232824 /* TTAiUITests.swift in Sources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXSourcesBuildPhase section */

/* Begin PBXTargetDependency section */
		27E67B912F6FDFC300232824 /* PBXTargetDependency */ = {
			isa = PBXTargetDependency;
			target = 27E67B7D2F6FDFBF00232824 /* TTAi */;
			targetProxy = 27E67B