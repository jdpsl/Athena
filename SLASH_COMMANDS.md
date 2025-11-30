# Slash Commands Guide

Slash commands are custom shortcuts that expand to detailed prompts. They make common tasks faster and more consistent.

## How They Work

1. **Create** a Markdown file in `.athena/commands/`
2. **Name** it whatever you want (e.g., `review.md`)
3. **Write** your prompt template in the file
4. **Use** it by typing `/review` in Athena

When you type `/review`, Athena loads `review.md` and uses its content as the prompt.

## Example Slash Commands Included

### `/review` - Code Review
Reviews code for security, quality, and best practices.

**Usage:**
```
You: /review
[Athena reads the code and provides a detailed review]
```

**What it does:**
- Checks for security vulnerabilities (SQL injection, XSS, etc.)
- Identifies code quality issues
- Suggests improvements
- Highlights what's done well

---

### `/explain` - Code Explanation
Provides a detailed explanation of how code works.

**Usage:**
```
You: Read main.py then /explain
[Athena explains the code step-by-step]
```

**What it does:**
- High-level overview
- Step-by-step walkthrough
- Dependencies and interactions
- Usage examples
- Potential issues

---

### `/test` - Generate Tests
Creates comprehensive test suites.

**Usage:**
```
You: /test for the authentication module
[Athena generates unit tests]
```

**What it does:**
- Generates unit tests
- Covers edge cases
- Tests error handling
- Uses appropriate testing framework
- Follows best practices

---

### `/debug` - Debug Assistance
Helps troubleshoot issues.

**Usage:**
```
You: /debug - getting TypeError on line 42
[Athena analyzes and helps fix the issue]
```

**What it does:**
- Analyzes the error
- Traces execution path
- Identifies root cause
- Provides fix with explanation
- Suggests prevention strategies

---

### `/optimize` - Performance Optimization
Analyzes and improves code performance.

**Usage:**
```
You: /optimize the search function
[Athena suggests performance improvements]
```

**What it does:**
- Identifies bottlenecks
- Suggests algorithm improvements
- Recommends data structure changes
- Provides optimized code
- Explains performance gains

---

### `/document` - Generate Documentation
Creates comprehensive documentation.

**Usage:**
```
You: /document the API endpoints
[Athena generates docs]
```

**What it does:**
- Adds docstrings/comments
- Creates API documentation
- Writes README sections
- Explains architecture
- Includes examples

---

### `/refactor` - Code Refactoring
Improves code structure and quality.

**Usage:**
```
You: /refactor the user controller
[Athena refactors the code]
```

**What it does:**
- Improves code structure
- Fixes naming issues
- Removes duplication
- Applies SOLID principles
- Simplifies complex logic

---

## Real-World Usage Examples

### Example 1: Security Review
```
You: Read src/api/auth.py then /review

Athena:
I'll review the authentication code for security and quality issues.

[Reading file...]

**Security Analysis:**

🔴 CRITICAL ISSUES:
1. Password stored in plain text (line 45)
   - Risk: Complete credential exposure if DB compromised
   - Fix: Use bcrypt or argon2 for password hashing

2. SQL query uses string concatenation (line 67)
   - Risk: SQL injection vulnerability
   - Fix: Use parameterized queries

⚠️ WARNINGS:
1. JWT secret is hardcoded (line 12)
   - Should be in environment variable

...
```

### Example 2: Creating Tests
```
You: /test for the calculate_discount function

Athena:
I'll create comprehensive tests for the discount calculation.

[Creates test file...]

```python
import pytest
from shop.pricing import calculate_discount

def test_calculate_discount_valid_percentage():
    """Test discount calculation with valid percentage."""
    assert calculate_discount(100, 10) == 90
    assert calculate_discount(50, 25) == 37.5

def test_calculate_discount_zero_percent():
    """Test with 0% discount."""
    assert calculate_discount(100, 0) == 100

def test_calculate_discount_hundred_percent():
    """Test with 100% discount."""
    assert calculate_discount(100, 100) == 0

def test_calculate_discount_invalid_negative():
    """Test that negative discounts raise error."""
    with pytest.raises(ValueError):
        calculate_discount(100, -10)
...
```

### Example 3: Debugging
```
You: Getting "KeyError: 'user_id'" when I run the app. /debug

Athena:
Let me help debug the KeyError issue.

[Reading code...]

**Analysis:**
The error occurs in `process_request()` at line 89:
```python
user_id = request.data['user_id']  # ← KeyError here
```

