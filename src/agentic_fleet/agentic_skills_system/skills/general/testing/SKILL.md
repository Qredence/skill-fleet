---
name: general-testing
description: Generic test task that exercises communication, reasoning, and state‑management,
  optionally integrating external tools.
metadata:
  skill_id: general/testing
---

# Generic Test Skill

**Skill ID**: `general/testing/generic_test`  
**Description**: Generic test task that exercises communication, reasoning, and state‑management, optionally integrating external tools.  
**Inputs**: `[]` (no explicit inputs)  
**Outputs**: `["test_report"]`  
**Category**: `testing`  

## Capabilities
- `communicate_test_status` – Announces the current test status to the user or downstream components.
- `perform_reasoning_steps` – Generates a sequence of logical steps required to execute the test.
- `manage_test_state` – Persists and updates the internal state of the test execution.
- `integrate_external_tool` – Invokes an external testing framework via the MCP interface.

## Configuration
The skill ships with an empty `config.json`. Users can extend this file to provide custom configuration for the external tool (e.g., tool name, arguments, environment variables).

## Test Cases
The skill includes a sample test case defined in `test_cases/example_test.yaml`:

```yaml
steps:
  - perform_reasoning_steps
  - communicate_test_status
  - manage_test_state
  - integrate_external_tool
outputs: [ "test_report" ]
```

Running this test case will produce a `test_report` artifact containing the results of the executed steps.

---

### Capability Implementation Details

| Capability | Implementation Sketch |
|------------|-----------------------|
| `communicate_test_status` | Emits a status message via the communication channel, indicating the current phase (e.g., “Starting test”, “Step 1 completed”). |
| `perform_reasoning_steps` | Generates a deterministic list of logical steps based on predefined heuristics or user‑provided metadata. |
| `manage_test_state` | Maintains a JSON state object (`{ "step": 0, "status": "pending", "results": [] }`) that is updated after each step. |
| `integrate_external_tool` | Calls the MCP endpoint `mcp_capabilities/tool_integration` with the configured tool spec, passing the current state and receiving a result payload to store in `test_report`. |

---

### Full File Listing

- `skill.yaml` – Metadata and capability declaration (see above).  
- `README.md` – Documentation (the text you are reading).  
- `config.json` – Optional configuration for external tool integration.  
- `test_cases/example_test.yaml` – Example test definition.  

---