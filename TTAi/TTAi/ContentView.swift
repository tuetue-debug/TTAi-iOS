import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack(spacing: 16) {
            Text("TTAi")
                .font(.largeTitle)
                .bold()
            Text("Placeholder UI — update with real content soon.")
                .font(.body)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
        .background(Color(uiColor: .systemBackground))
    }
}

#Preview {
    ContentView()
}
