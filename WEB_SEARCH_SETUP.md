# Web Search Configuration Guide

Web search is now fully configurable with slash commands!

## Quick Start

### 1. Switch to Brave Search (Recommended)

```bash
/use_brave
```

This switches to Brave Search API. You'll see a message about setting your API key.

### 2. Set Your Brave API Key

```bash
/braveapi YOUR_API_KEY_HERE
```

Get a free API key at: https://brave.com/search/api/
- Free tier: 2,000 queries/month
- No credit card required

### 3. Save Your Settings

```bash
/save
```

This saves your web search configuration to `~/.athena/config.json` so it persists across sessions.

## Available Commands

### Switching Search Engines

- `/use_brave` - Use Brave Search API (recommended)
- `/use_duckduckgo` - Use DuckDuckGo (currently broken due to CAPTCHA)
- `/use_searxng [url]` - Use SearXNG instance (self-hosted)

### API Configuration

- `/braveapi [key]` - Set Brave Search API key (only shown when Brave is active)
- `/config` - View current configuration including web search settings

### Persistence

- `/save` - Save all settings including web search configuration

## Example Workflow

```bash
# 1. Switch to Brave Search
/use_brave

# 2. Set your API key
/braveapi BSA1234567890abcdef

# 3. Save settings
/save

# 4. Now web search works!
# Ask Athena to search:
Search for Python async best practices
```

## Configuration File

Settings are saved to `~/.athena/config.json`:

```json
{
  "model": "your-model",
  "api_base": "your-api-base",
  "api_key": "your-llm-key",
  "temperature": 0.7,
  "search_api": "brave",
  "brave_api_key": "your-brave-key",
  "google_api_key": null,
  "google_cx": null,
  "searxng_url": null
}
```

## Alternative Options

### SearXNG (Self-Hosted)

If you prefer self-hosting:

```bash
# Set your SearXNG instance URL
/use_searxng http://localhost:8888

# Save settings
/save
```

Learn more: https://docs.searxng.org/

### Google Custom Search

Currently supported but requires setup:
- Google API key
- Custom Search Engine ID
- Limited to 100 free queries/day

(Commands for Google not yet implemented - use config file directly)

## Checking Your Configuration

```bash
/config
```

This shows:
- Current search API
- Whether API keys are set
- All other Athena settings

## Notes

- DuckDuckGo HTML scraping no longer works (CAPTCHA blocking)
- Brave Search is the recommended default
- Settings persist across Athena restarts when saved
- `/braveapi` command only appears in `/help` when Brave is selected
