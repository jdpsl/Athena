# {{project_name}}

{{description}}

A modern Apple Watch app built with SwiftUI and watchOS best practices for 2026.

## Features

- **SwiftUI**: Modern declarative UI (WatchKit deprecated since watchOS 7)
- **Watch Connectivity**: Sync data with paired iPhone
- **Minimal UI**: Optimized for quick glances
- **Battery Efficient**: Minimal background processing
- **Complications**: Quick access to information
- **Smart Stack**: Widget support for watchOS

## Requirements

- **watchOS**: 9.0+ (recommended 10.0+)
- **iOS**: 16.0+ (for companion iPhone app)
- **Xcode**: 17.0+
- **Swift**: 6.0+
- **Apple Watch**: Series 4 or later recommended

## Installation

```bash
# Open in Xcode
open {{project_name}}.xcworkspace

# Select Watch App target
# Build and run: Cmd+R
# Choose Apple Watch simulator or connected device
```

## Project Structure

```
{{project_name}} Watch App/
├── Views/
│   ├── ContentView.swift         # Main watch face
│   └── DetailView.swift          # Detail screens
├── ViewModels/
│   └── ContentViewModel.swift    # Watch app logic
├── Models/
│   └── WatchModel.swift          # Data models
├── Services/
│   └── ConnectivityService.swift # iPhone sync
└── Resources/
    └── Assets.xcassets           # Watch-specific assets
```

## watchOS Best Practices (2026)

### 1. Keep It Simple

```swift
// Good: Simple, focused interface
VStack {
    Text("Steps")
    Text("\(steps)")
        .font(.largeTitle)
}

// Bad: Too much information
// Don't cram lots of data on watch screen
```

### 2. Quick Interactions

Users glance at Apple Watch for only a few seconds:
- Show crucial information immediately
- Minimize taps required
- Use large, touch-friendly buttons

### 3. Battery Efficiency

```swift
// Minimize background processing
// Use WorkoutSession for fitness apps
// Avoid continuous location updates
```

### 4. Use Watch Connectivity

```swift
import WatchConnectivity

// Sync with iPhone
WCSession.default.sendMessage(["key": "value"]) { response in
    // Handle response
}
```

### 5. Avoid Nested TabView

⚠️ **Critical**: Nesting TabView causes memory leaks in watchOS!

```swift
// Bad: Nested TabView
TabView {
    TabView { ... } // Memory leak!
}

// Good: Single level
TabView {
    View1()
    View2()
}
```

## Watch UI Components

### Lists

```swift
List {
    ForEach(items) { item in
        NavigationLink(destination: DetailView(item: item)) {
            Text(item.name)
        }
    }
}
```

### Buttons

```swift
Button("Action") {
    performAction()
}
.buttonStyle(.borderedProminent)
```

### Progress Indicators

```swift
ProgressView(value: progress, total: 100)
    .progressViewStyle(.circular)
```

### Digital Crown

```swift
@State private var scrollAmount = 0.0

ScrollView {
    // Content
}
.focusable()
.digitalCrownRotation($scrollAmount)
```

## Complications

Add complications for quick access:

```swift
@main
struct {{project_name}}App: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

// Add ComplicationController for complications
```

## Smart Stack Widgets

Support the Smart Stack with widgets:

```swift
import WidgetKit

struct {{project_name}}Widget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(
            kind: "{{project_name}}Widget",
            provider: Provider()
        ) { entry in
            WidgetView(entry: entry)
        }
        .configurationDisplayName("{{project_name}}")
        .description("Quick access to {{project_name}}")
    }
}
```

## Syncing with iPhone

### Send Data to iPhone

```swift
func sendToiPhone() {
    guard WCSession.default.isReachable else { return }

    let message = ["data": "value"]
    WCSession.default.sendMessage(message) { response in
        print("iPhone responded: \(response)")
    }
}
```

### Receive Data from iPhone

