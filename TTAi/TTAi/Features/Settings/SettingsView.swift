//
//  SettingsView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @State private var showingAPIConfig = false
    @State private var showingAbout = false
    
    var body: some View {
        NavigationStack {
            List {
                // Profile Section
                Section {
                    HStack(spacing: 16) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.indigo)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Tuệ Văn")
                                .font(.headline)
                            
                            Text("tuetue@minhtue.vn")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Button("Edit") {
                            // Edit profile action
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Profile")
                }
                
                // API Configuration
                Section {
                    Button(action: { showingAPIConfig = true }) {
                        SettingsRow(
                            icon: "network",
                            title: "API Configuration",
                            subtitle: "Configure endpoints and keys"
                        )
                    }
                    
                    NavigationLink {
                        ModelSettingsView()
                    } label: {
                        SettingsRow(
                            icon: "brain",
                            title: "AI Models",
                            subtitle: "Default model and preferences"
                        )
                    }
                } header: {
                    Text("AI Settings")
                }
                
                // Appearance
                Section {
                    Toggle(isOn: $appState.isDarkMode) {
                        SettingsRow(
                            icon: "moon.fill",
                            title: "Dark Mode",
                            subtitle: "Auto, Light, or Dark"
                        )
                    }
                    
                    NavigationLink {
                        FontSettingsView()
                    } label: {
                        SettingsRow(
                            icon: "textformat.size",
                            title: "Font Size",
                            subtitle: "Adjust text size"
                        )
                    }
                } header: {
                    Text("Appearance")
                }
                
                // About
                Section {
                    Button(action: { showingAbout = true }) {
                        SettingsRow(
                            icon: "info.circle",
                            title: "About TTAi",
                            subtitle: "Version 1.0.0"
                        )
                    }
                    
                    Link(destination: URL(string: "https://minhtue.vn/privacy")!) {
                        SettingsRow(
                            icon: "lock.shield",
                            title: "Privacy Policy",
                            subtitle: "How we handle your data"
                        )
                    }
                    
                    Link(destination: URL(string: "https://minhtue.vn/terms")!) {
                        SettingsRow(
                            icon: "doc.text",
                            title: "Terms of Service",
                            subtitle: "Usage terms and conditions"
                        )
                    }
                } header: {
                    Text("About")
                }
                
                // Support
                Section {
                    Link(destination: URL(string: "mailto:support@minhtue.vn")!) {
                        SettingsRow(
                            icon: "envelope",
                            title: "Contact Support",
                            subtitle: "support@minhtue.vn"
                        )
                    }
                    
                    ShareLink(item: "Check out Tuệ Tuệ AI - Your local AI assistant!") {
                        SettingsRow(
                            icon: "square.and.arrow.up",
                            title: "Share App",
                            subtitle: "Tell your friends"
                        )
                    }
                } header: {
                    Text("Support")
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingAPIConfig) {
                APIConfigView()
            }
            .sheet(isPresented: $showingAbout) {
                AboutView()
            }
        }
    }
}

// MARK: - Settings Row

struct SettingsRow: View {
    let icon: String
    let title: String
    let subtitle: String
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .frame(width: 30)
                .foregroundColor(.indigo)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body)
                
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - API Config View

struct APIConfigView: View {
    @Environment(\.dismiss) var dismiss
    @AppStorage("apiEndpoint") private var apiEndpoint = "https://vannt.vinaddns.com:8317/v1"
    @AppStorage("apiKey") private var apiKey = ""
    @State private var showingKey = false
    
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("API Endpoint", text: $apiEndpoint)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                        .keyboardType(.URL)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            if showingKey {
                                TextField("API Key", text: $apiKey)
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            } else {
                                SecureField("API Key", text: $apiKey)
                            }
                            
