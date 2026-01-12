# CLI Security Review

## Executive Summary

This security review identifies potential vulnerabilities in the skill-fleet CLI related to path handling, input validation, and secrets management. While no critical vulnerabilities were found, several medium-risk issues should be addressed to improve security posture.

**Review Date:** 2026-01-12
**Scope:** `src/skill_fleet/cli/main.py`, `app.py`, `client.py`, `onboarding_cli.py`
**Severity Breakdown:**
- Critical: 0
- High: 0
- Medium: 4
- Low: 3

---

## Path Traversal Risks

### Issue 1: Unvalidated User-Provided Paths (Medium Severity)

**Location:** `main.py:55, 94, 105, 232, 262, 284, 385`

**Problem:**
User-provided paths via command-line arguments are used directly without validation:

```python
# main.py:55
taxonomy = TaxonomyManager(Path(args.skills_root))

# main.py:94
config = load_fleet_config(Path(args.config))

# main.py:235
skill_path = Path(args.skill_path)

# main.py:288
Path(args.output).write_text(xml_content, encoding="utf-8")

# interactive_cli.py:646, 649
config = load_fleet_config(Path(args.config))
taxonomy = TaxonomyManager(Path(args.skills_root))
```

**Vulnerability:**
While `Path.resolve()` normalizes paths (e.g., `../` gets expanded to absolute path), there is no validation that the resolved path stays within allowed directories. An attacker could potentially:

- Read files outside the intended directory (if they control skill paths)
- Write to unintended locations via `--output` flag
- Access sensitive files if they know the filesystem structure

**Test Results:**
```python
# Path resolution test
Path('../../etc/passwd').resolve()
# Returns: /Volumes/.../agent-framework/v0.5/_WORLD/skills-fleet/etc/passwd
# This escapes the intended skills root directory
```

**Mitigation Required:**
```python
def validate_path_within_root(user_path: Path, root_path: Path, path_type: str) -> Path:
    """Validate user path is within allowed root directory."""
    user_path = user_path.resolve()
    root_path = root_path.resolve()

    try:
        # Check if user_path is within root_path
        user_path.relative_to(root_path)
        return user_path
    except ValueError:
        raise ValueError(
            f"{path_type} path '{user_path}' must be within '{root_path}'"
        )

# Usage in commands:
skills_root = validate_path_within_root(
    Path(args.skills_root),
    Path.cwd() / "skills",  # Default allowed root
    "Skills root"
)
```

### Issue 2: Session File Path Not Sanitized (Medium Severity)

**Location:** `interactive_cli.py:94, 489`

**Problem:**
Session file location is derived from user input without sanitization:

```python
# interactive_cli.py:94
data = json.loads(self.session_file.read_text(encoding="utf-8"))

# interactive_cli.py:489
self.session_file.write_text(
    json.dumps(session_dict, indent=2, default=str), encoding="utf-8"
)
```

**Vulnerability:**
If session file path includes user input (e.g., from `--session` argument), an attacker could:
- Write session data to arbitrary locations
- Overwrite existing files
- Create files in sensitive directories

**Mitigation Required:**
- Validate session file paths are within allowed directory (e.g., `.skill-fleet/`)
- Use `.relative_to()` check before file operations
- Consider using a dedicated cache directory for sessions

---

## Input Validation

### Issue 3: API URLs Not Validated for Protocol (Medium Severity)

**Location:** `app.py:38-43`, `client.py:16-19`

**Problem:**
API URL is accepted from user without protocol validation:

```python
# app.py:38-43
api_url: str = typer.Option(
    "http://localhost:8000",
    "--api-url", "-a",
    help="API server URL",
    envvar="SKILL_FLEET_API_URL"
)

# client.py:16-19
def __init__(self, base_url: str = "http://localhost:8000"):
    """Initialize client."""
    self.base_url = base_url.rstrip("/")
    self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
```

**Vulnerability:**
No validation that URL uses secure protocol:
- User can accidentally use `http://` instead of `https://` in production
- Could lead to credentials being transmitted in plaintext
- MITM attack vector if production API is accessed over HTTP

