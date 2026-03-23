//
//  ChatView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct ChatView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = ChatViewModel()
    @State private var messageText = ""
    @FocusState private var isInputFocused: Bool
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Chat messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(viewModel.messages) { message in
                                ChatBubble(message: message)
                            }
                            
                            if viewModel.isLoading {
                                ThinkingIndicator()
                            }
                        }
                        .padding()
                    }
                    .onChange(of: viewModel.messages.count) { _, _ in
                        scrollToBottom(proxy: proxy)
                    }
                }
                
                // Model selector
                ModelSelectorView(selectedModel: $appState.selectedModel)
                    .padding(.horizontal)
                    .padding(.vertical, 12)
                    .background(Color(.systemGray6))
                
                // Input area
                HStack(spacing: 12) {
                    TextField("Type your message...", text: $messageText, axis: .vertical)
                        .focused($isInputFocused)
                        .padding(12)
                        .background(Color(.systemGray6))
                        .cornerRadius(20)
                        .lineLimit(1...5)
                    
                    Button(action: sendMessage) {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 32))
                            .foregroundColor(messageText.isEmpty ? .gray : .indigo)
                    }
                    .disabled(messageText.isEmpty || viewModel.isLoading)
                }
                .padding()
                .background(Color(.systemBackground))
            }
            .navigationTitle("Tuệ Tuệ AI")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {}) {
                        Image(systemName: "gear")
                    }
                }
            }
        }
    }
    
    private func sendMessage() {
        guard !messageText.isEmpty else { return }
        
        let userMessage = ChatMessage(role: .user, content: messageText, model: appState.selectedModel)
        viewModel.sendMessage(userMessage, using: appState.selectedModel)
        messageText = ""
        isInputFocused = false
    }
    
    private func scrollToBottom(proxy: ScrollViewProxy) {
        guard let lastMessage = viewModel.messages.last else { return }
        withAnimation {
            proxy.scrollTo(lastMessage.id, anchor: .bottom)
        }
    }
}

// MARK: - Chat Bubble

struct ChatBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.role == .user {
                Spacer()
            }
            
            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .background(bubbleBackground)
                    .foregroundColor(bubbleForeground)
                    .clipShape(RoundedRectangle(cornerRadius: 18))
                
                if let model = message.model {
                    Text(model.displayName)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            if message.role == .assistant {
                Spacer()
            }
        }
    }
    
    private var bubbleBackground: Color {
        message.role == .user ? .indigo : Color(.systemGray5)
    }
    
    private var bubbleForeground: Color {
        message.role == .user ? .white : .primary
    }
}

// MARK: - Model Selector

struct ModelSelectorView: View {
    @Binding var selectedModel: AIModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("AI Model")
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack(spacing: 0) {
                ForEach(AIModel.allCases) { model in
                    Button(action: { selectedModel = model }) {
                        VStack(spacing: 4) {
                            Text(model.displayName)
                                .font(.system(size: 14, weight: selectedModel == model ? .semibold : .regular))
                                .foregroundColor(selectedModel == model ? .indigo : .secondary)
                            
                            Circle()
                                .fill(selectedModel == model ? .indigo : .clear)
                                .frame(width: 6, height: 6)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(selectedModel == model ? Color.indigo.opacity(0.1) : Color.clear)
                        .cornerRadius(8)
                    }
                }
            }
            .background(Color(.systemGray5))
            .cornerRadius(10)
        }
    }
}

// MARK: - Thinking Indicator

struct ThinkingIndicator: View {
    @State private var dots = ""
    @State private var timer: Timer?
    
    var body: some View {
        HStack {
            Circle()
                .fill(.indigo)
                .frame(width: 8, height: 8)
                .opacity(0.6)
            
            Text("Thinking\(dots)")
                .font(.body)
                .foregroundColor(.secondary)
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.systemGray5))
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .onAppear { startAnimation() }
        .onDisappear { stopAnimation() }
    }
    
    private func startAnimation() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
            withAnimation {
                dots = String(repeating: ".", count: (dots.count + 1) % 4)
            }
        }
    }
    
    private func stopAnimation() {
        timer?.invalidate()
        timer = nil
    }
}

// MARK: - ViewModel

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = ChatMessage.sampleMessages
    @Published var isLoading = false
    
    func sendMessage(_ message: ChatMessage, using model: AIModel) {
        messages.append(message)
        isLoading = true
        
        Task {
            do {
                let response = try await APIClient.shared.sendChatMessage(
                    messages: messages,
                    model: model
                )
                
                let assistantMessage = ChatMessage(
                    role: .assistant,
                    content: response,
                    model: model
                )
                
                await MainActor.run {
                    messages.append(assistantMessage)
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    let errorMessage = ChatMessage(
                        role: .assistant,
                        content: "Error: \(error.localizedDescription)",
                        model: model
                    )
                    messages.append(errorMessage)
                    isLoading = false
                }
            }
        }
    }
}

#Preview {
    ChatView()
        .environmentObject(AppState())
}