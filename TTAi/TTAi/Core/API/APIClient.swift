//
//  APIClient.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import Foundation

class APIClient {
    static let shared = APIClient()
    
    let baseURL = "https://vannt.vinaddns.com:8317/v1"  //Bỏ private
    let session: URLSession                             //Bỏ private
    
    // Development flag - set to true to use mock data
    private let useMockData = false
    
    init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: configuration)
    }
    
    func sendChatMessage(
        messages: [ChatMessage],
        model: AIModel,
        temperature: Double = 0.7
    ) async throws -> String {
        
        // Use mock data for development/testing
        if useMockData {
            return try await MockAPIClient.shared.sendChatMessage(
                messages: messages,
                model: model,
                temperature: temperature
            )
        }
        let endpoint = "\(baseURL)/chat/completions"
        
        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = ChatRequest(
            model: model.apiModelName,
            messages: messages.map { message in
                ChatRequest.Message(role: message.role.rawValue, content: message.content)
            },
            temperature: temperature
        )
        
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0)
        }
        
        let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
        return chatResponse.choices.first?.message.content ?? ""
    }
}

// MARK: - Request/Response Models

struct ChatRequest: Encodable {
    let model: String
    let messages: [Message]
    let temperature: Double
    
    struct Message: Encodable {
        let role: String
        let content: String
    }
}

struct ChatResponse: Decodable {
    let id: String
    let choices: [Choice]
    
    struct Choice: Decodable {
        let message: Message
        
        struct Message: Decodable {
            let content: String
        }
    }
}

// MARK: - Errors

enum APIError: Error, LocalizedError {
    case invalidURL
    case serverError(statusCode: Int)
    case decodingError
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API endpoint"
        case .serverError(let statusCode):
            return "Server error (HTTP \(statusCode))"
        case .decodingError:
            return "Failed to parse response"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}
