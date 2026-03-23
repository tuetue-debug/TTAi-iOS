//
//  HistoryView.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""
    @State private var showingClearAlert = false
    
    var filteredHistory: [ChatMessage] {
        if searchText.isEmpty {
            return appState.chatHistory
        } else {
            return appState.chatHistory.filter { message in
                message.content.localizedCaseInsensitiveContains(searchText)
            }
        }
    }
    
    var groupedHistory: [String: [ChatMessage]] {
        let grouped = Dictionary(grouping: filteredHistory) { message in
            let calendar = Calendar.current
            if calendar.isDateInToday(message.timestamp) {
                return "Today"
            } else if calendar.isDateInYesterday(message.timestamp) {
                return "Yesterday"
            } else {
                let formatter = DateFormatter()
                formatter.dateStyle = .medium
                return formatter.string(from: message.timestamp)
            }
        }
        
        return grouped
    }
    
    var sortedDates: [String] {
        groupedHistory.keys.sorted { date1, date2 in
            let dateOrder = ["Today", "Yesterday"]
            if let index1 = dateOrder.firstIndex(of: date1),
               let index2 = dateOrder.firstIndex(of: date2) {
                return index1 < index2
            }
            
            if dateOrder.contains(date1) { return true }
            if dateOrder.contains(date2) { return false }
            
            return date1 > date2
        }
    }
    
    var body: some View {
        NavigationStack {
            if appState.chatHistory.isEmpty {
                emptyStateView
            } else {
                historyListView
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No History Yet")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Your chat history will appear here after you start conversations with Tuệ Tuệ AI.")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .padding(.horizontal, 40)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .navigationTitle("History")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                clearHistoryButton
            }
        }
    }
    
    private var historyListView: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 24) {
                // Search bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.secondary)
                    
                    TextField("Search history...", text: $searchText)
                        .textFieldStyle(.plain)
                    
                    if !searchText.isEmpty {
                        Button(action: { searchText = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding(12)
                .background(Color(.systemGray6))
                .cornerRadius(10)
                .padding(.horizontal)
                
                // History groups
                ForEach(sortedDates, id: \.self) { date in
                    if let messages = groupedHistory[date] {
                        HistoryGroupView(date: date, messages: messages)
                    }
                }
            }
            .padding(.vertical)
        }
        .navigationTitle("History")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                clearHistoryButton
            }
        }
        .alert("Clear History", isPresented: $showingClearAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Clear", role: .destructive) {
                appState.chatHistory.removeAll()
            }
        } message: {
            Text("Are you sure you want to clear all chat history? This action cannot be undone.")
        }
    }
    
    private var clearHistoryButton: some View {
        Button(action: { showingClearAlert = true }) {
            Text("Clear")
                .foregroundColor(.red)
        }
        .disabled(appState.chatHistory.isEmpty)
    }
}

// MARK: - History Group View

struct HistoryGroupView: View {
    let date: String
    let messages: [ChatMessage]
    @State private var isExpanded = true
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Text(date)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text("\(messages.count) conversation\(messages.count == 1 ? "" : "s")")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal)
            
            // Messages
            if isExpanded {
                VStack(spacing: 8) {
                    ForEach(messages.prefix(5)) { message in
                        HistoryItemView(message: message)
                    }
                    
                    if messages.count > 5 {
                        Text("+ \(messages.count - 5) more conversation\(messages.count - 5 == 1 ? "" : "s")")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, alignment: .center)
                            .padding(.top, 4)
                    }
                }
                .padding(.horizontal)
            }
        }
    }
}

// MARK: - History Item View

struct HistoryItemView: View {
    let message: ChatMessage
    @State private var isPressed = false
    
    var body: some View {
        Button(action: {}) {
            HStack(alignment: .top, spacing: 12) {
                // Icon
                ZStack {
                    Circle()
                        .fill(iconBackgroundColor)
                        .frame(width: 40, height: 40)
                    
                    Image(systemName: iconName)
                        .font(.system(size: 18))
                        .foregroundColor(iconForegroundColor)
                }
                
                // Content
                VStack(alignment: .leading, spacing: 4) {
                    Text(message.content)
                        .font(.body)
                        .foregroundColor(.primary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                    
                    HStack {
                        Text(message.timestamp, style: .time)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        
                        if let model = message.model {
                            Text("•")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                            
                            Text(model.displayName)
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(12)
            .background(isPressed ? Color(.systemGray5) : Color(.systemGray6))
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
    
    private var iconName: String {
        switch message.role {
        case .user: return "person.fill"
        case .assistant: return "sparkles"
        case .system: return "gear"
        }
    }
    
    private var iconBackgroundColor: Color {
        switch message.role {
        case .user: return .blue.opacity(0.2)
        case .assistant: return .indigo.opacity(0.2)
        case .system: return .gray.opacity(0.2)
        }
    }
    
    private var iconForegroundColor: Color {
        switch message.role {
        case .user: return .blue
        case .assistant: return .indigo
        case .system: return .gray
        }
    }
}

// MARK: - Preview

#Preview {
    HistoryView()
        .environmentObject({
            let state = AppState()
            state.chatHistory = [
                ChatMessage(role: .user, content: "How to make a network call in Swift?", timestamp: Date()),
                ChatMessage(role: .assistant, content: "Use URLSession with async/await...", model: .gptMini, timestamp: Date()),
                ChatMessage(role: .user, content: "Explain Combine publishers", timestamp: Date().addingTimeInterval(-86400)),
                ChatMessage(role: .assistant, content: "Combine is a reactive framework...", model: .geminiPro, timestamp: Date().addingTimeInterval(-86400)),
            ]
            return state
        }())
}