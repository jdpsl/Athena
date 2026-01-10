import Foundation
import WatchConnectivity
import Observation

@Observable
class ConnectivityService: NSObject {
    var isReachable: Bool = false
    var lastMessage: [String: Any]?

    override init() {
        super.init()
        setupWatchConnectivity()
    }

    private func setupWatchConnectivity() {
        guard WCSession.isSupported() else {
            print("Watch Connectivity not supported")
            return
        }

        let session = WCSession.default
        session.delegate = self
        session.activate()
    }

    func sendMessage(_ message: [String: Any]) {
        guard WCSession.default.isReachable else {
            print("iPhone not reachable")
            return
        }

        WCSession.default.sendMessage(message) { response in
            print("Received response from iPhone: \(response)")
            DispatchQueue.main.async {
                self.lastMessage = response
            }
        } errorHandler: { error in
            print("Error sending message: \(error.localizedDescription)")
        }
    }

    func updateApplicationContext(_ context: [String: Any]) {
        do {
            try WCSession.default.updateApplicationContext(context)
            print("Application context updated")
        } catch {
            print("Error updating context: \(error.localizedDescription)")
        }
    }
}

// MARK: - WCSessionDelegate

extension ConnectivityService: WCSessionDelegate {
    func session(
        _ session: WCSession,
        activationDidCompleteWith activationState: WCSessionActivationState,
        error: Error?
    ) {
        DispatchQueue.main.async {
            self.isReachable = session.isReachable
        }

        if let error = error {
            print("Session activation failed: \(error.localizedDescription)")
        } else {
            print("Session activated: \(activationState.rawValue)")
        }
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        DispatchQueue.main.async {
            self.isReachable = session.isReachable
        }
        print("Reachability changed: \(session.isReachable)")
    }

    func session(
        _ session: WCSession,
        didReceiveMessage message: [String : Any]
    ) {
        DispatchQueue.main.async {
            self.lastMessage = message
            print("Received message: \(message)")
        }
    }

    func session(
        _ session: WCSession,
        didReceiveApplicationContext applicationContext: [String : Any]
    ) {
        DispatchQueue.main.async {
            self.lastMessage = applicationContext
            print("Received application context: \(applicationContext)")
        }
    }
}
