package com.{{project_name_snake}}.model

/**
 * UI state for the main screen.
 *
 * This is an immutable data class that represents the entire UI state.
 * When any property changes, a new copy is created.
 *
 * @property counter The current counter value
 * @property message The message to display to the user
 * @property isLoading Whether data is currently loading
 * @property error Error message if an error occurred
 */
data class UiState(
    val counter: Int = 0,
    val message: String = "Welcome to {{project_name}}!",
    val isLoading: Boolean = false,
    val error: String? = null
)

/**
 * Example domain model.
 *
 * Customize this for your app's data structures.
 */
data class User(
    val id: String,
    val name: String,
    val email: String
)

/**
 * Example of a result wrapper for network/database operations.
 *
 * This is a sealed interface that represents the result of an operation:
 * - Success: Operation completed successfully with data
 * - Error: Operation failed with an error message
 * - Loading: Operation is in progress
 */
sealed interface Result<out T> {
    data class Success<T>(val data: T) : Result<T>
    data class Error(val message: String) : Result<Nothing>
    data object Loading : Result<Nothing>
}