```swift
func session(
    _ session: WCSession,
    didReceiveMessage message: [String : Any]
) {
    DispatchQueue.main.async {
        // Update UI with data from iPhone
        self.updateUI(with: message)
    }
}
```

## Testing

### Watch Simulator

- Test on different watch sizes (38mm, 40mm, 42mm, 44mm, 45mm, 49mm)
- Test complications
- Test notifications

### Debug Tips

⚠️ **Note**: Debugging watchOS apps is relatively difficult. Crash reports are 1/10 to 1/20 of iOS logs.

```bash
# View console logs
Window → Devices and Simulators → Select Watch → Console

# Debugging
print() statements are your friend on Watch!
```

## Performance Optimization

```swift
// Use LazyVStack for lists
LazyVStack {
    ForEach(items) { item in
        ItemRow(item: item)
    }
}

// Minimize animations
.animation(.default, value: someValue)

// Avoid heavy computation
Task.detached {
    // Heavy work
}
```

## Health & Fitness Integration

```swift
import HealthKit

let healthStore = HKHealthStore()

// Request authorization
let types: Set = [
    HKQuantityType.quantityType(forIdentifier: .stepCount)!,
    HKQuantityType.quantityType(forIdentifier: .heartRate)!
]

healthStore.requestAuthorization(toShare: nil, read: types) { success, error in
    // Handle authorization
}
```

## Workout Support

```swift
import WorkoutKit

let workout = WorkoutSession()
workout.start()

// Monitor metrics
workout.observe(.heartRate) { value in
    // Update UI
}
```

## Notifications

```swift
import UserNotifications

// Request permission
UNUserNotificationCenter.current().requestAuthorization(
    options: [.alert, .sound]
) { granted, error in
    // Handle response
}

// Send local notification
let content = UNMutableNotificationContent()
content.title = "Reminder"
content.body = "Time to check {{project_name}}!"

let trigger = UNTimeIntervalNotificationTrigger(
    timeInterval: 60,
    repeats: false
)

let request = UNNotificationRequest(
    identifier: UUID().uuidString,
    content: content,
    trigger: trigger
)

UNUserNotificationCenter.current().add(request)
```

## Common Pitfalls

1. **Too much content** - Keep it minimal
2. **Nested TabView** - Causes memory leaks
3. **Heavy animations** - Drains battery
4. **Small touch targets** - Make buttons large (44pt minimum)
5. **Not testing on device** - Simulator != real watch
6. **Ignoring battery** - Watch has limited power

## Deployment

### App Store Submission

1. Archive Watch App target
2. Validate: Product → Archive → Validate
3. Upload to App Store Connect
4. Submit for review

### Requirements

- Watch app must have corresponding iOS app
- Support latest watchOS SDK
- Follow Human Interface Guidelines
- Test on multiple watch sizes

## Resources

- [Apple Developer - watchOS](https://developer.apple.com/watchos/)
- [Creating a watchOS app](https://developer.apple.com/tutorials/swiftui/creating-a-watchos-app)
- [watchOS Design Guidelines](https://developer.apple.com/design/human-interface-guidelines/watchos)
- [WatchOS with SwiftUI (Kodeco)](https://www.kodeco.com/books/watchos-with-swiftui-by-tutorials)

## Troubleshooting

### Watch Not Appearing in Xcode

1. Unpair and re-pair Watch
2. Restart Xcode
3. Reset Watch simulator

### Build Errors

- Clean build: Cmd+Shift+K
- Delete derived data
- Update Xcode to 17+

### Connectivity Issues

- Ensure both watch and phone are on same WiFi
- Check Bluetooth is enabled
- Verify WCSession is activated

## Contributing

1. Fork the repository
2. Create feature branch
3. Test on Watch simulator AND device
4. Submit pull request

## License

{{license}}

---

Built for ⌚️ Apple Watch with SwiftUI

Generated with [Athena AI](https://github.com/jdpsl/Athena)
