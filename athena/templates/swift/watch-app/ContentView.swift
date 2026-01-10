import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    @EnvironmentObject var connectivityService: ConnectivityService

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                // Main content
                Text("{{project_name}}")
                    .font(.headline)

                // Counter display
                Text("\(viewModel.counter)")
                    .font(.system(size: 48, weight: .bold))

                // Action buttons
                HStack(spacing: 20) {
                    Button {
                        viewModel.decrement()
                    } label: {
                        Image(systemName: "minus.circle.fill")
                            .font(.title2)
                    }
                    .buttonStyle(.plain)

                    Button {
                        viewModel.increment()
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                    .buttonStyle(.plain)
                }

                // Sync button
                Button {
                    connectivityService.sendMessage([
                        "counter": viewModel.counter
                    ])
                } label: {
                    Label("Sync", systemImage: "arrow.triangle.2.circlepath")
                }
                .buttonStyle(.borderedProminent)
                .disabled(!connectivityService.isReachable)

                // Connection status
                HStack {
                    Circle()
                        .fill(connectivityService.isReachable ? .green : .red)
                        .frame(width: 8, height: 8)
                    Text(connectivityService.isReachable ? "Connected" : "Disconnected")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Watch")
            .padding()
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(ConnectivityService())
}
