# {{project_name}}

Modern Android app built with Kotlin, Jetpack Compose, and Material 3 for 2026.

## Features

- **Jetpack Compose**: Declarative UI with Material 3 design
- **MVVM Architecture**: Clean separation of concerns with ViewModel
- **Kotlin Coroutines**: Modern asynchronous programming
- **Material 3**: Latest Material Design components with dynamic theming
- **Type-Safe Navigation**: Compose navigation with type safety
- **State Management**: Modern state hoisting patterns
- **Dependency Injection**: Ready for Hilt/Koin integration

## Tech Stack

- **Language**: Kotlin 2.0+
- **UI Framework**: Jetpack Compose
- **Architecture**: MVVM (Model-View-ViewModel)
- **Minimum SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)
- **Build System**: Gradle with Kotlin DSL

## Project Structure

```
app/
├── src/
│   ├── main/
│   │   ├── java/com/{{project_name_snake}}/
│   │   │   ├── MainActivity.kt           # Main entry point
│   │   │   ├── ui/
│   │   │   │   ├── MainScreen.kt         # Main composable screen
│   │   │   │   └── theme/
│   │   │   │       ├── Theme.kt          # App theme definition
│   │   │   │       └── Color.kt          # Color palette
│   │   │   ├── viewmodel/
│   │   │   │   └── MainViewModel.kt      # ViewModel for business logic
│   │   │   ├── model/
│   │   │   │   └── AppModel.kt           # Data models
│   │   │   └── data/                     # Data layer (repositories, etc.)
│   │   ├── res/
│   │   │   └── values/
│   │   │       └── strings.xml           # String resources
│   │   └── AndroidManifest.xml
│   ├── test/                             # Unit tests
│   └── androidTest/                      # Instrumentation tests
└── build.gradle.kts
```

## Getting Started

### Prerequisites

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17 or higher
- Android SDK with API level 34

### Setup

1. **Open in Android Studio**:
   ```bash
   cd {{project_name}}
   # Then: File → Open → Select project folder
   ```

2. **Sync Gradle**:
   - Android Studio will prompt to sync
   - Or: File → Sync Project with Gradle Files

3. **Run the app**:
   - Click Run button (▶) or press Shift+F10
   - Select an emulator or connected device

### Build Variants

- **Debug**: For development with debugging enabled
- **Release**: Optimized production build

```bash
# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Run tests
./gradlew test

# Run instrumentation tests
./gradlew connectedAndroidTest
```

## Architecture

### MVVM Pattern

```
┌─────────────┐      ┌──────────────┐      ┌─────────┐
│   View      │─────▶│  ViewModel   │─────▶│  Model  │
│ (Compose UI)│◀─────│ (State Logic)│◀─────│ (Data)  │
└─────────────┘      └──────────────┘      └─────────┘
```

- **View (Composables)**: UI layer, observes ViewModel state
- **ViewModel**: Business logic, manages UI state
- **Model**: Data models and repositories

### State Management

```kotlin
// ViewModel exposes state
class MainViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
}

// Composable observes state
@Composable
fun MainScreen(viewModel: MainViewModel) {
    val uiState by viewModel.uiState.collectAsState()
    // UI reacts to state changes
}
```

## Material 3 Design

### Dynamic Theming

The app supports Material 3 dynamic color theming:

```kotlin
{{project_name}}Theme(
    darkTheme = isSystemInDarkTheme(),
    dynamicColor = true  // Adapts to system wallpaper colors
) {
    // Your content
}
```

### Components Used

- **Scaffold**: App structure with top bar, bottom bar, FAB
- **TopAppBar**: Material 3 app bar with scroll behavior
- **Card**: Material 3 elevated/filled cards
- **Button**: Filled, outlined, and text buttons
- **TextField**: Material 3 text input

## Common Tasks

### Adding a New Screen

1. Create composable in `ui/` package:
```kotlin
@Composable
fun NewScreen(
    onNavigateBack: () -> Unit,
    viewModel: NewViewModel = viewModel()
) {
    // Screen content
}
```

2. Add navigation route:
```kotlin
NavHost(navController, startDestination = "main") {
    composable("main") { MainScreen() }
    composable("new") { NewScreen() }
}
```

### Adding Dependencies

Edit `app/build.gradle.kts`:

```kotlin
dependencies {
    // Example: Add Room database
    implementation("androidx.room:room-runtime:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
}
```

