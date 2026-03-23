//
//  ChatMessage.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import Foundation

struct ChatMessage: Identifiable, Codable {
    let id: UUID
    let role: MessageRole
    let content: String
    let model: AIModel?
    let timestamp: Date
    
    init(id: UUID = UUID(), role: MessageRole, content: String, model: AIModel? = nil, timestamp: Date = Date()) {
        self.id = id
        self.role = role
        self.content = content
        self.model = model
        self.timestamp = timestamp
    }
}

enum MessageRole: String, Codable {
    case user
    case assistant
    case system
}

extension ChatMessage {
    static let sampleMessages: [ChatMessage] = [
        ChatMessage(role: .assistant, content: "Hi! I'm Tuệ Tuệ. How can I help you today?", model: .gptMini),
        ChatMessage(role: .user, content: "How to make a network call in Swift?", model: .gptMini),
        ChatMessage(role: .assistant, content: "Use URLSession. Here's an example with async/await...", model: .gptMini)
    ]
}