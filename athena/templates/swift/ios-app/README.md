# {{project_name}}

{{description}}

A modern iOS app built with Swift 6, SwiftUI, and iOS 26 best practices.

## Features

- **Swift 6**: Latest language features with improved macros and type-checking
- **SwiftUI**: Declarative UI framework (UIKit legacy support available)
- **MVVM Architecture**: Clean separation of concerns
- **SwiftData**: Modern data persistence
- **iOS 26 SDK**: Ready for App Store submission (required April 2026)
- **Liquid Glass Design**: Modern translucent UI patterns
- **On-Device AI**: Foundation Models framework support
- **Unit & UI Tests**: Comprehensive test coverage

## Requirements

- **iOS**: 16.0+ (recommended 26.0+)
- **Xcode**: 17.0+
- **Swift**: 6.0+
- **macOS**: Latest version for Xcode 17

## Installation

```bash
# Clone or create the project
cd {{project_name}}

# Open in Xcode
open {{project_name}}.xcodeproj

# Configure signing in Xcode:
# 1. Select project in navigator
# 2. Select target
# 3. Go to "Signing & Capabilities"
# 4. Select your team
```

## Project Structure

```
{{project_name}}/
├── App/
│   └── {{project_name}}App.swift    # App entry point
├── Views/
│   └── ContentView.swift             # Main UI views
├── ViewModels/
│   └── ContentViewModel.swift        # View models (MVVM)
├── Models/
│   └── AppModel.swift                # Data models
├── Services/
│   └── DataService.swift             # Business logic
└── Resources/
    ├── Assets.xcassets               # Images, colors, etc.
    └── Info.plist                    # App configuration
```

## Architecture

This app follows **MVVM (Model-View-ViewModel)** pattern:

- **Models**: Data structures and business entities
- **Views**: SwiftUI views (declarative UI)
- **ViewModels**: Presentation logic and state management
- **Services**: API calls, data persistence, etc.

## Development

### Building

```bash
# Build for simulator (Cmd+B in Xcode)
xcodebuild -scheme {{project_name}} -sdk iphonesimulator

# Build for device
xcodebuild -scheme {{project_name}} -sdk iphoneos
```

### Running

1. Open project in Xcode
2. Select target device/simulator
3. Press **Cmd+R** to build and run

### Testing

```bash
# Run tests in Xcode (Cmd+U)
xcodebuild test -scheme {{project_name}} -destination 'platform=iOS Simulator,name=iPhone 15'

# Run specific test
xcodebuild test -scheme {{project_name}} -only-testing:{{project_name}}Tests/ContentViewModelTests
```

## SwiftUI Best Practices (2026)

### 1. Use @State and @ObservableObject

```swift
@State private var count = 0
@StateObject private var viewModel = ContentViewModel()
```

### 2. Embrace Liquid Glass Design

```swift
.background(.ultraThinMaterial)
.glassBackgroundEffect()
```

### 3. Leverage SwiftData

```swift
@Model
class Item {
    var name: String
    var timestamp: Date
}
```

### 4. Use Swift 6 Macros

```swift
@Observable
class ViewModel {
    var items: [Item] = []
}
```

### 5. On-Device AI

```swift
import FoundationModels

let model = FoundationModel()
let result = await model.predict(input)
```

## Common SwiftUI Components

### Lists

```swift
List(items) { item in
    Text(item.name)
}
```

### Navigation

```swift
NavigationStack {
    ContentView()
        .navigationTitle("{{project_name}}")
}
```

### Forms

```swift
Form {
    Section("Settings") {
        Toggle("Enable notifications", isOn: $isEnabled)
    }
}
```

## Data Persistence

### Using SwiftData (Recommended)

```swift
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
```

### Using UserDefaults (Simple Data)

```swift
UserDefaults.standard.set("value", forKey: "key")
let value = UserDefaults.standard.string(forKey: "key")
```

## Deployment

### App Store Submission

1. **Archive the app**: Product → Archive (Cmd+Shift+B)
2. **Upload to App Store Connect**
3. **Important**: Must use iOS 26 SDK after April 2026

### TestFlight

1. Archive and distribute to TestFlight
2. Invite internal/external testers
3. Gather feedback before production release

## Performance Tips

- Use `LazyVStack`/`LazyHStack` for long lists
- Avoid heavy computation in view body
- Use `@ViewBuilder` for complex views
- Profile with Instruments (Cmd+I)
- Leverage Xcode 17's 35% faster compilation

## Accessibility

```swift
Text("Welcome")
    .accessibilityLabel("Welcome message")
    .accessibilityHint("Tap to continue")
```

## Testing

### Unit Tests

```swift
func testViewModel() async {
    let viewModel = ContentViewModel()
    await viewModel.loadData()
    XCTAssertEqual(viewModel.items.count, 5)
}
```

### UI Tests

```swift
func testLaunchPerformance() {
    measure(metrics: [XCTApplicationLaunchMetric()]) {
        XCUIApplication().launch()
    }
}
```

## Troubleshooting

### Build Errors

- Clean build folder: Cmd+Shift+K
- Delete derived data: ~/Library/Developer/Xcode/DerivedData
- Update Xcode to version 17+

### Simulator Issues

- Reset simulator: Device → Erase All Content and Settings
- Restart Xcode and simulator

### Signing Issues

- Ensure valid Apple Developer account
- Check bundle identifier is unique
- Verify provisioning profiles

## Resources

- [Swift.org - SwiftUI](https://www.swift.org/getting-started/swiftui/)
- [Apple Developer - SwiftUI](https://developer.apple.com/tutorials/swiftui)
- [iOS 26 Developer Guide](https://www.index.dev/blog/ios-26-developer-guide)
- [Stanford CS193p](https://cs193p.stanford.edu/)
- [Hacking with Swift](https://www.hackingwithswift.com/)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

{{license}}

---

Built with ❤️ using Swift 6 & SwiftUI

Generated with [Athena AI](https://github.com/jdpsl/Athena)
