---
name: practices-code-quality-analysis
description: Analyzes Python source code to evaluate overall quality by combining
  static analysis, code review insights, testing outcomes, code metrics, and style
  checking.
metadata:
  skill_id: technical_skills/programming/practices/code_quality_analysis
  version: '1.0'
---

# Code Quality Analysis Skill  

**Purpose**  
This skill orchestrates a suite of complementary quality‑checking practices—static analysis, code review heuristics, missing‑code metrics, style enforcement, and test coverage—to produce a unified quality score and detailed report for a Python project. It serves as the central entry point for CI/CD integration, local developer dashboards, and automated gatekeeping.

---  

## Directory Layout  

```
technical_skills/programming/practices/code_quality_analysis/
├─ README.md                 # Overview, quick‑start, API reference
├─ setup.py                  # Package metadata & entry‑point definition
├─ requirements.txt          # Runtime dependencies
│
├─ metrics/                  # Individual metric implementations
│   ├─ complexity.py
│   ├─ maintainability.py
│   ├─ halstead.py
│   └─ __init__.py
│
├─ style/                    # Style checking utilities
│   └─ checker.py
│
├─ coverage/                 # Coverage evaluation wrapper
│   └─ evaluator.py
│
├─ score/                    # Composite scoring logic
│   └─ composite.py
│
└─ tests/                    # Unit tests for each component
    ├─ test_complexity.py
    ├─ test_maintainability.py
    ├─ test_halstead.py
    ├─ test_style.py
    ├─ test_coverage.py
    └─ test_composite.py
```

### Key Files  

| File | Role |
|------|------|
| `README.md` | High‑level description, installation, CLI usage, contribution guide. |
| `setup.py` | Declares package name `code_quality_analysis`, installs dependencies, registers console script `cqac`. |
| `requirements.txt` | Lists `radon`, `flake8`, `pylint`, `coverage`, `jsonschema`, etc. |
| `metrics/*.py` | Stand‑alone functions/classes that compute cyclomatic complexity, maintainability index, Halstead metrics, etc. |
| `style/checker.py` | Wrapper around `flake8`/`pylint` that returns a structured JSON report. |
| `coverage/evaluator.py` | Executes test suite via `coverage` and returns line/branch coverage percentages. |
| `score/composite.py` | Takes raw metric dicts, normalizes them, applies weighted scoring, and emits a final JSON report. |
| `tests/*.py` | Pytest suite validating each metric and the composite output against known fixtures. |

---  

## Core Capabilities  

1. **Metric Collection** – Executes all sub‑metrics and aggregates results.  
2. **Normalization & Weighting** – Maps raw scores to a 0‑100 scale using configurable weights.  
3. **Composite Scoring** – Produces a single quality score and a detailed breakdown.  
4. **CLI Interface** – `cqac analyze <path>` runs the full pipeline and prints JSON or human‑readable summary.  
5. **Programmable API** – `analyze(path: str, config: dict) -> dict` can be imported and used in custom automation.  
6. **Extensibility Hooks** – Plugin points for adding new metrics or adjusting weights without code changes.  

---  

## API Overview  

```python
from code_quality_analysis.score.composite import analyze

result = analyze(
    project_path="/path/to/project",
    config={
        "weights": {"complexity": 0.25, "maintainability": 0.20,
                    "halstead": 0.15, "style": 0.20, "coverage": 0.20},
        "thresholds": {"high": 75, "medium": 50}
    }
)
```

`result` contains:  

```json
{
  "overall_score": 68,
  "breakdown": {
    "complexity": {"score": 72, "details": {...}},
    "maintainability": {"score": 65, "details": {...}},
    ...
  },
  "report_path": "quality_report.json"
}
```

---  

## CLI Usage  

```bash
$ cqac --help
Usage: cqac [OPTIONS] COMMAND [ARGS]...

  Analyze a Python project for overall code quality.

Options:
  -c, --config PATH      Path to a YAML config defining weights and thresholds.
  -j, --json             Output raw JSON instead of pretty table.
  -h, --help             Show this message and exit.

Commands:
  analyze   Run the full quality analysis on a project directory.
```

Running `cqac analyze .` in a project root will output a summary such as:

```
Overall Quality Score: 71/100
  Complexity      : 78  (good)
  Maintainability : 64  (caution)
  Halstead        : 66  (average)
  Style           : 80  (excellent)
  Coverage        : 85  (good)
```

---  

## Extending the Skill  

* Add new metric modules under `metrics/` and expose them via `metrics.__init__`.  
* Extend `score/composite.py` to incorporate the new metric key.  
* Update `setup.py` entry points if new CLI flags are introduced.  

---  

## Documentation Generation  

The skill uses `mkdocstrings` to auto‑generate API docs from docstrings. Run:

```bash
mkdocstrings -r . -o docs/metrics
```

The generated docs are version‑controlled alongside the code.

---