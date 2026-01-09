# Proactive Testing in Athena

Athena now automatically runs tests after code changes, matching Claude Code's proactive behavior.

## What Changed

### Before (Passive) ❌

```
User: "Fix the login bug in auth.py"

Athena: [Reads auth.py]
Athena: [Makes changes with Edit tool]
Athena: "I've fixed the login bug. The issue was in the validateToken function.
        Would you like me to run the tests?"

User: "yes please"

Athena: [Runs pytest]
Athena: "Tests passing!"
```

**Problem**: Extra back-and-forth. User has to ask for tests.

### After (Proactive) ✓

```
User: "Fix the login bug in auth.py"

Athena: [Reads auth.py]
Athena: [Makes changes with Edit tool]
Athena: [Immediately runs: pytest tests/test_auth.py]
Athena: "Fixed the login bug in validateToken! All 23 tests passing ✓"
```

**Result**: One interaction. Tests run automatically. User is happy.

---

## When Tests Run Automatically

Athena now runs tests automatically in these scenarios:

1. **After writing new functions/classes**
   ```
   User: "Add a validateEmail function"
   Athena: [Writes function] [Runs pytest] "Added! Tests passing ✓"
   ```

2. **After modifying existing code**
   ```
   User: "Refactor the database module for better performance"
   Athena: [Refactors] [Runs tests] "Refactored! 15% faster, tests pass ✓"
   ```

3. **After fixing bugs**
   ```
   User: "The date parser is crashing on invalid input"
   Athena: [Fixes bug] [Runs tests] "Fixed! Added error handling, tests pass ✓"
   ```

4. **Before committing code**
   ```
   User: "Commit the changes"
   Athena: [Runs tests first] "Tests pass ✓" [Creates commit]
   ```

5. **When user requests changes to tested code**
   ```
   User: "Update the API endpoint to return JSON instead of XML"
   Athena: [Makes changes] [Runs tests] "Updated! Tests pass ✓"
   ```

---

## Test Commands by Project Type

Athena automatically detects and uses the right test command:

| Project Type | Test Command | How It's Detected |
|--------------|--------------|-------------------|
| **Python** | `pytest` or `python -m pytest` | pyproject.toml, setup.py, tests/ directory |
| **Node.js** | `npm test` or `yarn test` | package.json with "test" script |
| **Rust** | `cargo test` | Cargo.toml |
| **Go** | `go test ./...` | go.mod |
| **Generic** | Checks Makefile, README | Look for "make test" or documented commands |

---

## Real-World Examples

### Example 1: Fixing a Bug

**User**: "The calculateTotal function is giving wrong results for negative numbers"

**Athena's Actions**:
1. Reads the file with the bug
2. Identifies the issue
3. Fixes the code using Edit tool
4. **Automatically runs**: `pytest tests/test_calculations.py`
5. Reports: "Fixed calculateTotal! Now handles negative numbers correctly. All 34 tests passing ✓"

**No asking. No waiting. Just done.**

### Example 2: Adding a Feature

**User**: "Add support for JWT authentication"

**Athena's Actions**:
1. Reads existing auth code
2. Adds JWT authentication with Edit tool
3. **Automatically runs**: `pytest tests/test_auth.py`
4. Sees 2 test failures (expected - new feature needs test updates)
5. Updates the tests automatically
6. **Runs tests again**: All passing
7. Reports: "Added JWT authentication! Updated tests, all 45 tests passing ✓"

**Athena fixes test failures automatically without asking!**

### Example 3: Refactoring

**User**: "Refactor the database connection pooling"

**Athena's Actions**:
1. Analyzes current implementation
2. Refactors the code for better performance
3. **Automatically runs**: `pytest tests/test_database.py`
4. Tests pass
5. **Runs full test suite**: `pytest`
6. Reports: "Refactored database pooling! 30% faster connections, all 127 tests passing ✓"

**Tests the specific area, then full suite. No permission needed.**

### Example 4: When Tests Fail

**User**: "Update the API to version 2"

**Athena's Actions**:
1. Updates API code
2. **Runs**: `pytest tests/test_api.py`
3. Sees 5 failures
4. **Automatically investigates**: Reads test output, identifies breaking changes
5. **Fixes the code**: Updates to maintain backward compatibility
6. **Runs tests again**: Still 2 failures
7. **Updates tests**: Changes expected responses for v2
8. **Runs tests again**: All pass
9. Reports: "Updated to API v2! Fixed compatibility issues and updated tests. All 67 tests passing ✓"

**No asking at each step. Just fixes until tests pass.**

---

## What If Tests Don't Exist?

Athena handles this gracefully:

```
User: "Add a new sortByPriority function"

Athena: [Adds function]
Athena: [Runs: pytest]
Athena: "Added sortByPriority function! Note: No tests found for this module.
        Existing tests (34) still pass ✓"
```

**Result**: Doesn't block progress, but notes the missing tests.

---

## Behavior Comparison

### Claude Code (Original)
- ✓ Runs tests automatically
- ✓ Fixes failures automatically
- ✓ No permission asking
- ✓ Reports results concisely

### Athena (Before This Change)
- ❌ Asked permission to run tests
- ❌ Required user to say "yes run tests"
- ✓ Ran tests when asked
- ✓ Fixed failures when asked

### Athena (After This Change)
- ✓ Runs tests automatically
- ✓ Fixes failures automatically
- ✓ No permission asking
- ✓ Reports results concisely

**Now matching Claude Code's behavior!**

---

## System Prompt Section Added

