import Foundation
import Observation

@Observable
class ContentViewModel {
    var counter: Int = 0

    func increment() {
        counter += 1
    }

    func decrement() {
        counter = max(0, counter - 1)
    }

    func reset() {
        counter = 0
    }
}
