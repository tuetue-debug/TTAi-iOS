//
//  SplashScreen.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct SplashScreen: View {
    @State private var isActive = false
    @State private var size = 0.8
    @State private var opacity = 0.5
    
    var body: some View {
        if isActive {
            ContentView()
                .environmentObject(AppState())
        } else {
            ZStack {
                Color(.systemBackground)
                    .ignoresSafeArea()
                
                VStack {
                    VStack(spacing: 20) {
                        // Logo
                        ZStack {
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [.indigo, .purple],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 150, height: 150)
                                .shadow(color: .indigo.opacity(0.3), radius: 20)
                            
                            Image(systemName: "sparkles")
                                .font(.system(size: 70))
                                .foregroundColor(.white)
                        }
                        
                        // App name
                        VStack(spacing: 8) {
                            Text("Tuệ Tuệ AI")
                                .font(.system(size: 40, weight: .bold))
                                .foregroundColor(.primary)
                            
                            Text("Your Local AI Assistant")
                                .font(.title3)
                                .foregroundColor(.secondary)
                        }
                    }
                    .scaleEffect(size)
                    .opacity(opacity)
                    .onAppear {
                        withAnimation(.easeIn(duration: 1.2)) {
                            self.size = 0.9
                            self.opacity = 1.0
                        }
                    }
                }
            }
            .onAppear {
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    withAnimation {
                        self.isActive = true
                    }
                }
            }
        }
    }
}

#Preview {
    SplashScreen()
}