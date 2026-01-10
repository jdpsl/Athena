import SwiftUI

@main
struct {{project_name}}App: App {
    @StateObject private var connectivityService = ConnectivityService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(connectivityService)
        }
    }
}
