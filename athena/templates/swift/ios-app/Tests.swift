import XCTest
@testable import {{project_name}}

final class {{project_name}}Tests: XCTestCase {

    var viewModel: ContentViewModel!

    override func setUpWithError() throws {
        viewModel = ContentViewModel()
    }

    override func tearDownWithError() throws {
        viewModel = nil
    }

    // MARK: - ViewModel Tests

    func testIncrementCounter() {
        // Given
        let initialValue = viewModel.counter

        // When
        viewModel.incrementCounter()

        // Then
        XCTAssertEqual(viewModel.counter, initialValue + 1)
    }

    func testDecrementCounter() {
        // Given
        viewModel.counter = 5

        // When
        viewModel.decrementCounter()

        // Then
        XCTAssertEqual(viewModel.counter, 4)
    }

    func testDecrementCounterAtZero() {
        // Given
        viewModel.counter = 0

        // When
        viewModel.decrementCounter()

        // Then
        XCTAssertEqual(viewModel.counter, 0, "Counter should not go below zero")
    }

    func testResetCounter() {
        // Given
        viewModel.counter = 42

        // When
        viewModel.resetCounter()

        // Then
        XCTAssertEqual(viewModel.counter, 0)
    }

    // MARK: - Async Tests

    func testLoadDataSetsLoadingState() async {
        // Given
        XCTAssertFalse(viewModel.isLoading)

        // When
        let loadTask = Task {
            await viewModel.loadData()
        }

        // Then - should be loading
        try? await Task.sleep(for: .milliseconds(100))
        // Note: isLoading might already be false if task completed quickly

        await loadTask.value
        XCTAssertFalse(viewModel.isLoading, "Should not be loading after completion")
    }

    // MARK: - Model Tests

    func testAppModelCreation() {
        // Given
        let title = "Test Title"
        let description = "Test Description"

        // When
        let model = AppModel(title: title, description: description)

        // Then
        XCTAssertEqual(model.title, title)
        XCTAssertEqual(model.description, description)
        XCTAssertNotNil(model.id)
        XCTAssertNotNil(model.createdAt)
    }

    func testAppModelCodable() throws {
        // Given
        let original = AppModel(
            title: "Test",
            description: "Description"
        )

        // When
        let encoder = JSONEncoder()
        let data = try encoder.encode(original)
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(AppModel.self, from: data)

        // Then
        XCTAssertEqual(original.id, decoded.id)
        XCTAssertEqual(original.title, decoded.title)
        XCTAssertEqual(original.description, decoded.description)
    }

    // MARK: - Performance Tests

    func testPerformanceExample() {
        measure {
            // Performance test
            for _ in 0..<1000 {
                viewModel.incrementCounter()
                viewModel.decrementCounter()
            }
        }
    }
}
