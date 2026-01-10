import Foundation

struct WatchItem: Identifiable, Codable {
    let id: UUID
    var title: String
    var description: String
    var timestamp: Date

    init(
        id: UUID = UUID(),
        title: String,
        description: String,
        timestamp: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.timestamp = timestamp
    }
}
