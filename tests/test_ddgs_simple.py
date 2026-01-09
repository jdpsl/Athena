"""Test with a simple query."""

from duckduckgo_search import DDGS

queries = [
    "python programming",
    "weather today",
    "how to cook pasta",
]

for query in queries:
    print(f"\nSearching: {query}")
    print("="*60)
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=2))
        print(f"Results: {len(results)}")
        if results:
            for r in results:
                print(f"  - {r.get('title', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
