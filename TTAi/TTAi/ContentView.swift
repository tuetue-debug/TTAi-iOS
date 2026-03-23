import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        SplashScreen()
            .preferredColorScheme(appState.isDarkMode ? .dark : .light)
    }
}