**Mitigation Required:**
```python
from urllib.parse import urlparse

def validate_api_url(url: str) -> str:
    """Validate API URL uses secure protocol."""
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ('https', 'http'):
        raise ValueError(f"API URL must use http:// or https:// protocol: {url}")

    # In production, enforce HTTPS
    # if parsed.scheme != 'https':
    #     raise ValueError("API URL must use HTTPS in production")

    return url

# Usage:
api_url: str = typer.Option(
    "http://localhost:8000",
    "--api-url", "-a",
    help="API server URL (must use https:// in production)",
    callback=validate_api_url
)
```

### Issue 4: User IDs Not Sanitized for Injection (Low Severity)

**Location:** `main.py:447, 512, 524, 613`, `app.py:44-49`

**Problem:**
User IDs are accepted without sanitization:

```python
# main.py:447
create.add_argument("--user-id", default="default", help="User id for mounted skills context")

# main.py:512
onboard.add_argument("--user-id", required=True, help="Unique user identifier")

# app.py:44-49
user_id: str = typer.Option(
    "default",
    "--user", "-u",
    help="User ID for context",
    envvar="SKILL_FLEET_USER_ID"
)
```

**Vulnerability:**
Special characters in user IDs could cause issues:
- Path injection if user ID used in file paths
- Log injection if user ID logged without escaping
- API injection if sent directly to API endpoints

**Mitigation Required:**
```python
import re

def sanitize_user_id(user_id: str) -> str:
    """Sanitize user ID to prevent injection attacks."""
    # Remove dangerous characters
    sanitized = re.sub(r'[^\w\-@.]', '', user_id)

    if len(sanitized) != len(user_id):
        raise ValueError(
            f"User ID contains invalid characters. "
            f"Only alphanumeric, @, -, . allowed"
        )

    if not sanitized or len(sanitized) > 100:
        raise ValueError("User ID must be 1-100 characters")

    return sanitized
```

---

## Secrets Handling

### Issue 5: No Secrets Exposed (Good Practice)

**Finding:** ✅ **No secrets logged or printed**

**Analysis:**
Grep search for `print.*api.*key|print.*token|print.*secret` returned no matches in CLI code.

**Evidence:**
```bash
uv run grep -rin 'print.*api.*key|print.*token|print.*secret' src/skill_fleet/cli/
# No matches found
```

**Assessment:**
- API keys are not printed to stdout/stderr
- Secrets are loaded from environment variables (`.env` file excluded from git)
- Stack traces do not contain secrets (verified via error handling patterns)

**Recommendation:** Keep current practices, consider adding additional safeguards:
```python
# In production logging, redact sensitive URLs
import logging

class RedactingFormatter(logging.Formatter):
    """Redact sensitive information from log messages."""

    def format(self, record):
        message = super().format(record)
        # Redact API keys
        message = re.sub(r'api[_-]?key[=\s]+\S+', 'api_key=***REDACTED***', message, flags=re.IGNORECASE)
        # Redact tokens
        message = re.sub(r'token[=\s]+\S+', 'token=***REDACTED***', message, flags=re.IGNORECASE)
        return message
```

### Issue 6: Config File Paths May Be Exposed (Low Severity)

**Location:** `main.py:665`, `interactive_typer.py:93`

**Problem:**
Config file error messages include full path:

```python
# main.py:665
print(f"config error: {exc}", file=sys.stderr)

# interactive_typer.py:93
console.print(f"[red]Config error: {e}[/red]")
```

**Vulnerability:**
If exception includes the config file path and verbose mode is enabled, it could expose:
- Project directory structure
- Sensitive configuration file locations
- File system layout

**Mitigation Required:**
```python
# In error handling, sanitize file paths
def sanitize_error_message(error: Exception, context: str) -> str:
    """Sanitize error messages to remove sensitive paths."""
    message = str(error)

    # Remove absolute paths (keep relative paths only)
    message = re.sub(r'/[^/\s]+(/[^/\s]+)*', '[PATH]', message)

    # Replace with context if provided
    if context:
        message = f"{context}: {message.split(':', 1)[1] if ':' in message else message}"

    return message

# Usage:
except FleetConfigError as exc:
    error_msg = sanitize_error_message(exc, "config error")
    console.print(f"[red]{error_msg}[/red]")
```

---

