//
//  TTAiApp.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

@main
struct TTAiApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .networkAware()
        }
    }
}

class AppState: ObservableObject {
    @Published var selectedModel: AIModel = .gptMini
    @Published var chatHistory: [ChatMessage] = []
    @Published var isDarkMode: Bool = false
    
    init() {
        // Load saved settings
        loadSettings()
    }
    
    private func loadSettings() {
        // TODO: Load from UserDefaults
    }
    
    private func saveSettings() {
        // TODO: Save to UserDefaults
    }
}

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        SplashScreen()
            .preferredColorScheme(appState.isDarkMode ? .dark : .light)
    }
}