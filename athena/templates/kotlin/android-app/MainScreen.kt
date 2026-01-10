package com.{{project_name_snake}}.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.{{project_name_snake}}.R
import com.{{project_name_snake}}.ui.theme.{{project_name}}Theme
import com.{{project_name_snake}}.viewmodel.MainViewModel

/**
 * Main screen of the app with a counter demonstration.
 *
 * This screen demonstrates:
 * - Material 3 Scaffold with TopAppBar and FAB
 * - State management with ViewModel
 * - Modern Compose UI patterns
 *
 * @param viewModel The ViewModel that manages the screen's state
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    viewModel: MainViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.app_name),
                        style = MaterialTheme.typography.titleLarge
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.increment() },
                containerColor = MaterialTheme.colorScheme.primaryContainer
            ) {
                Icon(
                    imageVector = Icons.Default.Add,
                    contentDescription = stringResource(R.string.increment)
                )
            }
        }
    ) { paddingValues ->
        MainContent(
            counter = uiState.counter,
            message = uiState.message,
            onIncrement = { viewModel.increment() },
            onDecrement = { viewModel.decrement() },
            onReset = { viewModel.reset() },
            modifier = Modifier.padding(paddingValues)
        )
    }
}

/**
 * Main content area showing the counter and controls.
 */
@Composable
private fun MainContent(
    counter: Int,
    message: String,
    onIncrement: () -> Unit,
    onDecrement: () -> Unit,
    onReset: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Counter display card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 32.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.secondaryContainer
            )
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = stringResource(R.string.counter_label),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = counter.toString(),
                    style = MaterialTheme.typography.displayLarge,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
        }

        // Message text
        Text(
            text = message,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        // Control buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterHorizontally)
        ) {
            Button(
                onClick = onDecrement,
                modifier = Modifier.weight(1f)
            ) {
                Text(stringResource(R.string.decrement))
            }

            FilledTonalButton(
                onClick = onReset,
                modifier = Modifier.weight(1f)
            ) {
                Text(stringResource(R.string.reset))
            }

            Button(
                onClick = onIncrement,
                modifier = Modifier.weight(1f)
            ) {
                Text(stringResource(R.string.increment))
            }
        }
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun MainScreenPreview() {
    {{project_name}}Theme {
        Surface {
            MainContent(
                counter = 42,
                message = "Tap the buttons to change the counter",
                onIncrement = {},
                onDecrement = {},
                onReset = {}
            )
        }
    }
}