```
CRITICAL - Proactive Testing:
After writing or modifying code, AUTOMATICALLY run tests without asking permission!

When to run tests (do this automatically):
1. After writing new functions/classes
2. After modifying existing code
3. After fixing bugs
4. Before committing code
5. When user requests changes to tested code

DO NOT ask "Should I run the tests?" or "Would you like me to test this?"
Just run them automatically!

Test commands by project type:
- Python: pytest, python -m pytest, pytest tests/
- Node.js: npm test, npm run test, yarn test
- Rust: cargo test
- Go: go test ./...
- Generic: Check package.json, Makefile, or project files

What to do with test results:
- ✅ Tests pass: Report success briefly
- ❌ Tests fail: Automatically investigate and fix (don't ask permission!)
- ⚠️ Tests missing: Note it, but don't let it block progress

REMEMBER: Test automatically! Like Claude Code does. Users love not having to ask.
```

---

## Benefits

### For Users
- **Less typing**: No need to ask "can you run tests?"
- **Faster workflow**: Tests run immediately after changes
- **Confidence**: Know your code works right away
- **No forgotten tests**: Can't forget to test when it's automatic

### For Code Quality
- **Catch bugs earlier**: Tests run on every change
- **Prevent regressions**: Every modification is tested
- **Maintain quality**: Tests must pass before moving on
- **Better coverage**: Tests run more frequently

### For UX
- **Matches Claude Code**: Familiar behavior for users
- **Professional**: Feels like working with a senior developer
- **Proactive**: Anticipates what users want
- **Reliable**: Consistent testing behavior

---

## Testing Philosophy

Athena's testing approach follows these principles:

1. **Test First, Report After**
   - Run tests before saying "done"
   - Report results as part of the completion message
   - Don't announce you're about to test, just test

2. **Fix Failures Automatically**
   - If tests fail, investigate and fix immediately
   - Don't ask permission to fix test failures
   - Only escalate if you can't fix after 2-3 attempts

3. **Be Concise**
   - "Fixed! Tests passing ✓" is better than a paragraph
   - Show test count if it's helpful: "All 47 tests passing ✓"
   - Only show detailed output if tests fail

4. **Respect Project Conventions**
   - Use the project's test command (npm test, pytest, etc.)
   - Run specific test files when relevant (test_auth.py for auth changes)
   - Run full suite for major changes

5. **Don't Block on Missing Tests**
   - Note if tests are missing
   - Don't let missing tests stop progress
   - Suggest adding tests but don't require it

---

## Edge Cases

### No Test Framework Installed

```
User: "Fix the bug in utils.py"

Athena: [Fixes bug]
Athena: [Attempts: pytest]
Athena: Error: pytest not found
Athena: "Fixed the bug! (Note: pytest not installed, couldn't run tests)"
```

**Result**: Completes the task, notes the issue.

### Tests Take Long Time

```
User: "Update the CSS in header.css"

Athena: [Updates CSS]
Athena: [Runs: npm test]
(Takes 45 seconds...)
Athena: "Updated header CSS! All 234 tests passing ✓ (took 45s)"
```

**Result**: Still runs tests, just notes they were slow.

### Tests Fail and Can't Fix

```
User: "Refactor the authentication system"

Athena: [Refactors]
Athena: [Runs tests] → 3 failures
Athena: [Attempts fix #1] [Runs tests] → Still 2 failures
Athena: [Attempts fix #2] [Runs tests] → Still 1 failure
Athena: [Attempts fix #3] [Runs tests] → Still 1 failure
Athena: "Refactored authentication system. Note: 1 test still failing in
        test_oauth.py - the test might need updating for the new flow.
        Here's the error: [shows error]"
```

**Result**: Tries multiple times, then reports and explains.

---

## Comparison to Other Tools

| Tool | Auto-test | Auto-fix | No asking |
|------|-----------|----------|-----------|
| **Claude Code** | ✓ | ✓ | ✓ |
| **Athena (now)** | ✓ | ✓ | ✓ |
| **GitHub Copilot** | ✗ | ✗ | ✗ |
| **Cursor** | ⚠️ | ⚠️ | ⚠️ |
| **Aider** | ⚠️ | ✗ | ⚠️ |

(✓ = Yes, ✗ = No, ⚠️ = Sometimes/Depends)

---

## Future Enhancements

Potential improvements to consider:

1. **Test Coverage Reports**
   - Show coverage percentage after tests
   - Identify untested code
   - Suggest areas that need tests

2. **Performance Benchmarks**
   - Run benchmarks on performance-critical code
   - Report if changes made things faster/slower
   - Warn about significant performance regressions

3. **Test Generation**
   - Auto-generate tests for new functions
   - Use AI to write comprehensive test cases
   - Ensure new code is always tested

4. **Continuous Monitoring**
   - Watch for file changes and auto-test
   - Run tests in background while user types
   - Show live test status indicator

5. **Smart Test Selection**
   - Only run tests affected by changes
   - Use test impact analysis
   - Run full suite periodically

---

## Summary

**What**: Athena now automatically runs tests after code changes

**Why**: Matches Claude Code's behavior that users love

**How**: Added "CRITICAL - Proactive Testing" section to system prompt

**Result**: Faster workflow, better code quality, happier users

**Key Principle**: Test automatically, fix failures automatically, don't ask permission!

---

## Try It Out

Test the new behavior:

```bash
# Example 1: Fix a bug
User: "Fix the off-by-one error in calculate_age"
# Watch Athena automatically run tests!

# Example 2: Add a feature
User: "Add email validation to the signup form"
# Tests run automatically after the change

# Example 3: Refactor
User: "Simplify the error handling in api.py"
# Tests verify nothing broke during refactoring
```

**You'll never have to ask "can you run the tests?" again!** 🎉

---

Generated with [Athena AI](https://github.com/jdpsl/Athena)
