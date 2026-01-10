package com.{{project_name_snake}}.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.{{project_name_snake}}.model.UiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * ViewModel for the main screen.
 *
 * This ViewModel manages the UI state and business logic for the main screen.
 * It uses Kotlin Flow for state management and Coroutines for asynchronous operations.
 *
 * Key responsibilities:
 * - Manage counter state
 * - Handle user actions (increment, decrement, reset)
 * - Update UI state messages
 */
class MainViewModel : ViewModel() {

    // Private mutable state (only ViewModel can modify)
    private val _uiState = MutableStateFlow(UiState())

    // Public read-only state (UI observes this)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    /**
     * Increment the counter by 1.
     */
    fun increment() {
        viewModelScope.launch {
            _uiState.update { currentState ->
                val newCounter = currentState.counter + 1
                currentState.copy(
                    counter = newCounter,
                    message = "Counter incremented to $newCounter"
                )
            }
        }
    }

    /**
     * Decrement the counter by 1 (minimum 0).
     */
    fun decrement() {
        viewModelScope.launch {
            _uiState.update { currentState ->
                val newCounter = maxOf(0, currentState.counter - 1)
                currentState.copy(
                    counter = newCounter,
                    message = if (currentState.counter > 0) {
                        "Counter decremented to $newCounter"
                    } else {
                        "Counter is already at minimum (0)"
                    }
                )
            }
        }
    }

    /**
     * Reset the counter to 0.
     */
    fun reset() {
        viewModelScope.launch {
            _uiState.update { currentState ->
                currentState.copy(
                    counter = 0,
                    message = "Counter reset to 0"
                )
            }
        }
    }

    /**
     * Example of loading data asynchronously.
     *
     * Uncomment and modify for your needs:
     *
     * fun loadData() {
     *     viewModelScope.launch {
     *         _uiState.update { it.copy(isLoading = true) }
     *         try {
     *             val data = repository.fetchData()
     *             _uiState.update { it.copy(data = data, isLoading = false) }
     *         } catch (e: Exception) {
     *             _uiState.update { it.copy(error = e.message, isLoading = false) }
     *         }
     *     }
     * }
     */
}
