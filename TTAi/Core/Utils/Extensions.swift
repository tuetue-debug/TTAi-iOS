//
//  Extensions.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

// MARK: - Color Extensions

extension Color {
    static let indigo = Color(red: 99/255, green: 102/255, blue: 241/255)
    static let emerald = Color(red: 16/255, green: 185/255, blue: 129/255)
}

// MARK: - View Extensions

extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content
    ) -> some View {
        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
    
    func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
    
    func onTapGestureWithFeedback(action: @escaping () -> Void) -> some View {
        self.modifier(TapWithFeedbackModifier(action: action))
    }
}

struct TapWithFeedbackModifier: ViewModifier {
    let action: () -> Void
    
    func body(content: Content) -> some View {
        content
            .onTapGesture {
                let generator = UIImpactFeedbackGenerator(style: .light)
                generator.impactOccurred()
                action()
            }
    }
}

// MARK: - Date Extensions

extension Date {
    func formattedRelative() -> String {
        let calendar = Calendar.current
        let now = Date()
        
        if calendar.isDateInToday(self) {
            return "Today"
        } else if calendar.isDateInYesterday(self) {
            return "Yesterday"
        } else if let days = calendar.dateComponents([.day], from: self, to: now).day, days < 7 {
            let formatter = DateFormatter()
            formatter.dateFormat = "EEEE"
            return formatter.string(from: self)
        } else {
            let formatter = DateFormatter()
            formatter.dateStyle = .medium
            return formatter.string(from: self)
        }
    }
}

// MARK: - String Extensions

extension String {
    var isNotEmpty: Bool {
        !isEmpty
    }
    
    func truncate(to length: Int, trailing: String = "...") -> String {
        if count > length {
            return prefix(length) + trailing
        }
        return self
    }
    
    func containsCaseInsensitive(_ other: String) -> Bool {
        range(of: other, options: .caseInsensitive) != nil
    }
}

// MARK: - Array Extensions

extension Array where Element: Identifiable {
    func chunked(into size: Int) -> [[Element]] {
        stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
}

// MARK: - Optional Extensions

extension Optional where Wrapped == String {
    var orEmpty: String {
        self ?? ""
    }
    
    var isNilOrEmpty: Bool {
        self?.isEmpty ?? true
    }
}