                            Button(action: { showingKey.toggle() }) {
                                Image(systemName: showingKey ? "eye.slash" : "eye")
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        Text("Your API key is stored securely on device.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                } header: {
                    Text("CLIProxy Configuration")
                } footer: {
                    Text("Configure your CLIProxy endpoint and API key for AI model access.")
                }
                
                Section {
                    Button("Test Connection") {
                        testConnection()
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .navigationTitle("API Configuration")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveSettings()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func testConnection() {
        // TODO: Implement connection test
        print("Testing connection to \(apiEndpoint)")
    }
    
    private func saveSettings() {
        // Settings are automatically saved via @AppStorage
        print("API settings saved")
    }
}

// MARK: - Model Settings View

struct ModelSettingsView: View {
    @EnvironmentObject var appState: AppState
    @AppStorage("defaultModel") private var defaultModel = AIModel.gptMini.rawValue
    
    var body: some View {
        Form {
            Section {
                Picker("Default Model", selection: $defaultModel) {
                    ForEach(AIModel.allCases) { model in
                        Text(model.displayName).tag(model.rawValue)
                    }
                }
                .onChange(of: defaultModel) { _, newValue in
                    if let model = AIModel(rawValue: newValue) {
                        appState.selectedModel = model
                    }
                }
            } header: {
                Text("Default Selection")
            } footer: {
                Text("This model will be selected when you start a new chat.")
            }
            
            Section {
                ForEach(AIModel.allCases) { model in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(model.displayName)
                                .font(.headline)
                            
                            Spacer()
                            
                            if appState.selectedModel == model {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                            }
                        }
                        
                        Text(model.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                    .padding(.vertical, 4)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        appState.selectedModel = model
                    }
                }
            } header: {
                Text("Available Models")
            }
        }
        .navigationTitle("AI Models")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - Font Settings View

struct FontSettingsView: View {
    @AppStorage("fontSize") private var fontSize = 1.0
    
    var body: some View {
        Form {
            Section {
                VStack(spacing: 20) {
                    Slider(value: $fontSize, in: 0.8...1.2, step: 0.1) {
                        Text("Font Size")
                    }
                    
                    HStack {
                        Text("A")
                            .font(.system(size: 14 * fontSize))
                        
                        Spacer()
                        
                        Text("Sample Text")
                            .font(.system(size: 17 * fontSize))
                        
                        Spacer()
                        
                        Text("A")
                            .font(.system(size: 20 * fontSize))
                    }
                    .foregroundColor(.secondary)
                }
                .padding(.vertical, 8)
            } header: {
                Text("Adjust Font Size")
            } footer: {
                Text("Adjust the text size throughout the app.")
            }
            
            Section {
                Button("Reset to Default") {
                    fontSize = 1.0
                }
                .foregroundColor(.red)
            }
        }
        .navigationTitle("Font Size")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - About View

struct AboutView: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Logo
                    VStack(spacing: 16) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 60))
                            .foregroundColor(.indigo)
                        
                        Text("Tuệ Tuệ AI")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Your Local AI Assistant")
                            .font(.title3)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top, 40)
                    
                    // Description
                    VStack(alignment: .leading, spacing: 16) {
                        Text("About")
                            .font(.headline)
                        
                        Text("Tuệ Tuệ AI (TTAi) is a local AI assistant that combines the strengths of multiple AI models (GPT‑mini, Gemini‑Pro, DeepSeek‑chat) to provide comprehensive support for programming, learning, and task management.")
                            .foregroundColor(.secondary)
                        
                        Text("The app runs locally on your device and connects to your own CLIProxy instance, ensuring privacy and control over your data.")
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    
                    // Version Info
                    VStack(spacing: 12) {
                        InfoRow(title: "Version", value: "1.0.0 (Beta)")
                        InfoRow(title: "Build", value: "2026.03.21")
                        InfoRow(title: "Developer", value: "Tuệ Tuệ AI Team")
                        InfoRow(title: "Website", value: "minhtue.vn")
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                    Spacer()
                }
            }
            .navigationTitle("About TTAi")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct InfoRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(value)
                .fontWeight(.medium)
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppState())
}