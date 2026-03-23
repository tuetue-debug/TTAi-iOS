//
//  TTAiApp.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

@main
struct TTAiApp: App {
    @State private var isDarkMode = false
    
    var body: some Scene {
        WindowGroup {
            ContentView(isDarkMode: $isDarkMode)
        }
    }
}

struct ContentView: View {
    @Binding var isDarkMode: Bool
    
    var body: some View {
        VStack {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            Text("TTAi")
                .font(.largeTitle)
                .fontWeight(.bold)
            Text("Tuệ Tuệ AI Assistant")
                .font(.title2)
                .foregroundColor(.gray)
            Text("Build successful! 🎉")
                .font(.title3)
                .padding(.top, 20)
                .foregroundColor(.green)
        }
        .preferredColorScheme(isDarkMode ? .dark : .light)
        .padding()
    }
}