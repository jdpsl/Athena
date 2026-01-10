package com.{{project_name_snake}}

import com.{{project_name_snake}}.model.UiState
import com.{{project_name_snake}}.viewmodel.MainViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for {{project_name}}.
 *
 * These tests verify the business logic in isolation without Android dependencies.
 * For UI tests, see the androidTest directory.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MainViewModelTest {

    private lateinit var viewModel: MainViewModel

    @Before
    fun setup() {
        viewModel = MainViewModel()
    }

    @Test
    fun `initial state has counter at zero`() = runTest {
        // Given: Fresh ViewModel
        // When: Get initial state
        val state = viewModel.uiState.first()

        // Then: Counter should be 0
        assertEquals(0, state.counter)
    }

    @Test
    fun `increment increases counter by one`() = runTest {
        // Given: Initial counter value
        val initialCounter = viewModel.uiState.value.counter

        // When: Increment is called
        viewModel.increment()

        // Then: Counter should increase by 1
        val newState = viewModel.uiState.first()
        assertEquals(initialCounter + 1, newState.counter)
    }

    @Test
    fun `decrement decreases counter by one`() = runTest {
        // Given: Counter at 5
        repeat(5) { viewModel.increment() }

        // When: Decrement is called
        viewModel.decrement()

        // Then: Counter should be 4
        val state = viewModel.uiState.first()
        assertEquals(4, state.counter)
    }

    @Test
    fun `decrement does not go below zero`() = runTest {
        // Given: Counter at 0
        assertEquals(0, viewModel.uiState.value.counter)

        // When: Decrement is called
        viewModel.decrement()

        // Then: Counter should still be 0
        val state = viewModel.uiState.first()
        assertEquals(0, state.counter)
    }

    @Test
    fun `reset sets counter to zero`() = runTest {
        // Given: Counter at 42
        repeat(42) { viewModel.increment() }
        assertEquals(42, viewModel.uiState.value.counter)

        // When: Reset is called
        viewModel.reset()

        // Then: Counter should be 0
        val state = viewModel.uiState.first()
        assertEquals(0, state.counter)
    }

    @Test
    fun `increment updates message`() = runTest {
        // When: Increment is called
        viewModel.increment()

        // Then: Message should reflect the increment
        val state = viewModel.uiState.first()
        assertTrue(state.message.contains("incremented"))
    }
}

/**
 * Example tests for data models.
 */
class UiStateTest {

    @Test
    fun `UiState defaults are correct`() {
        // Given: Default UiState
        val state = UiState()

        // Then: Defaults should be set correctly
        assertEquals(0, state.counter)
        assertEquals("Welcome to {{project_name}}!", state.message)
        assertEquals(false, state.isLoading)
        assertNull(state.error)
    }

    @Test
    fun `UiState copy works correctly`() {
        // Given: Initial state
        val initialState = UiState(counter = 5, message = "Test")

        // When: Copy with changes
        val newState = initialState.copy(counter = 10)

        // Then: Only changed property should be different
        assertEquals(10, newState.counter)
        assertEquals("Test", newState.message) // Unchanged
    }
}
