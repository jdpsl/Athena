#!/usr/bin/env python3
"""Test the athena-docs agent."""

from athena.cli import AthenaSession
from athena.models.config import AthenaConfig

# Test the documentation question detection
config = AthenaConfig()  # Use default config
session = AthenaSession(config)

test_questions = [
    ("What tools does Athena have?", True),
    ("How do I configure web search?", True),
    ("Can Athena do X?", True),
    ("Does Athena support MCP?", True),
    ("Fix this bug in my code", False),
    ("Write a function to calculate fibonacci", False),
    ("How does the agent work?", True),
    ("Explain what MCP is", True),
    ("Read the file test.py", False),
    ("Tell me about Athena features", True),
]

print("Testing documentation question detection:\n")
for question, expected in test_questions:
    result = session._is_documentation_question(question)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{question}' -> {result} (expected {expected})")

print("\n" + "="*60)
print("Summary:")
passed = sum(1 for q, e in test_questions if session._is_documentation_question(q) == e)
total = len(test_questions)
print(f"Passed: {passed}/{total}")
