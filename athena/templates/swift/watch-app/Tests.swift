import XCTest
@testable import {{project_name}}_Watch_App

final class {{project_name}}Tests: XCTestCase {

    var viewModel: ContentViewModel!

    override func setUpWithError() throws {
        viewModel = ContentViewModel()
    }

    override func tearDownWithError() throws {
        viewModel = nil
    }

    func testIncrement() {
        // Given
        let initial = viewModel.counter

        // When
        viewModel.increment()

        // Then
        XCTAssertEqual(viewModel.counter, initial + 1)
    }

    func testDecrement() {
        // Given
        viewModel.counter = 5

        // When
        viewModel.decrement()

        // Then
        XCTAssertEqual(viewModel.counter, 4)
    }

    func testDecrementAtZero() {
        // Given
        viewModel.counter = 0

        // When
        viewModel.decrement()

        // Then
        XCTAssertEqual(viewModel.counter, 0)
    }

    func testReset() {
        // Given
        viewModel.counter = 42

        // When
        viewModel.reset()

        // Then
        XCTAssertEqual(viewModel.counter, 0)
    }
}
