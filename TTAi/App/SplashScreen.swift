import SwiftUI

struct SplashScreen: View {
    var body: some View {
        VStack {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            Text("TTAi")
                .font(.largeTitle)
                .fontWeight(.bold)
            Text("Tuệ Tuệ AI Assistant")
                .font(.title2)
                .foregroundColor(.gray)
        }
        .padding()
    }
}