"""Test the updated WebSearch tool."""

import asyncio
from athena.tools.web import WebSearchTool


async def test_websearch():
    """Test WebSearch with ddgs library."""

    # Create tool instance
    tool = WebSearchTool(search_api="duckduckgo")

    # Test search
    print("Testing WebSearch with query: 'Python 3.13 release date'")
    print("="*80)

    result = await tool.execute(query="Python 3.13 release date", num_results=3)

    print(f"\nSuccess: {result.success}")
    if result.success:
        print(f"\nResults:\n{result.output}")
        print(f"\nMetadata: {result.metadata}")
    else:
        print(f"\nError: {result.error}")

    print("\n" + "="*80)
    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(test_websearch())
