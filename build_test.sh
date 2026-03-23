#!/bin/bash
# Minimal build test
cat > main.swift << 'EOF'
import SwiftUI

@main
struct TestApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Hello TTAi")
        }
    }
}
EOF

# Create minimal project
cat > Project.swift << 'EOF'
import ProjectDescription

let project = Project(
    name: "TTAi",
    targets: [
        .target(
            name: "TTAi",
            destinations: .iOS,
            product: .app,
            bundleId: "com.tuetue.TTAi",
            infoPlist: .default,
            sources: ["main.swift"],
            resources: [],
            settings: .settings(
                configurations: [
                    .debug(name: "Debug"),
                    .release(name: "Release")
                ]
            )
        )
    ]
)
EOF

echo "Test project created"