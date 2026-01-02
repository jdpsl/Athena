"""Web tools for searching and fetching content."""

import json
import re
from typing import Any, Optional
from urllib.parse import quote_plus
import requests
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult

# Import ddgs for DuckDuckGo search (try both package names)
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False


class WebSearchTool(Tool):
    """Tool for searching the web."""

    def __init__(self, search_api: str = "duckduckgo"):
        """Initialize web search tool.

        Args:
            search_api: Search API to use (duckduckgo, brave, google, searxng)
        """
        super().__init__()
        self.search_api = search_api
        self.brave_api_key = None  # Set via config if using Brave
        self.google_api_key = None  # Set via config if using Google
        self.google_cx = None  # Google Custom Search Engine ID
        self.searxng_url = None  # SearXNG instance URL

    @property
    def name(self) -> str:
        return "WebSearch"

    @property
    def description(self) -> str:
        return """Search the web and get structured results with titles, snippets, and URLs.

Returns search results that you can browse. Use WebFetch to read full content from specific URLs.

IMPORTANT: After using this tool, you MUST include a 'Sources:' section in your response
with markdown links to the URLs you reference."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description="Search query",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type=ToolParameterType.NUMBER,
                description="Number of results to return (default: 10, max: 20)",
                required=False,
                default=10,
            ),
        ]

    async def execute(
        self, query: str, num_results: int = 10, **kwargs: Any
    ) -> ToolResult:
        """Execute web search."""
        try:
            num_results = min(num_results, 20)  # Cap at 20

            # Route to appropriate search API
            if self.search_api == "brave" and self.brave_api_key:
                results = self._search_brave(query, num_results)
            elif self.search_api == "google" and self.google_api_key:
                results = self._search_google(query, num_results)
            elif self.search_api == "searxng" and self.searxng_url:
                results = self._search_searxng(query, num_results)
            else:
                # Default to DuckDuckGo (no API key needed)
                results = self._search_duckduckgo(query, num_results)

            if not results:
                return ToolResult(
                    success=True,
                    output=f"No results found for: {query}",
                    metadata={"query": query, "count": 0},
                )

            # Format results
            output_lines = [f"Search results for: {query}\n"]
            for i, result in enumerate(results, 1):
                output_lines.append(f"{i}. **{result['title']}**")
                output_lines.append(f"   {result['snippet']}")
                output_lines.append(f"   URL: {result['url']}\n")

            output = "\n".join(output_lines)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "query": query,
                    "count": len(results),
                    "results": results,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Web search failed: {str(e)}",
            )

    def _search_duckduckgo(self, query: str, num_results: int) -> list[dict]:
        """Search using DuckDuckGo via ddgs library (no API key needed)."""
        try:
            # Use ddgs library if available
            if DDGS_AVAILABLE:
                ddgs = DDGS()
                raw_results = list(ddgs.text(query, region='wt-wt', max_results=num_results))

                # Map ddgs result format to our expected format
                results = []
                for result in raw_results:
                    results.append({
                        "title": result.get('title', 'N/A'),
                        "snippet": result.get('body', 'N/A'),
                        "url": result.get('href', 'N/A'),
                    })

                return results

            # Fallback to HTML scraping if ddgs not available (legacy)
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML results (simple regex-based parsing)
            results = []

            # Extract results using regex
            title_pattern = r'<a class="result__a" href="(.*?)">(.*?)</a>'
            snippet_pattern = r'<a class="result__snippet".*?>(.*?)</a>'

            titles = re.findall(title_pattern, response.text)
            snippets = re.findall(snippet_pattern, response.text)

            for i, ((url, title), snippet) in enumerate(zip(titles, snippets)):
                if i >= num_results:
                    break

                # Clean HTML tags from title and snippet
                title_clean = re.sub(r"<.*?>", "", title)
                snippet_clean = re.sub(r"<.*?>", "", snippet)

                results.append(
                    {
                        "title": title_clean.strip(),
                        "snippet": snippet_clean.strip(),
                        "url": url.strip(),
                    }
                )

            return results[:num_results]

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    def _search_brave(self, query: str, num_results: int) -> list[dict]:
        """Search using Brave Search API."""
        if not self.brave_api_key:
            return []

        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key,
            }
            params = {"q": query, "count": num_results}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("web", {}).get("results", [])[:num_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("description", ""),
                        "url": item.get("url", ""),
                    }
                )

            return results

        except Exception as e:
            print(f"Brave search error: {e}")
            return []

    def _search_google(self, query: str, num_results: int) -> list[dict]:
        """Search using Google Custom Search API."""
        if not self.google_api_key or not self.google_cx:
            return []

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(num_results, 10),  # Google max is 10 per request
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", [])[:num_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                    }
                )

            return results

        except Exception as e:
            print(f"Google search error: {e}")
            return []

    def _search_searxng(self, query: str, num_results: int) -> list[dict]:
        """Search using SearXNG instance."""
        if not self.searxng_url:
            return []

        try:
            url = f"{self.searxng_url}/search"
            params = {"q": query, "format": "json", "number_of_results": num_results}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("results", [])[:num_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("content", ""),
                        "url": item.get("url", ""),
                    }
                )

            return results

        except Exception as e:
            print(f"SearXNG search error: {e}")
            return []


class WebFetchTool(Tool):
    """Tool for fetching web content."""

    def __init__(self, llm_client=None):
        """Initialize web fetch tool.

        Args:
            llm_client: Optional LLM client for AI-enhanced extraction
        """
        super().__init__()
        self.llm_client = llm_client

    @property
    def name(self) -> str:
        return "WebFetch"

    @property
    def description(self) -> str:
        return """Fetch and extract content from a URL.