### Network Calls

Add Retrofit and OkHttp:

```kotlin
dependencies {
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
}
```

Example repository:

```kotlin
interface ApiService {
    @GET("users")
    suspend fun getUsers(): List<User>
}

class UserRepository(private val api: ApiService) {
    suspend fun fetchUsers(): Result<List<User>> = try {
        Result.success(api.getUsers())
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```

### Dependency Injection with Hilt

1. Add Hilt dependencies:
```kotlin
plugins {
    id("com.google.dagger.hilt.android")
}

dependencies {
    implementation("com.google.dagger:hilt-android:2.50")
    ksp("com.google.dagger:hilt-compiler:2.50")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
}
```

2. Annotate Application:
```kotlin
@HiltAndroidApp
class {{project_name}}Application : Application()
```

3. Inject ViewModels:
```kotlin
@HiltViewModel
class MainViewModel @Inject constructor(
    private val repository: Repository
) : ViewModel()
```

## Testing

### Unit Tests

Located in `src/test/`:

```kotlin
class MainViewModelTest {
    private lateinit var viewModel: MainViewModel

    @Before
    fun setup() {
        viewModel = MainViewModel()
    }

    @Test
    fun `increment increases counter`() {
        val initial = viewModel.uiState.value.counter
        viewModel.increment()
        assertEquals(initial + 1, viewModel.uiState.value.counter)
    }
}
```

### UI Tests

Located in `src/androidTest/`:

```kotlin
@get:Rule
val composeTestRule = createComposeRule()

@Test
fun mainScreen_displaysCounter() {
    composeTestRule.setContent {
        MainScreen()
    }
    composeTestRule.onNodeWithText("Counter: 0").assertExists()
}
```

## Performance Tips

### Compose Best Practices

1. **Avoid unnecessary recompositions**:
```kotlin
// Use remember to cache expensive calculations
val expensiveValue = remember(key) {
    expensiveCalculation()
}
```

2. **Use derivedStateOf for computed state**:
```kotlin
val filteredList by remember {
    derivedStateOf {
        list.filter { it.isActive }
    }
}
```

3. **Prefer immutable state**:
```kotlin
// Good: Immutable state
data class UiState(val counter: Int = 0)

// Avoid: Mutable properties
var counter = 0
```

### Memory Management

- Use `viewModelScope` for coroutines tied to ViewModel lifecycle
- Cancel background work when ViewModel is cleared
- Use `LazyColumn` for long lists instead of `Column`
- Load images with Coil or Glide for efficient caching

## Debugging

### Compose Layout Inspector

1. Run app on emulator/device
2. Tools → Layout Inspector
3. Select your app process
4. View composition tree and recomposition counts

### Logcat Filtering

```bash
# Filter by tag
adb logcat -s {{project_name}}

# Filter by package
adb logcat --pid=$(adb shell pidof -s com.{{project_name_snake}})
```

### Debug Compose Recompositions

```kotlin
@Composable
fun DebugComposable() {
    Log.d("Compose", "Recomposing DebugComposable")
    // Your content
}
```

## Deployment

### Generate Signed APK/Bundle

1. **Create keystore**:
```bash
keytool -genkey -v -keystore release-key.jks -keyalg RSA \
  -keysize 2048 -validity 10000 -alias release
```

2. **Configure signing in `app/build.gradle.kts`**:
```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("../release-key.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = "release"
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

3. **Build release bundle**:
```bash
./gradlew bundleRelease
```

Output: `app/build/outputs/bundle/release/app-release.aab`

### ProGuard/R8

For release builds, code shrinking and obfuscation are enabled:

```kotlin
buildTypes {
    release {
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),
            "proguard-rules.pro"
        )
    }
}
```

## Resources

### Documentation

- [Jetpack Compose](https://developer.android.com/jetpack/compose)
- [Material 3](https://m3.material.io/)
- [Android Developers](https://developer.android.com)
- [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)

### Libraries

- [Accompanist](https://google.github.io/accompanist/): Compose utilities
- [Coil](https://coil-kt.github.io/coil/): Image loading
- [Retrofit](https://square.github.io/retrofit/): Networking
- [Room](https://developer.android.com/training/data-storage/room): Database
- [Hilt](https://dagger.dev/hilt/): Dependency injection

## License

{{license}}

---

Generated with [Athena AI](https://github.com/jdpsl/Athena)
