import Foundation
import Observation

@Observable
class ContentViewModel {
    var counter: Int = 0
    var isLoading: Bool = false
    var errorMessage: String?

    // MARK: - Counter Actions

    func incrementCounter() {
        counter += 1
    }

    func decrementCounter() {
        counter = max(0, counter - 1)
    }

    func resetCounter() {
        counter = 0
    }

    // MARK: - Data Loading Example

    func loadData() async {
        isLoading = true
        errorMessage = nil

        do {
            // Simulate API call
            try await Task.sleep(for: .seconds(1))

            // Process data here
            isLoading = false
        } catch {
            errorMessage = "Failed to load data: \(error.localizedDescription)"
            isLoading = false
        }
    }
}
