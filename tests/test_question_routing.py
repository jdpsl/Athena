#!/usr/bin/env python3
"""Test question routing to ensure general questions don't trigger docs agent."""

from athena.cli import AthenaSession
from athena.models.config import AthenaConfig


def test_question_routing():
    """Test that question routing is specific to Athena docs."""
    print("\nTesting Question Routing\n")
    print("=" * 60)

    config = AthenaConfig(working_directory=".")
    session = AthenaSession(config)

    test_cases = [
        # Should NOT trigger docs agent
        ("what is in drone?", False),
        ("what is in this directory?", False),
        ("what are the files here?", False),
        ("list the contents", False),
        ("show me what's in the folder", False),
        ("what is the weather?", False),
        ("how do i cook pasta?", False),

        # SHOULD trigger docs agent
        ("what is athena?", True),
        ("what is mcp?", True),
        ("how do i configure athena?", True),
        ("what tools does athena have?", True),
        ("can athena do X?", True),
        ("what is a skill?", True),
        ("what is a tool?", True),
        ("explain athena features", True),
        ("how do i use athena?", True),
    ]

    passed = 0
    failed = 0

    for question, should_trigger_docs in test_cases:
        result = session._is_documentation_question(question)

        if result == should_trigger_docs:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1

        trigger_text = "DOCS" if result else "MAIN"
        expected_text = "DOCS" if should_trigger_docs else "MAIN"

        print(f"{status} '{question}' → {trigger_text} (expected: {expected_text})")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All question routing tests passed!")
    else:
        print(f"❌ {failed} tests failed")

    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    try:
        success = test_question_routing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
