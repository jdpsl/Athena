import Foundation

// MARK: - Data Models

struct AppModel: Codable, Identifiable {
    let id: UUID
    var title: String
    var description: String
    var createdAt: Date

    init(
        id: UUID = UUID(),
        title: String,
        description: String,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.createdAt = createdAt
    }
}

// MARK: - API Response Models

struct APIResponse<T: Codable>: Codable {
    let data: T
    let message: String?
    let status: Int
}

// MARK: - Error Types

enum AppError: Error, LocalizedError {
    case networkError(String)
    case decodingError(String)
    case unknown

    var errorDescription: String? {
        switch self {
        case .networkError(let message):
            return "Network error: \(message)"
        case .decodingError(let message):
            return "Decoding error: \(message)"
        case .unknown:
            return "An unknown error occurred"
        }
    }
}
