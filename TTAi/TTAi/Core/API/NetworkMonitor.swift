//
//  NetworkMonitor.swift
//  TTAi
//
//  Created by Tuệ Tuệ AI on 2026-03-21.
//

import Network
import SwiftUI

class NetworkMonitor: ObservableObject {
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    
    @Published var isConnected = true
    @Published var isExpensive = false
    @Published var connectionType = NWInterface.InterfaceType.other
    
    init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
                self?.isExpensive = path.isExpensive
                self?.connectionType = self?.getConnectionType(path) ?? .other
            }
        }
        monitor.start(queue: queue)
    }
    
    deinit {
        monitor.cancel()
    }
    
    private func getConnectionType(_ path: NWPath) -> NWInterface.InterfaceType {
        if path.usesInterfaceType(.wifi) {
            return .wifi
        } else if path.usesInterfaceType(.cellular) {
            return .cellular
        } else if path.usesInterfaceType(.wiredEthernet) {
            return .wiredEthernet
        } else {
            return .other
        }
    }
}

// MARK: - Network Error View

struct NetworkErrorView: View {
    @EnvironmentObject var networkMonitor: NetworkMonitor
    
    var body: some View {
        if !networkMonitor.isConnected {
            VStack(spacing: 12) {
                Image(systemName: "wifi.slash")
                    .font(.system(size: 40))
                    .foregroundColor(.red)
                
                VStack(spacing: 4) {
                    Text("No Internet Connection")
                        .font(.headline)
                    
                    Text("Please check your network settings and try again.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                
                Button("Retry") {
                    // The network monitor will automatically update
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(Color(.systemGray6))
            .cornerRadius(12)
            .padding()
        }
    }
}

// MARK: - Network Aware View Modifier

struct NetworkAwareViewModifier: ViewModifier {
    @StateObject private var networkMonitor = NetworkMonitor()
    
    func body(content: Content) -> some View {
        content
            .environmentObject(networkMonitor)
            .overlay(alignment: .top) {
                NetworkErrorView()
                    .environmentObject(networkMonitor)
            }
    }
}

extension View {
    func networkAware() -> some View {
        modifier(NetworkAwareViewModifier())
    }
}

// MARK: - API Error Handling

enum NetworkError: Error, LocalizedError {
    case noInternetConnection
    case cellularDataWarning
    case timeout
    case serverUnreachable
    
    var errorDescription: String? {
        switch self {
        case .noInternetConnection:
            return "No internet connection. Please check your network settings."
        case .cellularDataWarning:
            return "You are using cellular data. Large responses may use significant data."
        case .timeout:
            return "The request timed out. Please try again."
        case .serverUnreachable:
            return "Unable to reach the server. Please check your API endpoint."
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .noInternetConnection:
            return "Connect to Wi-Fi or enable cellular data."
        case .cellularDataWarning:
            return "Switch to Wi-Fi for large conversations."
        case .timeout:
            return "Check your internet connection and try again."
        case .serverUnreachable:
            return "Verify your CLIProxy is running and the endpoint is correct."
        }
    }
}

// MARK: - Network Check before API Call

extension APIClient {
    func checkNetworkConditions() throws {
        // In a real app, you would check NetworkMonitor state
        // For now, we'll assume network is available
        // This would be integrated with the NetworkMonitor class
        
        // Simulated check - always passes for now
        // In production, inject NetworkMonitor dependency
    }
}