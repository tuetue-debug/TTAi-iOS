//
//  CodeGeneratorView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct CodeGeneratorView: View {
    @State private var selectedLanguage: ProgrammingLanguage = .swift
    @State private var description = "Create a login screen with email and password fields, and a submit button."
    @State private var generatedCode = ""
    @State private var isGenerating = false
    @State private var showExplanation = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Language picker
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Language")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Picker("Language", selection: $selectedLanguage) {
                            ForEach(ProgrammingLanguage.allCases) { language in
                                Text(language.displayName).tag(language)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                    .padding(.horizontal)
                    
                    // Description input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Describe what you want to build")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        TextEditor(text: $description)
                            .frame(minHeight: 120)
                            .padding(12)
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                            .font(.body)
                    }
                    .padding(.horizontal)
                    
                    // Generate button
                    Button(action: generateCode) {
                        if isGenerating {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Label("Generate Code", systemImage: "sparkles")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(description.isEmpty || isGenerating)
                    
                    // Generated code
                    if !generatedCode.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("Generated Code")
                                    .font(.headline)
                                
                                Spacer()
                                
                                Button(action: copyCode) {
                                    Label("Copy", systemImage: "doc.on.doc")
                                        .font(.caption)
                                }
                                .buttonStyle(.bordered)
                            }
                            
                            CodeBlockView(code: generatedCode, language: selectedLanguage)
                                .frame(maxHeight: 300)
                            
                            HStack(spacing: 12) {
                                Button(action: runTests) {
                                    Label("Run Tests", systemImage: "play.fill")
                                        .frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.bordered)
                                
                                Button(action: { showExplanation = true }) {
                                    Label("Explain", systemImage: "questionmark.circle")
                                        .frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(16)
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Code Generator")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: refresh) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .sheet(isPresented: $showExplanation) {
                CodeExplanationView(code: generatedCode, language: selectedLanguage)
            }
        }
    }
    
    private func generateCode() {
        isGenerating = true
        
        // Simulate API call
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            generatedCode = sampleCode(for: selectedLanguage)
            isGenerating = false
        }
    }
    
    private func copyCode() {
        UIPasteboard.general.string = generatedCode
    }
    
    private func runTests() {
        // Simulate test run
        print("Running tests for \(selectedLanguage.displayName) code...")
    }
    
    private func refresh() {
        description = ""
        generatedCode = ""
    }
    
    private func sampleCode(for language: ProgrammingLanguage) -> String {
        switch language {
        case .swift:
            return """
            import SwiftUI
            
            struct LoginView: View {
                @State private var email = ""
                @State private var password = ""
                @State private var isLoggedIn = false
                
                var body: some View {
                    VStack(spacing: 20) {
                        Text("Welcome")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        TextField("Email", text: $email)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                            .keyboardType(.emailAddress)
                        
                        SecureField("Password", text: $password)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                        
                        Button("Sign In") {
                            // Authentication logic
                            isLoggedIn = true
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(email.isEmpty || password.isEmpty)
                        
                        Spacer()
                    }
                    .padding()
                }
            }
            """
        case .python:
            return """
            def login(email, password):
                # Simple login validation
                valid_email = "user@example.com"
                valid_password = "password123"
                
                if email == valid_email and password == valid_password:
                    return True
                return False
            
            if __name__ == "__main__":
                email = input("Enter email: ")
                password = input("Enter password: ")
                
                if login(email, password):
                    print("Login successful!")
                else:
                    print("Invalid credentials")
            """
        case .javascript:
            return """
            class LoginForm {
                constructor() {
                    this.email = '';
                    this.password = '';
                    this.isLoggedIn = false;
                }
                
                validateEmail(email) {
                    const re = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
                    return re.test(email);
                }
                
                login() {
                    if (this.validateEmail(this.email) && this.password.length >= 6) {
                        this.isLoggedIn = true;
                        console.log('Login successful');
                        return true;
                    }
                    console.log('Invalid credentials');
                    return false;
                }
            }
            
            // Usage
            const form = new LoginForm();
            form.email = 'user@example.com';
            form.password = 'password123';
            form.login();
            """
        }
    }
}

// MARK: - Programming Language

enum ProgrammingLanguage: String, CaseIterable, Identifiable {
    case swift
    case python
    case javascript
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .swift: return "Swift"
        case .python: return "Python"
        case .javascript: return "JavaScript"
        }
    }
    
    var fileExtension: String {
        switch self {
        case .swift: return "swift"
        case .python: return "py"
        case .javascript: return "js"
        }
    }
}

// MARK: - Code Block View

struct CodeBlockView: View {
    let code: String
    let language: ProgrammingLanguage
    
    var body: some View {
        ScrollView(.horizontal) {
            Text(code)
                .font(.system(.body, design: .monospaced))
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(Color.black)
        .foregroundColor(.white)
        .cornerRadius(12)
    }
}

// MARK: - Code Explanation View

struct CodeExplanationView: View {
    let code: String
    let language: ProgrammingLanguage
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Code Explanation")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("This \(language.displayName) code demonstrates:")
                        .font(.headline)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        explanationPoints
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    Text("Key Concepts:")
                        .font(.headline)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(keyConcepts, id: \.self) { concept in
                            HStack(alignment: .top) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                Text(concept)
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                }
                .padding()
            }
            .navigationTitle("Explain Code")
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
    
    private var explanationPoints: some View {
        Group {
            switch language {
            case .swift:
                VStack(alignment: .leading, spacing: 8) {
                    Text("• SwiftUI declarative UI with @State properties")
                    Text("• TextField and SecureField for user input")
                    Text("• Button with prominent style and validation")
                    Text("• Responsive layout with VStack and padding")
                }
            case .python:
                VStack(alignment: .leading, spacing: 8) {
                    Text("• Function definition with parameters")
                    Text("• Conditional logic for validation")
                    Text("• Main guard for script execution")
                    Text("• User input with input() function")
                }
            case .javascript:
                VStack(alignment: .leading, spacing: 8) {
                    Text("• ES6 class with constructor")
                    Text("• Regular expression for email validation")
                    Text("• Method for login logic")
                    Text("• Console logging for debugging")
                }
            }
        }
    }
    
    private var keyConcepts: [String] {
        switch language {
        case .swift:
            return ["SwiftUI", "@State property wrapper", "View protocol", "Modifiers"]
        case .python:
            return ["Functions", "Conditionals", "String comparison", "Input/Output"]
        case .javascript:
            return ["Classes", "Regular expressions", "Console API", "DOM manipulation"]
        }
    }
}

#Preview {
    CodeGeneratorView()
}