#!/usr/bin/env python3
"""Test the Insert tool."""

import asyncio
import os
import tempfile
from pathlib import Path
from athena.tools.file_ops import InsertTool

async def test_insert_tool():
    """Test InsertTool functionality."""
    tool = InsertTool()

    print("Testing InsertTool:\n")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        test_file = f.name
        f.write("def hello():\n")
        f.write("    print('Hello, World!')\n")
        f.write("\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    hello()\n")

    try:
        print(f"Created test file: {test_file}")

        # Read original content
        with open(test_file, 'r') as f:
            original_content = f.read()
        print("\nOriginal content:")
        print(original_content)
        print("-" * 60)

        # Test 1: Insert at beginning (line 0)
        print("\nTest 1: Insert docstring at beginning")
        result = await tool.execute(
            file_path=test_file,
            insert_line=0,
            new_text='"""Test module for Insert tool."""\n'
        )
        print(f"Result: {result.output}")
        assert result.success, f"Test 1 failed: {result.error}"

        with open(test_file, 'r') as f:
            content = f.read()
        print("Content after insert at line 0:")
        print(content)
        print("-" * 60)

        # Test 2: Insert after line 1 (add import after docstring)
        print("\nTest 2: Insert import after docstring")
        result = await tool.execute(
            file_path=test_file,
            insert_line=1,
            new_text='import sys\n\n'
        )
        print(f"Result: {result.output}")
        assert result.success, f"Test 2 failed: {result.error}"

        with open(test_file, 'r') as f:
            content = f.read()
        print("Content after insert at line 1:")
        print(content)
        print("-" * 60)

        # Test 3: Insert comment after import
        print("\nTest 3: Insert comment after import")
        result = await tool.execute(
            file_path=test_file,
            insert_line=3,
            new_text='# Main greeting function\n'
        )
        print(f"Result: {result.output}")
        assert result.success, f"Test 3 failed: {result.error}"

        with open(test_file, 'r') as f:
            content = f.read()
        print("Content after insert at line 4:")
        print(content)
        print("-" * 60)

        # Test 4: Invalid line number (should fail)
        print("\nTest 4: Invalid line number (should fail)")
        result = await tool.execute(
            file_path=test_file,
            insert_line=999,
            new_text='This should fail\n'
        )
        print(f"Result: {result.output if result.success else result.error}")
        assert not result.success, "Test 4 should have failed"
        print("✓ Correctly rejected invalid line number")
        print("-" * 60)

        # Test 5: File not found (should fail)
        print("\nTest 5: File not found (should fail)")
        result = await tool.execute(
            file_path="/nonexistent/file.txt",
            insert_line=0,
            new_text="test"
        )
        print(f"Result: {result.error}")
        assert not result.success, "Test 5 should have failed"
        print("✓ Correctly rejected nonexistent file")
        print("-" * 60)

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        # Show final content
        with open(test_file, 'r') as f:
            final_content = f.read()
        print("\nFinal file content:")
        print(final_content)

    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"\nCleaned up test file: {test_file}")

if __name__ == "__main__":
    asyncio.run(test_insert_tool())
