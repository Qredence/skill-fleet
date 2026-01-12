# CLI Error Handling Review

## Issues Found

### Bare Except Clauses
- `interactive_cli.py:76` - Generic `except Exception:` catches all errors
- `interactive_cli.py:487` - Generic `except Exception:` catches all errors
- `interactive_cli.py:93` - Generic `except Exception:` catches all errors
- `interactive_cli.py:123` - Generic `except Exception:` catches all errors
- `interactive_typer.py:138` - Generic `except Exception:` catches all errors
- `interactive_typer.py:243` - Generic `except Exception:` catches all errors
- `main.py:344` - Empty except clause (bare except)
- `chat.py:96` - Generic `except Exception:` catches all errors
- `create.py:88` - Generic `except Exception:` catches all errors
- `list_skills.py:18` - Generic `except Exception:` catches all errors

### Missing Specific Exceptions
- FleetConfigError handling exists but other config errors not caught
- HTTP errors from httpx not differentiated (timeouts vs connection errors)
- File I/O errors not explicitly handled (session save/load)
- JSON parsing errors not specifically caught
- JSON serialization errors not specifically caught
- Task loading errors not differentiated

### Inconsistent Error Reporting
- Some use `print(..., file=sys.stderr)` (main.py:316, 375, 379)
- Some use `console.print("[red]Error: ...[/red]")` (multiple files)
- Mix of Rich formatting and plain text for errors
- Some errors use logger.exception() (interactive_cli.py:263)
- Some use logger.warning() (interactive_cli.py:493)
- Inconsistent capitalization: "Error:", "Config error:", "❌ Job failed"

### Missing User-Facing Messages
- "Config error" doesn't explain what to fix (interactive_typer.py:93)
- "Error during optimization" gives no actionable guidance (main.py:379)
- HTTP errors don't show retry options
- Generic "Error: {e}" messages don't provide context or next steps
- JSON load errors don't explain what format is expected
- Session save/load errors don't suggest recovery options

### Resource Cleanup
- Finally blocks present in all try blocks (good practice)
- HTTP client cleanup consistent across async commands
- Session files may not be saved on crashes
- Main.py line 180 has bare except with finally (client.py:180)
- Some async functions properly close connections in finally blocks

### Exit Code Inconsistency
- main.py returns 1 for optimization errors
- main.py returns 2 for config errors and missing files
- Other commands may use different exit codes
- No standardized exit code scheme documented

## Recommendations

1. **Replace bare `except Exception` with specific exception types**
   - Catch specific errors: ValueError, TypeError, KeyError, etc.
   - Keep Exception only as fallback for truly unexpected errors
   - Log full stack trace for unexpected exceptions

2. **Create consistent error message format using Rich**
   - Standardize on `console.print("[red]Error: ...[/red]")` pattern
   - Use `[yellow]` for warnings
   - Add context and actionable suggestions to all error messages
   - Include file paths and line numbers where appropriate

3. **Add error recovery suggestions**
   - "Run with --help" for command usage errors
   - "Check configuration file at {path}" for config errors
   - "Retry with --verbose for more details"
   - "See documentation at URL" for complex errors

4. **Ensure all async functions have proper cleanup in finally blocks**
   - Close HTTP connections in finally
   - Save state/session data on error when possible
   - Clean up temporary files
   - Ensure database connections are closed

5. **Log full stack traces for debugging**
   - Use `logger.exception()` for unexpected errors
   - Add `LOG_LEVEL` env var to control verbosity
   - Keep detailed logs separate from user-facing messages
   - Include timestamps and request IDs

6. **Define custom CLI error classes for better handling**
   - `CLIConfigError` for configuration issues
   - `CLINetworkError` for HTTP/connection errors
   - `CLIValidationError` for input validation
   - `CLIStateError` for session/state management errors

7. **Standardize exit codes**
   - 0: Success
   - 1: General error
   - 2: Configuration error
   - 3: Network/connectivity error
   - 4: Validation error
   - 5: Permission error
   - Document exit code scheme in CLI reference

8. **Add HTTP error differentiation**
   - Catch specific httpx exceptions: Timeout, ConnectError, HTTPStatusError
   - Retry for transient errors (timeouts, connection errors)
   - Show status code and response body for HTTP errors
   - Suggest retry strategies based on error type

9. **Improve session error handling**
   - Catch JSONDecodeError for malformed session files
   - Catch PermissionError for read/write permission issues
   - Create backup before overwriting session files
   - Suggest recovery steps when session loading fails

10. **Add validation error details**
    - Show which field failed validation
    - Provide example of valid input
    - Link to documentation for complex validation rules
    - Show line number if validating a file
