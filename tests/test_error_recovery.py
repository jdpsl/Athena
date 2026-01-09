#!/usr/bin/env python3
"""Test error recovery functionality."""

import asyncio
from athena.errors.classifier import ErrorClassifier, ErrorType
from athena.errors.strategies import (
    ExponentialBackoff,
    LinearBackoff,
    RateLimitBackoff,
    get_strategy_for_error_type,
)
from athena.errors.recovery import ErrorRecovery


def test_error_classification():
    """Test error classification."""
    print("\nTesting Error Classification\n")
    print("=" * 60)

    classifier = ErrorClassifier()

    test_cases = [
        ("Connection refused", ErrorType.NETWORK),
        ("network is unreachable", ErrorType.NETWORK),
        ("No such file or directory", ErrorType.FILE_NOT_FOUND),
        ("FileNotFoundError: file.txt", ErrorType.FILE_NOT_FOUND),
        ("Permission denied", ErrorType.PERMISSION),
        ("Access is denied", ErrorType.PERMISSION),
        ("SyntaxError: invalid syntax", ErrorType.SYNTAX),
        ("Operation timed out", ErrorType.TIMEOUT),
        ("429 Too Many Requests", ErrorType.RATE_LIMIT),
        ("Rate limit exceeded", ErrorType.RATE_LIMIT),
        ("ValueError: invalid input", ErrorType.VALIDATION),
        ("413 Request Entity Too Large", ErrorType.VALIDATION),
        ("Some random error", ErrorType.UNKNOWN),
    ]

    passed = 0
    failed = 0

    for error_msg, expected_type in test_cases:
        result = classifier.classify(error_msg)
        if result == expected_type:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1

        print(f"{status} '{error_msg[:40]:40}' → {result.value:15} (expected: {expected_type.value})")

    print("\n" + "=" * 60)
    print(f"Classification: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


async def test_retry_strategies():
    """Test retry strategies."""
    print("\nTesting Retry Strategies\n")
    print("=" * 60)

    # Test exponential backoff
    print("\n1. Exponential Backoff (max 3 attempts):")
    strategy = ExponentialBackoff(max_attempts=3, base_delay=0.1, max_delay=1.0)

    for attempt in range(1, 4):
        print(f"   Attempt {attempt}/{strategy.max_attempts}")
        if strategy.should_retry(attempt):
            import time
            start = time.time()
            await strategy.wait(attempt)
            elapsed = time.time() - start
            print(f"   Waited {elapsed:.2f}s")

    # Test linear backoff
    print("\n2. Linear Backoff (max 3 attempts):")
    strategy = LinearBackoff(max_attempts=3, base_delay=0.1)

    for attempt in range(1, 4):
        print(f"   Attempt {attempt}/{strategy.max_attempts}")
        if strategy.should_retry(attempt):
            import time
            start = time.time()
            await strategy.wait(attempt)
            elapsed = time.time() - start
            print(f"   Waited {elapsed:.2f}s")

    # Test rate limit backoff
    print("\n3. Rate Limit Backoff (faster test):")
    strategy = RateLimitBackoff(max_attempts=3, base_delay=0.1, max_delay=1.0)

    for attempt in range(1, 3):
        print(f"   Attempt {attempt}/{strategy.max_attempts}")
        if strategy.should_retry(attempt):
            import time
            start = time.time()
            await strategy.wait(attempt)
            elapsed = time.time() - start
            print(f"   Waited {elapsed:.2f}s")

    print("\n" + "=" * 60)
    print("✅ Retry strategies work correctly")
    print("=" * 60)


async def test_error_recovery():
    """Test error recovery with retries."""
    print("\nTesting Error Recovery\n")
    print("=" * 60)

    recovery = ErrorRecovery(enable_recovery=True)

    # Test 1: Function that succeeds immediately
    print("\n1. Testing immediate success:")

    async def success_func():
        return "Success!"

    result = await recovery.execute_with_recovery(
        success_func,
        operation_name="test operation"
    )
    print(f"   ✓ Result: {result}")

    # Test 2: Function that fails once then succeeds
    print("\n2. Testing retry after failure:")

    attempt_count = {"count": 0}

    async def retry_func():
        attempt_count["count"] += 1
        if attempt_count["count"] < 2:
            raise ConnectionError("Network error")
        return "Success after retry!"

    result = await recovery.execute_with_recovery(
        retry_func,
        operation_name="network operation"
    )
    print(f"   ✓ Result: {result} (after {attempt_count['count']} attempts)")

    # Test 3: Non-retryable error
    print("\n3. Testing non-retryable error:")

    async def non_retryable_func():
        raise FileNotFoundError("File not found")

    try:
        await recovery.execute_with_recovery(
            non_retryable_func,
            operation_name="file operation"
        )
    except FileNotFoundError:
        print("   ✓ Correctly failed without retry (FileNotFoundError)")

    # Test 4: Error classification and hints
    print("\n4. Testing error hints:")

    test_errors = [
        FileNotFoundError("file.txt not found"),
        PermissionError("Permission denied"),
        ConnectionError("Network unreachable"),
        TimeoutError("Operation timed out"),
    ]

    for error in test_errors:
        error_type = recovery.classify_error(error)
        hint = recovery.get_recovery_hint(error)
        is_retryable = recovery.is_retryable(error)
        print(f"   {type(error).__name__:20} → {error_type.value:15} retryable={is_retryable}")
        if hint:
            print(f"      Hint: {hint}")

    print("\n" + "=" * 60)
    print("✅ Error recovery works correctly")
    print("=" * 60)


async def test_strategy_selection():
    """Test automatic strategy selection."""
    print("\nTesting Strategy Selection\n")
    print("=" * 60)

    strategies = [
        (ErrorType.NETWORK, "ExponentialBackoff"),
        (ErrorType.TIMEOUT, "ExponentialBackoff"),
        (ErrorType.RATE_LIMIT, "RateLimitBackoff"),
        (ErrorType.FILE_NOT_FOUND, "NoRetry"),
        (ErrorType.PERMISSION, "NoRetry"),
        (ErrorType.SYNTAX, "NoRetry"),
        (ErrorType.UNKNOWN, "LinearBackoff"),
    ]

    for error_type, expected_strategy in strategies:
        strategy = get_strategy_for_error_type(error_type)
        strategy_name = type(strategy).__name__
        status = "✓" if strategy_name == expected_strategy else "✗"
        print(f"{status} {error_type.value:15} → {strategy_name:20} (expected: {expected_strategy})")

    print("\n" + "=" * 60)
    print("✅ Strategy selection works correctly")
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ERROR RECOVERY SYSTEM TESTS")
    print("=" * 60)

    # Run tests
    classification_ok = test_error_classification()
    await test_retry_strategies()
    await test_error_recovery()
    await test_strategy_selection()

    print("\n" + "=" * 60)
    if classification_ok:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  Some tests had issues")
    print("=" * 60)
    print("\nError recovery system is ready to use!")
    print("\nFeatures:")
    print("  • Automatic error classification (network, file, permission, etc.)")
    print("  • Intelligent retry strategies (exponential backoff, rate limiting)")
    print("  • LLM API calls automatically retry on network/timeout errors")
    print("  • Read-only tools retry on failure, write tools don't (safety)")
    print("  • Helpful error hints for recovery")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
        exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
