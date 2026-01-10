import SwiftUI
import SwiftData

@main
struct {{project_name}}App: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: [Item.self])
    }
}

// MARK: - Sample Model for SwiftData
@Model
class Item {
    var timestamp: Date
    var name: String

    init(name: String, timestamp: Date = Date()) {
        self.name = name
        self.timestamp = timestamp
    }
}
