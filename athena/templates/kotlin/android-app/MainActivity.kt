package com.{{project_name_snake}}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.{{project_name_snake}}.ui.MainScreen
import com.{{project_name_snake}}.ui.theme.{{project_name}}Theme

/**
 * Main entry point for the {{project_name}} app.
 *
 * This activity sets up the Compose UI and enables edge-to-edge display
 * for a modern, immersive experience.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Enable edge-to-edge display (content behind system bars)
        enableEdgeToEdge()

        setContent {
            {{project_name}}Theme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen()
                }
            }
        }
    }
}
