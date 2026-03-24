//
//  ContentView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        SplashScreen()
            .preferredColorScheme(appState.isDarkMode ? .dark : .light)
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}