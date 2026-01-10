import Foundation

actor DataService {
    static let shared = DataService()

    private init() {}

    // MARK: - API Configuration

    private let baseURL = "https://api.example.com"
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    // MARK: - Network Requests

    func fetchData<T: Decodable>(
        from endpoint: String,
        type: T.Type
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)/\(endpoint)") else {
            throw AppError.networkError("Invalid URL")
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AppError.networkError("Invalid response")
        }

        do {
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
        } catch {
            throw AppError.decodingError(error.localizedDescription)
        }
    }

    func postData<T: Encodable>(
        to endpoint: String,
        body: T
    ) async throws {
        guard let url = URL(string: "\(baseURL)/\(endpoint)") else {
            throw AppError.networkError("Invalid URL")
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        request.httpBody = try encoder.encode(body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AppError.networkError("POST request failed")
        }
    }
}

// MARK: - Local Data Persistence

extension DataService {
    func saveToUserDefaults<T: Codable>(_ value: T, forKey key: String) throws {
        let encoder = JSONEncoder()
        let data = try encoder.encode(value)
        UserDefaults.standard.set(data, forKey: key)
    }

    func loadFromUserDefaults<T: Codable>(forKey key: String, type: T.Type) throws -> T? {
        guard let data = UserDefaults.standard.data(forKey: key) else {
            return nil
        }
        let decoder = JSONDecoder()
        return try decoder.decode(T.self, from: data)
    }
}
