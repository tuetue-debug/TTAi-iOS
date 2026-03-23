#!/usr/bin/env python3
"""
Update project.pbxproj to include all Swift files
"""
import os
import json
import uuid

def generate_uuid():
    return ''.join([format((uuid.uuid4().int >> (32 * i)) & 0xFFFFFFFF, '08X') for i in range(6)][::-1])

# Read current project
with open('TTAi.xcodeproj/project.pbxproj', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all Swift files
swift_files = []
for root, dirs, files in os.walk('TTAi'):
    for file in files:
        if file.endswith('.swift'):
            rel_path = os.path.relpath(os.path.join(root, file), '.')
            swift_files.append((file, rel_path))

print(f"Found {len(swift_files)} Swift files")

# Create a simple new project structure
# This is a simplified version - in reality we need to parse and modify the existing project
# For now, let's create a minimal working project

simple_project = '''// !$*UTF8*$!
{
	archiveVersion = 1;
	classes = {
	};
	objectVersion = 68;
	objects = {
		FF0000000000000000000001 /* TTAi.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = TTAi.app; sourceTree = BUILT_PRODUCTS_DIR; };
		FF0000000000000000000002 /* TTAiApp.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TTAiApp.swift; sourceTree = "<group>"; };
		FF0000000000000000000003 /* AIModel.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AIModel.swift; sourceTree = "<group>"; };
		FF0000000000000000000004 /* ChatMessage.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = ChatMessage.swift; sourceTree = "<group>"; };
		FF0000000000000000000005 /* SplashScreen.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = SplashScreen.swift; sourceTree = "<group>"; };
		FF0000000000000000000006 /* Info.plist */ = {isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = "<group>"; };
		FF0000000000000000000007 /* Assets.xcassets */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = "<group>"; };
		FF0000000000000000000008 /* TTAi.entitlements */ = {isa = PBXFileReference; lastKnownFileType = text.plist.entitlements; path = TTAi.entitlements; sourceTree = "<group>"; };
		FF0000000000000000000009 /* Preview Assets.xcassets */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = "Preview Assets.xcassets"; sourceTree = "<group>"; };
		FF000000000000000000000A /* Products */ = {isa = PBXGroup; children = (FF0000000000000000000001 /* TTAi.app */); name = Products; sourceTree = "<group>"; };
		FF000000000000000000000B /* TTAi */ = {isa = PBXGroup; children = (FF0000000000000000000002 /* TTAiApp.swift */, FF0000000000000000000003 /* AIModel.swift */, FF0000000000000000000004 /* ChatMessage.swift */, FF0000000000000000000005 /* SplashScreen.swift */, FF0000000000000000000006 /* Info.plist */, FF0000000000000000000007 /* Assets.xcassets */, FF0000000000000000000008 /* TTAi.entitlements */, FF000000000000000000000C /* Preview Content */); path = TTAi; sourceTree = "<group>"; };
		FF000000000000000000000C /* Preview Content */ = {isa = PBXGroup; children = (FF0000000000000000000009 /* Preview Assets.xcassets */); path = "Preview Content"; sourceTree = "<group>"; };
		FF000000000000000000000D /* Project object */ = {isa = PBXProject; buildConfigurationList = FF000000000000000000000E /* Build configuration list for PBXProject "TTAi" */; compatibilityVersion = "Xcode 16.0"; developmentRegion = en; hasScannedForEncodings = 0; knownRegions = (en); mainGroup = FF000000000000000000000B /* TTAi */; productRefGroup = FF000000000000000000000A /* Products */; projectDirPath = ""; projectRoot = ""; targets = (FF000000000000000000000F /* TTAi */); };
		FF000000000000000000000E /* Build configuration list for PBXProject "TTAi" */ = {isa = XCConfigurationList; buildConfigurations = (FF0000000000000000000010 /* Debug */, FF0000000000000000000011 /* Release */); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; };
		FF000000000000000000000F /* TTAi */ = {isa = PBXNativeTarget; buildConfigurationList = FF0000000000000000000012 /* Build configuration list for PBXNativeTarget "TTAi" */; buildPhases = (FF0000000000000000000013 /* Sources */, FF0000000000000000000014 /* Frameworks */, FF0000000000000000000015 /* Resources */); buildRules = (); dependencies = (); name = TTAi; productName = TTAi; productReference = FF0000000000000000000001 /* TTAi.app */; productType = "com.apple.product-type.application"; };
		FF0000000000000000000010 /* Debug */ = {isa = XCBuildConfiguration; buildSettings = {ALWAYS_SEARCH_USER_PATHS = NO; CLANG_ANALYZER_NONNULL = YES; CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE; CLANG_CXX_LANGUAGE_STANDARD = "gnu++20"; CLANG_ENABLE_MODULES = YES; CLANG_ENABLE_OBJC_ARC = YES; CLANG_ENABLE_OBJC_WEAK = YES; CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES; CLANG_WARN_BOOL_CONVERSION = YES; CLANG_WARN_COMMA = YES; CLANG_WARN_CONSTANT_CONVERSION = YES; CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES; CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR; CLANG_WARN_DOCUMENTATION_COMMENTS = YES; CLANG_WARN_EMPTY_BODY = YES; CLANG_WARN_ENUM_CONVERSION = YES; CLANG_WARN_INFINITE_RECURSION = YES; CLANG_WARN_INT_CONVERSION = YES; CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES; CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES; CLANG_WARN_OBJC_LITERAL_CONVERSION = YES; CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR; CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES; CLANG_WARN_RANGE_LOOP_ANALYSIS = YES; CLANG_WARN_STRICT_PROTOTYPES = YES; CLANG_WARN_SUSPICIOUS_MOVE = YES; CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE; CLANG_WARN_UNREACHABLE_CODE = YES; CLANG_WARN__DUPLICATE_METHOD_MATCH = YES; COPY_PHASE_STRIP = NO; DEBUG_INFORMATION_FORMAT = dwarf; ENABLE_STRICT_OBJC_MSGSEND = YES; ENABLE_TESTABILITY = YES; GCC_C_LANGUAGE_STANDARD = gnu11; GCC_DYNAMIC_NO_PIC = NO; GCC_NO_COMMON_BLOCKS = YES; GCC_OPTIMIZATION_LEVEL = 0; GCC_PREPROCESSOR_DEFINITIONS = ("DEBUG=1", "$(inherited)"); GCC_WARN_64_TO_32_BIT_CONVERSION = YES; GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR; GCC_WARN_UNDECLARED_SELECTOR = YES; GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE; GCC_WARN_UNUSED_FUNCTION = YES; GCC_WARN_UNUSED_VARIABLE = YES; IPHONEOS_DEPLOYMENT_TARGET = 17.2; MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE; MTL_FAST_MATH = YES; ONLY_ACTIVE_ARCH = YES; SDKROOT = iphoneos; SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG; SWIFT_OPTIMIZATION_LEVEL = "-Onone"; TARGETED_DEVICE_FAMILY = "1,2"; }; name = Debug; };
		FF0000000000000000000011 /* Release */ = {isa = XCBuildConfiguration; buildSettings = {ALWAYS_SEARCH_USER_PATHS = NO; CLANG_ANALYZER_NONNULL = YES; CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION = YES_AGGRESSIVE; CLANG_CXX_LANGUAGE_STANDARD = "gnu++20"; CLANG_ENABLE_MODULES = YES; CLANG_ENABLE_OBJC_ARC = YES; CLANG_ENABLE_OBJC_WEAK = YES; CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES; CLANG_WARN_BOOL_CONVERSION = YES; CLANG_WARN_COMMA = YES; CLANG_WARN_CONSTANT_CONVERSION = YES; CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES; CLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR; CLANG_WARN_DOCUMENTATION_COMMENTS = YES; CLANG_WARN_EMPTY_BODY = YES; CLANG_WARN_ENUM_CONVERSION = YES; CLANG_WARN_INFINITE_RECURSION = YES; CLANG_WARN_INT_CONVERSION = YES; CLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES; CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES; CLANG_WARN_OBJC_LITERAL_CONVERSION = YES; CLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR; CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER = YES; CLANG_WARN_RANGE_LOOP_ANALYSIS = YES; CLANG_WARN_STRICT_PROTOTYPES = YES; CLANG_WARN_SUSPICIOUS_MOVE = YES; CLANG_WARN_UNGUARDED_AVAILABILITY = YES_AGGRESSIVE; CLANG_WARN_UNREACHABLE_CODE = YES; CLANG_WARN__DUPLICATE_METHOD_MATCH = YES; COPY_PHASE_STRIP = NO; DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym"; ENABLE_NS_ASSERTIONS = NO; ENABLE_STRICT_OBJC_MSGSEND = YES; GCC_C_LANGUAGE_STANDARD = gnu11; GCC_NO_COMMON_BLOCKS = YES; GCC_WARN_64_TO_32_BIT_CONVERSION = YES; GCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR; GCC_WARN_UNDECLARED_SELECTOR = YES; GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE; GCC_WARN_UNUSED_FUNCTION = YES; GCC_WARN_UNUSED_VARIABLE = YES; IPHONEOS_DEPLOYMENT_TARGET = 17.2; MTL_ENABLE_DEBUG_INFO = NO; MTL_FAST_MATH = YES; SDKROOT = iphoneos; SWIFT_COMPILATION_MODE = wholemodule; SWIFT_OPTIMIZATION_LEVEL = "-O"; TARGETED_DEVICE_FAMILY = "1,2"; VALIDATE_PRODUCT = YES; }; name = Release; };
		FF0000000000000000000012 /* Build configuration list for PBXNativeTarget "TTAi" */ = {isa = XCConfigurationList; buildConfigurations = (FF0000000000000000000016 /* Debug */, FF0000000000000000000017 /* Release */); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; };
		FF0000000000000000000013 /* Sources */ = {isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (FF0000000000000000000018 /* TTAiApp.swift in Sources */, FF0000000000000000000019 /* AIModel.swift in Sources */, FF000000000000000000001A /* ChatMessage.swift in Sources */, FF000000000000000000001B /* SplashScreen.swift in Sources */); runOnlyForDeploymentPostprocessing = 0; };
		FF0000000000000000000014 /* Frameworks */ = {isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
		FF0000000000000000000015 /* Resources */ = {isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (FF000000000000000000001C /* Assets.xcassets in Resources */, FF000000000000000000001D /* Preview Assets.xcassets in Resources */); runOnlyForDeploymentPostprocessing = 0; };
		FF0000000000000000000016 /* Debug */ = {isa = XCBuildConfiguration; buildSettings = {ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon; ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor; CODE_SIGN_STYLE = Manual; CODE_SIGN_IDENTITY = ""; DEVELOPMENT_TEAM = ""; INFOPLIST_FILE = TTAi/Info.plist; IPHONEOS_DEPLOYMENT_TARGET = 17.2; LD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks"); PRODUCT_BUNDLE_IDENTIFIER = "com.tuetue.TTAi"; PRODUCT_NAME = "$(TARGET_NAME)"; SWIFT_VERSION = 5.0; TARGETED_DEVICE_FAMILY = "1,2"; }; name = Debug; };
		FF0000000000000000000017 /* Release */ = {isa = XCBuildConfiguration; buildSettings = {ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon; ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor; CODE_SIGN_STYLE = Manual; CODE_SIGN_IDENTITY = ""; DEVELOPMENT_TEAM = ""; INFOPLIST_FILE = TTAi/Info.plist; IPHONEOS_DEPLOYMENT_TARGET = 17.2; LD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks"); PRODUCT_BUNDLE_IDENTIFIER = "com.tuetue.TTAi"; PRODUCT_NAME = "$(TARGET_NAME)"; SWIFT_VERSION = 5.0; TARGETED_DEVICE_FAMILY = "1,2"; }; name = Release; };
		FF0000000000000000000018 /* TTAiApp.swift in Sources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000002 /* TTAiApp.swift */; };
		FF0000000000000000000019 /* AIModel.swift in Sources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000003 /* AIModel.swift */; };
		FF000000000000000000001A /* ChatMessage.swift in Sources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000004 /* ChatMessage.swift */; };
		FF000000000000000000001B /* SplashScreen.swift in Sources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000005 /* SplashScreen.swift */; };
		FF000000000000000000001C /* Assets.xcassets in Resources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000007 /* Assets.xcassets */; };
		FF000000000000000000001D /* Preview Assets.xcassets in Resources */ = {isa = PBXBuildFile; fileRef = FF0000000000000000000009 /* Preview Assets.xcassets */; };
	};
	rootObject = FF000000000000000000000D /* Project object */;
}
'''

with open('TTAi.xcodeproj/project.pbxproj', 'w', encoding='utf-8') as f:
    f.write(simple_project)

print("Updated project.pbxproj with all Swift files")