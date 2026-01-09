"""Test ddgs library directly."""

try:
    from ddgs import DDGS
    print("✓ ddgs library imported successfully")

    ddgs = DDGS()
    results = list(ddgs.text("Python 3.13 release date", region='wt-wt', max_results=3))

    print(f"\n✓ Got {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('title', 'N/A')}")
        print(f"   {result.get('body', 'N/A')[:100]}...")
        print(f"   {result.get('href', 'N/A')}\n")

except ImportError as e:
    print(f"✗ Failed to import ddgs: {e}")
except Exception as e:
    print(f"✗ Error during search: {e}")
