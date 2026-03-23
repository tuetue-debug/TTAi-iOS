//
//  MainTabView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "bubble.left.and.bubble.right")
                }
                .tag(0)
            
            CodeGeneratorView()
                .tabItem {
                    Label("Code", systemImage: "chevron.left.slash.chevron.right")
                }
                .tag(1)
            
            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock.arrow.circlepath")
                }
                .tag(2)
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(3)
        }
        .accentColor(.indigo)
    }
}

#Preview {
    MainTabView()
        .environmentObject(AppState())
}