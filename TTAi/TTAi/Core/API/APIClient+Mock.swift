//
//  APIClient+Mock.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import Foundation

extension APIClient {
    
    // MARK: - Development/Testing Mode
    
    /// Toggle between real API and mock data
    /// Set to true during development to avoid hitting real API
    var isMockModeEnabled: Bool {
        #if DEBUG
        return ProcessInfo.processInfo.environment["USE_MOCK_API"] == "true"
        #else
        return false
        #endif
    }
    
    // MARK: - Mock Implementation
    
    func sendChatMessageMock(
        messages: [ChatMessage],
        model: AIModel,
        temperature: Double = 0.7
    ) async throws -> String {
        // Simulate network delay
        let delaySeconds = Double.random(in: 0.5...2.0)
        try await Task.sleep(nanoseconds: UInt64(delaySeconds * 1_000_000_000))
        
        let lastMessage = messages.last?.content ?? "Hello"
        
        // Generate realistic mock response based on input
        let responses = [
            "I understand you're asking about \"\(lastMessage)\". Based on my analysis using \(model.displayName), here's what I found...",
            "That's an interesting question! As \(model.displayName), I can tell you that \(lastMessage) involves several key considerations.",
            "Regarding \"\(lastMessage)\", the \(model.displayName) model suggests the following approach...",
            "I've analyzed your query about \(lastMessage). Here are the insights from \(model.displayName):",
            "Great question! Using \(model.displayName), I can provide this perspective on \(lastMessage)..."
        ]
        
        let randomResponse = responses.randomElement() ?? "I'm here to help with \(lastMessage)."
        
        // Add some code if the question seems technical
        if lastMessage.lowercased().contains("code") || 
           lastMessage.lowercased().contains("program") ||
           lastMessage.lowercased().contains("function") {
            
            let codeExamples = [
                """
                Here's an example:
                ```swift
                func example() {
                    print("Hello from \(model.displayName)!")
                }
                ```
                """,
                """
                Consider this approach:
                ```python
                def solution():
                    return "Answer from \(model.displayName)"
                ```
                """,
                """
                You could implement it like this:
                ```javascript
                function handleQuery() {
                    console.log("\(model.displayName) response");
                }
                ```
                """
            ]
            
            return "\(randomResponse)\n\n\(codeExamples.randomElement() ?? "")"
        }
        
        return randomResponse
    }
    
    func testConnection() async -> Bool {
        if isMockModeEnabled {
            // Mock connection test always succeeds
            return true
        }
        
        do {
            let endpoint = "\(baseURL)/models"
            let request = URLRequest(url: URL(string: endpoint)!)
            let (_, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                return false
            }
            
            return (200...299).contains(httpResponse.statusCode)
        } catch {
            return false
        }
    }
    
    // MARK: - Configuration Helper
    
    static func configureForDevelopment() {
        #if DEBUG
        // Enable mock mode by setting environment variable
        setenv("USE_MOCK_API", "true", 1)
        
        print("📱 TTAi API Client configured for development")
        print("   Mock mode: ENABLED")
        print("   Real API calls will be simulated")
        #endif
    }
    
    static func configureForProduction() {
        #if DEBUG
        // Disable mock mode
        setenv("USE_MOCK_API", "false", 1)
        
        print("📱 TTAi API Client configured for production")
        print("   Mock mode: DISABLED")
        print("   Real API calls will be made to: https://vannt.vinaddns.com:8317/v1")
        #endif
    }
}

// MARK: - Mock API Response Generator

struct MockResponseGenerator {
    
    static func generateForPrompt(_ prompt: String, model: AIModel) -> String {
        let template = """
        As \(model.displayName), I understand you're asking about:
        
        "\(prompt)"
        
        This is a complex topic with several important aspects to consider. Based on my training data and capabilities as \(model.displayName), I can provide the following insights:
        
        1. **Key Concept**: The fundamental principle here involves understanding the core mechanics.
        2. **Practical Application**: In real-world scenarios, this typically manifests as...
        3. **Best Practices**: When implementing this, consider...
        4. **Common Pitfalls**: Be aware of...
        
        Would you like me to elaborate on any specific aspect, or provide code examples related to this topic?
        
        *Response generated by \(model.displayName) mock system for development purposes.*
        """
        
        return template
    }
    
    static func generateCodeResponse(language: String, description: String) -> String {
        let timestamp = Date().ISO8601Format()
        
        switch language.lowercased() {
        case "swift":
            return """
            // Generated Swift code
            // Request: \(description)
            // Generated: \(timestamp)
            
            import Foundation
            
            struct Solution {
                static func execute() -> String {
                    let result = "Solution for: \(description)"
                    print(result)
                    return result
                }
                
                // Helper methods
                private func validateInput() -> Bool {
                    return true
                }
            }
            
            // Usage
            let output = Solution.execute()
            print("Execution complete: \\(output)")
            """
            
        case "python":
            return """
            # Generated Python code
            # Request: \(description)
            # Generated: \(timestamp)
            
            def main():
                \"\"\"Main function to handle: \(description)\"\"\"
                result = f"Solution for: {description}"
                print(result)
                return result
            
            def validate_input():
                \"\"\"Validate input parameters\"\"\"
                return True
            
            if __name__ == "__main__":
                if validate_input():
                    output = main()
                    print(f"Execution complete: {output}")
                else:
                    print("Input validation failed")
            """
            
        case "javascript":
            return """
            // Generated JavaScript code
            // Request: \(description)
            // Generated: \(timestamp)
            
            class Solution {
                constructor() {
                    this.description = "\(description)";
                }
                
                execute() {
                    const result = `Solution for: ${this.description}`;
                    console.log(result);
                    return result;
                }
                
                validateInput() {
                    return true;
                }
            }
            
            // Usage
            const solver = new Solution();
            if (solver.validateInput()) {
                const output = solver.execute();
                console.log(`Execution complete: ${output}`);
            }
            """
            
        default:
            return "// Code generation for \(language)\n// Description: \(description)\n// Generated: \(timestamp)"
        }
    }
}