# Web Tools Guide

Athena can now search the internet and fetch web pages - just like Claude Code!

## 🌐 Available Web Tools

### 1. WebSearch - Search the Internet
### 2. WebFetch - Read Web Pages (HTML→Markdown + AI extraction)

---

## 📊 WebSearch Tool

**What it does:**
- Searches the internet using DuckDuckGo (default, no API key needed)
- Returns structured results: titles, snippets, URLs
- Supports multiple search engines (Brave, Google, SearXNG)

### Basic Usage

```
You: Search for "Python async best practices"

Athena uses WebSearch:
→ Returns 10 search results
→ Each with title, snippet, URL

You can then:
- Ask Athena to summarize findings
- Use WebFetch to read specific URLs
- Get code examples from results
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `query` | Search query | Required |
| `num_results` | Number of results | 10 (max 20) |

### Example Session

```
You: Search for how to implement OAuth2 in FastAPI

Athena:
[Uses WebSearch tool]

Search results for: OAuth2 FastAPI

1. **FastAPI OAuth2 with Password and Bearer**
   Complete guide to implementing OAuth2 authentication...
   URL: https://fastapi.tiangolo.com/tutorial/security/

2. **OAuth2 Authentication in FastAPI**
   Step-by-step tutorial with working code examples...
   URL: https://realpython.com/fastapi-oauth2/

3. **FastAPI Security Best Practices**
   Security patterns including OAuth2, JWT tokens...
   URL: https://example.com/security

[Continues with more results...]

Based on these results, FastAPI has built-in OAuth2 support...

