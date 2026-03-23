import Foundation

enum AIModel: String, CaseIterable {
    case gptMini = "GPT Mini"
    case deepSeek = "DeepSeek"
    case gemini = "Gemini"
    
    var displayName: String {
        return self.rawValue
    }
}