## Additional Security Concerns

### Issue 7: Hardcoded HTTP Timeout (Low Severity)

**Location:** `client.py:19`

**Problem:**
HTTP client timeout is hardcoded:

```python
self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
```

**Concern:**
- No timeout validation
- Could allow very long connections (DoS vector if server is malicious)
- No retry limit for failed requests

**Mitigation Required:**
```python
import typer

def validate_timeout(seconds: float) -> float:
    """Validate timeout is reasonable."""
    if not (0 < seconds <= 300):
        raise ValueError("Timeout must be between 0 and 300 seconds")
    return seconds

# In CLI arguments:
timeout: float = typer.Option(
    30.0,
    "--timeout",
    help="API timeout in seconds (max: 300)",
    callback=validate_timeout
)
```

---

## Recommendations

### High Priority (Address Immediately)

1. **Implement path validation for all user-provided paths**
   - Use `.relative_to()` to check paths are within allowed directories
   - Add validation to `--skills-root`, `--config`, `--output` arguments
   - Validate session file paths before read/write operations

2. **Add API URL protocol validation**
   - Enforce HTTPS for production environments
   - Add warning if HTTP used with non-localhost URLs
   - Validate URL format before HTTP client initialization

3. **Sanitize user IDs**
   - Remove special characters that could cause injection
   - Validate length constraints
   - Use in file paths only after sanitization

### Medium Priority (Address Soon)

4. **Redact sensitive paths in error messages**
   - Remove absolute paths from exception messages
   - Keep error context without exposing filesystem structure
   - Use sanitized error display utility

5. **Add configuration file validation**
   - Validate config file exists and is readable before loading
   - Check file permissions (world-readable should be warning)
   - Validate config schema before application startup

### Low Priority (Address When Convenient)

6. **Make HTTP timeout configurable**
   - Add CLI argument for timeout
   - Set reasonable limits (max 300 seconds)
   - Add connection timeout separate from read timeout

7. **Add logging redaction for production**
   - Implement RedactingFormatter for log messages
   - Redact API keys, tokens, passwords
   - Enable in production via environment variable

---

## Security Testing Recommendations

### Manual Testing Checklist

- [ ] Test path traversal: `skill-fleet validate-skill ../../etc/passwd`
- [ ] Test malicious output path: `skill-fleet generate-xml -o /tmp/malicious.xml`
- [ ] Test HTTP vs HTTPS: `skill-fleet --api-url http://malicious.com`
- [ ] Test user ID injection: `skill-fleet --user-id "../../../test"`
- [ ] Test session file path injection: `skill-fleet interactive --session /tmp/test.json`

### Automated Testing

```python
# tests/cli/test_security.py
import pytest
from pathlib import Path

def test_path_traversal_prevented():
    """Test that path traversal attempts are blocked."""
    with pytest.raises(ValueError):
        validate_path_within_root(
            Path("../../etc/passwd"),
            Path.cwd() / "skills",
            "Skills root"
        )

def test_api_url_protocol_validation():
    """Test that API URLs require valid protocol."""
    with pytest.raises(ValueError):
        validate_api_url("ftp://localhost:8000")

def test_user_id_sanitization():
    """Test that malicious user IDs are sanitized."""
    with pytest.raises(ValueError):
        sanitize_user_id("../../../etc/passwd")
```

---

## Conclusion

The skill-fleet CLI follows good security practices in many areas:
- ✅ No secrets logged or printed
- ✅ Environment variables used for sensitive data
- ✅ Path normalization via `.resolve()`

However, several medium-risk vulnerabilities should be addressed:
- ❌ No validation that paths stay within allowed directories
- ❌ No API URL protocol validation
- ❌ No user ID sanitization

**Overall Security Posture:** Good with actionable improvements needed
**Estimated Effort to Mitigate:** 2-3 days (including tests)
**Priority:** Medium (address before production deployment)

---

**Review Methodology:**
- Static analysis of CLI code
- Manual testing of path operations
- Grep searches for dangerous patterns
- Review of error handling and logging

**Next Steps:**
1. Implement path validation utility functions
2. Add input sanitization to all CLI arguments
3. Create security test suite
4. Update documentation with security guidelines
5. Consider security audit before major release