Sources:
- [FastAPI OAuth2 Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [Real Python FastAPI OAuth2](https://realpython.com/fastapi-oauth2/)
```

---

## 📄 WebFetch Tool

**What it does:**
- Fetches web pages
- Converts HTML → Clean Markdown
- Optional: AI-enhanced extraction for specific info

### Mode 1: Simple Fetch (HTML→Markdown)

```python
You: Fetch https://fastapi.tiangolo.com/tutorial/security/

Athena uses WebFetch (simple mode):
→ Downloads page
→ Removes scripts, styles, navigation
→ Converts to clean markdown
→ Returns readable content

Returns:
# FastAPI Security Tutorial

OAuth2 with Password (and hashing), Bearer with JWT tokens

This tutorial shows how to implement complete security...

## Installation
First install the dependencies:
pip install fastapi[all]

## Simple OAuth2
...
```

### Mode 2: AI-Enhanced Extraction

```python
You: From https://example.com/api-docs, extract the authentication endpoints

Athena uses WebFetch (AI mode):
→ Downloads page
→ Converts HTML→Markdown
→ Passes to AI with extraction prompt
→ Returns only relevant info

Returns:
Extracted from https://example.com/api-docs:

Authentication Endpoints:
1. POST /auth/login
   - Parameters: username, password
   - Returns: access_token, refresh_token

2. POST /auth/refresh
   - Parameters: refresh_token
   - Returns: new access_token
...
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `url` | URL to fetch | Yes |
| `extract_prompt` | What to extract (enables AI mode) | No |

---

## 🔥 Real-World Examples

### Example 1: Research & Implementation

```
You: I need to add rate limiting to my FastAPI app.
     Search for best practices and show me how.

Athena:
[Uses WebSearch for "FastAPI rate limiting"]

Search results show several approaches...

[Uses WebFetch on top result]

Based on the documentation, here's how to implement rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/items")
@limiter.limit("5/minute")
async def get_items():
    return {"items": [...]}
```

Sources:
- [SlowAPI Documentation](https://slowapi.readthedocs.io/)
- [FastAPI Rate Limiting Guide](https://example.com/guide)
```

### Example 2: Documentation Lookup

```
You: What are the latest features in Python 3.12?

Athena:
[Uses WebSearch for "Python 3.12 new features"]

[Uses WebFetch with AI extraction on python.org]

Python 3.12 New Features:

1. **Improved Error Messages**
   - Better syntax error suggestions
   - More precise tracebacks

2. **Per-Interpreter GIL**
   - Subinterpreters can have their own GIL
   - Better parallelism

3. **Performance Improvements**
   - 5-10% faster than 3.11
   - Better memory usage
...

Sources:
- [Python 3.12 Release Notes](https://docs.python.org/3.12/whatsnew/)
```

### Example 3: API Documentation

```
You: Find documentation for the Stripe payment intent API

Athena:
[Uses WebSearch for "Stripe payment intent API"]

[Uses WebFetch with extraction on stripe.com/docs]

Stripe Payment Intent API:

**Create Payment Intent:**
POST /v1/payment_intents

Parameters:
- amount (required): Amount in cents
- currency (required): Three-letter currency code
- payment_method_types: ["card"]

Example:
```python
stripe.PaymentIntent.create(
    amount=2000,
    currency="usd",
    payment_method_types=["card"]
)
```

Sources:
- [Stripe Payment Intents API](https://stripe.com/docs/api/payment_intents)
```

### Example 4: Debugging Assistance

```
You: Getting error "ModuleNotFoundError: No module named 'fastapi.security'"
     Search for solutions

Athena:
[Uses WebSearch for error message]

[Uses WebFetch to read Stack Overflow top answer]

This error occurs when FastAPI dependencies aren't fully installed.

Solution:
```bash
pip uninstall fastapi
pip install fastapi[all]
```

The issue is that `fastapi.security` requires optional dependencies
that aren't installed with basic `pip install fastapi`.

Sources:
- [Stack Overflow: FastAPI Security Import Error](https://stackoverflow.com/...)
```

---

## 🎯 Advanced Features

### Multiple Search Engines

WebSearch supports multiple backends:

**DuckDuckGo (Default)**
- No API key needed
- Free, unlimited searches
- Privacy-focused
- Already configured!

**Brave Search API**
```python
# Set in config.yaml or .env
BRAVE_API_KEY=your_key_here

# In code:
web_search = WebSearchTool(search_api="brave")
web_search.brave_api_key = "your_key_here"
```
- 2000 free searches/month
- Fast, good results

**Google Custom Search**
```python
GOOGLE_API_KEY=your_key_here
GOOGLE_CX=your_search_engine_id

web_search = WebSearchTool(search_api="google")
web_search.google_api_key = "your_key"
web_search.google_cx = "your_cx"
```
- 100 free searches/day
- Best quality results

**SearXNG (Self-hosted)**
```python
SEARXNG_URL=http://localhost:8888

web_search = WebSearchTool(search_api="searxng")
web_search.searxng_url = "http://localhost:8888"
```
- Unlimited searches
- Aggregates multiple engines
- Full privacy control

### AI Extraction Prompts

WebFetch becomes powerful with extraction prompts:

```
# Extract code examples
WebFetch(
    url="...",
    extract_prompt="extract all Python code examples"
)

# Extract specific data
WebFetch(
    url="...",
    extract_prompt="list all API endpoints with their parameters"
)

# Summarize
WebFetch(
    url="...",
    extract_prompt="summarize the main points in 3 bullet points"
)

# Compare
WebFetch(
    url="...",
    extract_prompt="compare the pros and cons mentioned in this article"
)
```

---

## 🛠️ How It Works Internally

### WebSearch Flow
```
1. User asks question
2. Athena decides to search
3. WebSearch sends query to API
4. Gets JSON results: [{title, snippet, url}, ...]
5. Formats as markdown
6. Athena analyzes results
7. May fetch specific URLs for more info
```

### WebFetch Flow (Simple Mode)
```
1. Download HTML from URL
2. Try trafilatura (best for articles)
   ↓ if fails
3. Try html2text (converts HTML→Markdown)
   ↓ if fails
4. Use BeautifulSoup (strip tags, clean text)
5. Return clean content
```

### WebFetch Flow (AI Mode)
```
1. Download & convert HTML→Markdown
2. Truncate to ~6000 chars (fits in context)
3. Send to LLM with prompt:
   "From this content, {extract_prompt}"
4. LLM returns only relevant extracted info
5. Return focused, summarized content
```

---

## 📊 Performance

**WebSearch:**
- Speed: ~1-2 seconds
- No AI processing needed
- Returns structured data immediately

**WebFetch (Simple):**
- Speed: ~2-4 seconds
- HTML download + conversion
- No AI processing

**WebFetch (AI Enhanced):**
- Speed: ~5-10 seconds
- HTML download + conversion + AI extraction
- Uses your configured model

---

## 💡 Best Practices

1. **Search First, Then Fetch**
   ```
   WebSearch → get URLs
   WebFetch → read interesting ones
   ```

2. **Use AI Extraction for Large Pages**
   ```
   Instead of fetching entire documentation,
   use extract_prompt to get just what you need
   ```

3. **Include Sources**
   ```
   Always cite URLs in your response
   Athena will remind you!
   ```

4. **Combine with Local Search**
   ```
   WebSearch for docs/examples
   Grep local files for implementation
   Combine knowledge!
   ```

5. **Cache Results**
   ```
   If you fetch the same URL repeatedly,
   copy the content to a local file
   ```

---

## 🚀 Installation

The web tools are already integrated! Just install dependencies:

```bash
cd athena
pip install -e .
```

This installs:
- `requests` - HTTP requests
- `trafilatura` - Best HTML→Text extraction
- `html2text` - HTML→Markdown conversion
- `beautifulsoup4` - HTML parsing fallback

---

## 🎮 Try It Out

```bash
$ athena

You: Search for "async Python tutorial"
# Athena searches and shows results

You: Fetch the first result and summarize it
# Athena fetches and summarizes

You: Now search for "Python async best practices"
     and extract the top 5 recommendations
# Athena searches, fetches top results, extracts practices

You: Create a Python script implementing those practices
# Athena writes code based on what it learned!
```

---

## 🔧 Configuration

Add to your `config.yaml` or `.env`:

```yaml
# config.yaml
web:
  search_engine: duckduckgo  # or brave, google, searxng
  brave_api_key: null
  google_api_key: null
  google_cx: null
  searxng_url: null
```

```bash
# .env
WEB_SEARCH_ENGINE=duckduckgo
BRAVE_API_KEY=
GOOGLE_API_KEY=
GOOGLE_CX=
SEARXNG_URL=
```

---

## 📚 Summary

Athena's web tools give you:

✅ **Internet search** - Find docs, examples, solutions
✅ **Web page reading** - Clean HTML→Markdown conversion
✅ **AI extraction** - Get specific info from pages
✅ **Multiple search engines** - DuckDuckGo, Brave, Google, SearXNG
✅ **No API keys required** - DuckDuckGo works out of the box
✅ **Smart processing** - AI extracts only what you need

Now Athena can:
- Research documentation
- Find code examples
- Debug by searching error messages
- Learn new APIs
- Stay updated on best practices
- Access the entire internet!

Just like Claude Code, but **open source** and **free**! 🎉
