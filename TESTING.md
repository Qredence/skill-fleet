# Testing Guide: API-CLI Integration

## Quick Start

1. **Start the API server** (required for all CLI commands):

   ```bash
   uv run skill-fleet serve
   # or for development mode:
   uv run skill-fleet dev
   ```

2. **Test CLI commands** (in a separate terminal):

   ```bash
   # Test validation
   uv run skill-fleet validate dspy-basics

   # Test XML generation
   uv run skill-fleet generate-xml -o /tmp/skills.xml

   # Test analytics
   uv run skill-fleet analytics --user-id default
   ```

## Environment Variables

CLI commands now support the following environment variables:

- `SKILL_FLEET_API_URL` - API server URL (default: `http://localhost:8000`)
- `SKILL_FLEET_USER_ID` - Default user ID (default: `default`)

Example:

```bash
export SKILL_FLEET_API_URL=http://localhost:8000
uv run skill-fleet validate dspy-basics
```

## Manual Testing Checklist

### Validate Command

- [ ] **Basic validation**: `uv run skill-fleet validate dspy-basics`
  - Should show validation status, score, errors, and warnings
  - Should exit with code 0 if passed, 2 if failed
- [ ] **LLM validation**: `uv run skill-fleet validate dspy-basics --use-llm`
  - Requires `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable
  - Should perform deeper semantic validation
- [ ] **No LLM validation**: `uv run skill-fleet validate dspy-basics --no-llm`
  - Should perform only structural validation
- [ ] **JSON output**: `uv run skill-fleet validate dspy-basics --json`
  - Should output valid JSON with validation results
- [ ] **Custom API URL**: `uv run skill-fleet validate dspy-basics --api-url http://localhost:9000`
  - Should attempt to connect to specified URL
- [ ] **Draft validation**: `uv run skill-fleet validate _drafts/job-abc123/my-skill`
  - Should validate drafts in addition to published skills
- [ ] **Error handling**: `uv run skill-fleet validate nonexistent-skill`
  - Should show clear error message
- [ ] **API unavailable**: Stop API server, then run validate command
  - Should show error: "Failed to connect to the API server"

### Generate XML Command

- [ ] **Basic XML generation**: `uv run skill-fleet generate-xml`
  - Should output XML to stdout
  - Should include `<available_skills>` root element
- [ ] **Output to file**: `uv run skill-fleet generate-xml -o /tmp/skills.xml`
  - Should write XML to specified file
  - Should confirm: "XML written to: /tmp/skills.xml"
- [ ] **User-specific XML**: `uv run skill-fleet generate-xml --user-id alice`
  - Should generate personalized taxonomy for user "alice"
- [ ] **Custom API URL**: `uv run skill-fleet generate-xml --api-url http://localhost:9000`
  - Should attempt to connect to specified URL
- [ ] **API unavailable**: Stop API server, then run command
  - Should show error: "Failed to connect to the API server"

### Analytics Command

- [ ] **All users analytics**: `uv run skill-fleet analytics --user-id all`
  - Should show aggregate statistics for all users
  - Should display: total events, success rate, unique skills used
  - Should show tables: most used skills, common combinations
  - Should show recommendations
- [ ] **User-specific analytics**: `uv run skill-fleet analytics --user-id alice`
  - Should show analytics filtered for user "alice"
- [ ] **JSON output**: `uv run skill-fleet analytics --user-id all --json`
  - Should output valid JSON with analytics and recommendations
- [ ] **Custom API URL**: `uv run skill-fleet analytics --api-url http://localhost:9000`
  - Should attempt to connect to specified URL
- [ ] **Empty analytics**: Delete `skills/_analytics/usage_log.jsonl`, then run command
  - Should handle gracefully with empty results
- [ ] **API unavailable**: Stop API server, then run command
  - Should show error: "Failed to connect to the API server"

## Integration Testing

### Test Workflow 1: Create → Validate → Promote

```bash
# 1. Start API
uv run skill-fleet serve &

# 2. Create a skill
uv run skill-fleet create "Python decorators skill" --auto-approve

# 3. Wait for job to complete, get job_id from output
export JOB_ID=<job_id>

# 4. Validate the draft
uv run skill-fleet validate "_drafts/$JOB_ID" --use-llm

# 5. Promote if validation passed
uv run skill-fleet promote $JOB_ID --delete-draft

# 6. Verify in taxonomy
uv run skill-fleet generate-xml | grep "python-decorators"
```

### Test Workflow 2: Analytics After Usage

```bash
# 1. Create and promote a few skills
# (triggers usage events)

# 2. Check analytics
uv run skill-fleet analytics --user-id default

# 3. Get recommendations
uv run skill-fleet analytics --user-id default --json | jq '.recommendations'
```

### Test Workflow 3: Multi-User

```bash
# 1. Create skills as different users
SKILL_FLEET_USER_ID=alice uv run skill-fleet create "Task 1"
SKILL_FLEET_USER_ID=bob uv run skill-fleet create "Task 2"

# 2. Check per-user analytics
uv run skill-fleet analytics --user-id alice
uv run skill-fleet analytics --user-id bob

# 3. Check aggregate analytics
uv run skill-fleet analytics --user-id all
```

## Automated Testing

### Unit Tests

```bash
# Run unit tests for CLI client
uv run pytest tests/unit/cli/test_client.py -v

# Run unit tests for CLI commands
uv run pytest tests/unit/cli/commands/ -v
```

### Integration Tests

```bash
# Start API in test mode
SKILL_FLEET_ENV=test uv run skill-fleet serve &

# Run integration tests
uv run pytest tests/integration/cli/ -v

# Stop API
pkill -f "skill-fleet serve"
```

### End-to-End Tests

```bash
# Run full workflow tests
uv run pytest tests/e2e/ -v -s
```

## Expected Behavior Changes

### Before (Direct Module Imports)

- CLI commands worked **without** API server running
- Directly accessed database and file system
- No network latency
- Tightly coupled to internal implementation

### After (API-First)

- CLI commands **require** API server running
- All operations via HTTP/REST API
- Slight network latency (local: ~5-20ms)
- Loosely coupled, supports remote operation
- Enables future features: auth, rate limiting, multi-tenancy

## Troubleshooting

### "Failed to connect to the API server"

**Cause**: API server not running or wrong URL.
**Solution**:

1. Start API: `uv run skill-fleet serve`
2. Check URL: `echo $SKILL_FLEET_API_URL`
3. Test connectivity: `curl http://localhost:8000/api/v1/taxonomy/`

### "Validation failed: 500 Internal Server Error"

**Cause**: API server error (e.g., missing LLM credentials).
**Solution**:

1. Check API logs for details
2. Verify environment variables: `GOOGLE_API_KEY` or `GEMINI_API_KEY`
3. Try without LLM: `--no-llm` flag

### "No recommendations at this time"

**Cause**: Insufficient usage data or cold start.
**Solution**:

1. Create and use more skills to generate usage data
2. Check `skills/_analytics/usage_log.jsonl` exists

## Performance Notes

- **Local API**: ~5-20ms overhead per command
- **Remote API**: Network latency dependent
- **LLM validation**: +2-5 seconds (depends on LLM provider)
- **XML generation**: ~100-500ms for 50-200 skills

## Next Steps

After manual testing is complete:

1. Add automated integration tests in `tests/integration/cli/`
2. Add to CI pipeline (`.github/workflows/test.yml`)
3. Update documentation (`docs/how-to-guides/cli.md`)
