//
//  AIModel.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import Foundation

enum AIModel: String, Codable, CaseIterable, Identifiable {
    case gptMini = "GPT‑mini"
    case geminiPro = "Gemini‑Pro"
    case deepSeekChat = "DeepSeek‑chat"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .gptMini: return "GPT‑mini"
        case .geminiPro: return "Gemini Pro"
        case .deepSeekChat: return "DeepSeek Chat"
        }
    }
    
    var description: String {
        switch self {
        case .gptMini:
            return "Reasoning mượt, context dài"
        case .geminiPro:
            return "Đa phương thức, cập nhật nhanh"
        case .deepSeekChat:
            return "Chi phí thấp, tốt cho tra cứu lỗi"
        }
    }
    
    var apiModelName: String {
        switch self {
        case .gptMini: return "cliproxy/gpt-mini"
        case .geminiPro: return "cliproxy/gemini-pro"
        case .deepSeekChat: return "cliproxy/deepseek-chat"
        }
    }
}