**Root Cause:**
The code assumes 'user_id' always exists in request.data, but it may be missing.

**Fix:**
```python
# Option 1: Use .get() with default
user_id = request.data.get('user_id')
if not user_id:
    return error_response("Missing user_id")

# Option 2: Try-except
try:
    user_id = request.data['user_id']
except KeyError:
    return error_response("Missing user_id")
```

**Testing:**
Try these requests:
1. Valid: `{"user_id": 123, "data": "..."}`
2. Missing ID: `{"data": "..."}` ← should handle gracefully
...
```

## Creating Your Own Slash Commands

### Simple Command
`.athena/commands/hello.md`:
```markdown
Say hello to the user in a friendly way and offer to help with coding tasks.
```

Usage: `/hello` → Gets friendly greeting

### Command with Context
`.athena/commands/security-scan.md`:
```markdown
Perform a comprehensive security scan of the entire codebase.

Search for:
- Hardcoded credentials or API keys
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure dependencies
- Authentication bypasses
- Unvalidated inputs

Use the Grep and Read tools to scan all files.
Provide a detailed security report.
```

Usage: `/security-scan` → Full security audit

### Command with Arguments
When you use a slash command with arguments:
```
/review src/auth.py
```

Athena expands it to:
```
[Content of review.md]

Arguments: src/auth.py
```

Then Athena uses both the command content and the arguments.

## Best Practices

### 1. Be Specific
❌ **Bad:** "Review the code"
✅ **Good:** "Review for security vulnerabilities, code quality, and performance"

### 2. Provide Structure
❌ **Bad:** "Explain the code"
✅ **Good:**
```markdown
Explain including:
- Overview
- How it works step-by-step
- Dependencies
- Usage examples
```

### 3. Include Examples
Tell Athena what format you want:
```markdown
Provide examples in this format:
```python
# Example usage
result = my_function(param1, param2)
print(result)  # Output: expected_value
```
```

### 4. Specify Tools
If you want specific tools used:
```markdown
Use the Glob tool to find all Python files,
then use Grep to search for TODO comments.
```

### 5. Set Expectations
```markdown
Generate at least 10 test cases covering:
- Happy path (3 tests)
- Edge cases (4 tests)
- Error cases (3 tests)
```

## Advanced Examples

### Project-Specific Commands
`.athena/commands/api-review.md`:
```markdown
Review this API endpoint according to our company standards:

**Required Checks:**
- Uses our standard error response format
- Includes rate limiting decorator
- Has comprehensive OpenAPI documentation
- Validates input with Pydantic models
- Returns proper HTTP status codes
- Includes unit and integration tests

**Our Error Format:**
```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {}
}
```

Check against our internal API guidelines document.
```

### Workflow Commands
`.athena/commands/feature.md`:
```markdown
Help me implement a new feature following our workflow:

1. **Planning**: Create a detailed implementation plan
2. **Code**: Write the feature code
3. **Tests**: Generate comprehensive tests
4. **Docs**: Update documentation
5. **Review**: Self-review for issues

Use TodoWrite to track progress through these steps.
```

## Command Organization

Organize commands by purpose:
```
.athena/commands/
├── review.md           # Code review
├── security.md         # Security scan
├── test.md            # Generate tests
├── debug.md           # Debug help
├── optimize.md        # Performance
├── document.md        # Documentation
├── explain.md         # Explanations
├── refactor.md        # Refactoring
├── api-review.md      # API-specific review
├── feature.md         # Feature workflow
└── onboard.md         # Codebase onboarding
```

## Tips

1. **Chain Commands**: You can use multiple commands
   ```
   /review then /optimize then /test
   ```

2. **Combine with Tools**: Commands work with tool mentions
   ```
   Read src/app.py then /review
   ```

3. **Iterate**: Start simple, refine based on results
   - First version: Basic prompt
   - After testing: Add specifics
   - Final version: Detailed, structured

4. **Share Commands**: Great commands can be shared with your team
   - Check them into version control
   - Everyone gets consistent results

5. **Update Regularly**: As your needs change, update commands
   - Add new checks
   - Remove outdated patterns
   - Improve clarity

## Summary

Slash commands are **powerful shortcuts** that:
- ✅ Save typing
- ✅ Ensure consistency
- ✅ Encode best practices
- ✅ Work with sub-agents
- ✅ Customize Athena for your workflow

Create commands for tasks you do repeatedly, and Athena becomes perfectly tailored to your needs!
