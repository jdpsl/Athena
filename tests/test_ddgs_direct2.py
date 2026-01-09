"""Test duckduckgo_search library directly."""

try:
    from duckduckgo_search import DDGS
    print("✓ duckduckgo_search library imported successfully")

    ddgs = DDGS()
    print("✓ DDGS instance created")

    print("\nSearching for: Python 3.13 release date")
    results = list(ddgs.text("Python 3.13 release date", region='wt-wt', max_results=3))

    print(f"\n✓ Got {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('title', 'N/A')}")
        print(f"   {result.get('body', 'N/A')[:100]}...")
        print(f"   {result.get('href', 'N/A')}\n")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