Converts HTML to clean, readable markdown. Optionally use AI to extract specific information.

Use this after WebSearch to read full content from interesting URLs."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type=ToolParameterType.STRING,
                description="URL to fetch",
                required=True,
            ),
            ToolParameter(
                name="extract_prompt",
                type=ToolParameterType.STRING,
                description="Optional: What to extract (uses AI if provided)",
                required=False,
            ),
        ]

    async def execute(
        self, url: str, extract_prompt: Optional[str] = None, **kwargs: Any
    ) -> ToolResult:
        """Execute web fetch."""
        try:
            # Fetch content
            content = self._fetch_and_convert(url)

            if not content:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Failed to extract content from: {url}",
                )

            # If no extraction prompt, return cleaned content
            if not extract_prompt or not self.llm_client:
                # Truncate if too long (keep first 8000 chars)
                if len(content) > 8000:
                    content = content[:8000] + "\n\n[Content truncated...]"

                return ToolResult(
                    success=True,
                    output=f"Content from {url}:\n\n{content}",
                    metadata={"url": url, "length": len(content)},
                )

            # AI-enhanced extraction
            extracted = await self._extract_with_ai(content, extract_prompt)

            return ToolResult(
                success=True,
                output=f"Extracted from {url}:\n\n{extracted}",
                metadata={
                    "url": url,
                    "original_length": len(content),
                    "extracted_length": len(extracted),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to fetch URL: {str(e)}",
            )

    def _fetch_and_convert(self, url: str) -> str:
        """Fetch URL and convert to clean text."""
        try:
            # Try using trafilatura first (best for articles)
            try:
                import trafilatura

                downloaded = trafilatura.fetch_url(url)
                text = trafilatura.extract(downloaded, include_comments=False)
                if text:
                    return text
            except ImportError:
                pass

            # Fallback: use requests + basic HTML cleaning
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # Try html2text if available
            try:
                import html2text

                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.ignore_emphasis = False
                return h.handle(response.text)
            except ImportError:
                pass

            # Last resort: basic BeautifulSoup cleaning
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)

                return text
            except ImportError:
                # Absolute fallback: regex-based cleaning
                text = re.sub(r"<script.*?</script>", "", response.text, flags=re.DOTALL)
                text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
                text = re.sub(r"<.*?>", "", text)
                text = re.sub(r"\s+", " ", text)
                return text.strip()

        except Exception as e:
            raise Exception(f"Failed to fetch and convert: {e}")

    async def _extract_with_ai(self, content: str, prompt: str) -> str:
        """Use AI to extract specific information from content."""
        try:
            from athena.models.message import Message, Role

            # Truncate content if too long
            max_content = 6000
            if len(content) > max_content:
                content = content[:max_content] + "\n\n[Content truncated...]"

            # Create extraction prompt
            extraction_message = Message(
                role=Role.USER,
                content=f"""From the following web content, {prompt}

Web Content:
{content}

Please extract and summarize the relevant information.""",
            )

            # Use LLM to extract
            response = await self.llm_client.generate(
                messages=[extraction_message], temperature=0.3  # Lower temp for extraction
            )

            return response.content

        except Exception as e:
            # If AI extraction fails, return original content
            print(f"AI extraction failed: {e}")
            return content
