// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TTAi",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "TTAi",
            targets: ["TTAi"]),
    ],
    targets: [
        .target(
            name: "TTAi",
            path: "TTAi",
            exclude: ["Info.plist"],
            resources: [
                .process("Assets.xcassets"),
                .process("TTAi.entitlements")
            ]
        )
    ]
)