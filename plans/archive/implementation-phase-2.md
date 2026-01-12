}")
        print(f"✓ Files: {len(skeleton_data['files'])}")
        print(f"✓ Directories: {len(skeleton_data['directories'])}")
        
        # Step 4: EDIT
        print("\n" + "="*60)
        print("STEP 4: EDIT - Generating skill content")
        print("="*60)
        
        content = self.edit(
            skill_skeleton=skeleton.skill_skeleton,
            parent_skills=understanding.parent_skills,
            composition_strategy=plan.composition_strategy
        )
        
        print(f"✓ Main content generated: {len(content.skill_content)} chars")
        print(f"✓ Capabilities documented: {len(json.loads(content.capability_implementations))}")
        print(f"✓ Examples created: {len(json.loads(content.usage_examples))}")
        
        # Step 5: PACKAGE
        print("\n" + "="*60)
        print("STEP 5: PACKAGE - Validating and packaging")
        print("="*60)
        
        package = self.package(
            skill_content=content.skill_content,
            skill_metadata=plan.skill_metadata,
            taxonomy_path=understanding.taxonomy_path,
            capability_implementations=content.capability_implementations
        )
        
        validation = json.loads(package.validation_report)
        print(f"✓ Validation: {'PASSED' if validation['passed'] else 'FAILED'}")
        print(f"✓ Quality score: {package.quality_score:.2f}")
        
        if validation['errors']:
            print(f"❌ Validation errors:")
            for error in validation['errors']:
                print(f"   - {error}")
            return {
                "status": "validation_failed",
                "errors": validation['errors']
            }
        
        # Step 6: ITERATE (HITL)
        print("\n" + "="*60)
        print("STEP 6: ITERATE - Human-in-the-loop approval")
        print("="*60)
        
        iteration_count = 0
        while iteration_count < max_iterations:
            # Get human feedback
            if auto_approve:
                feedback = json.dumps({
                    "status": "approved",
                    "comments": "Auto-approved for testing"
                })
            else:
                feedback = self._get_human_feedback(
                    package.packaging_manifest,
                    validation
                )
            
            approval = self.iterate(
                packaged_skill=package.packaging_manifest,
                validation_report=package.validation_report,
                human_feedback=feedback,
                usage_analytics=json.dumps({})  # No analytics for new skill
            )
            
            print(f"\n📋 Iteration {iteration_count + 1}: {approval.approval_status}")
            
            if approval.approval_status == "approved":
                # Persist to taxonomy
                print(f"\n✅ Skill approved! Registering in taxonomy...")
                
                success = self.taxonomy.register_skill(
                    path=understanding.taxonomy_path,
                    metadata=skill_metadata,
                    content=content.skill_content,
                    evolution=json.loads(approval.evolution_metadata)
                )
                
                if success:
                    print(f"🎉 Skill successfully created!")
                    print(f"📍 Location: skills/{understanding.taxonomy_path}")
                    print(f"🆔 Skill ID: {skill_metadata['skill_id']}")
                    
                    return {
                        "status": "approved",
                        "skill_id": skill_metadata['skill_id'],
                        "path": understanding.taxonomy_path,
                        "version": skill_metadata['version'],
                        "quality_score": package.quality_score
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to register skill in taxonomy"
                    }
            
            elif approval.approval_status == "needs_revision":
                print(f"📝 Revision needed...")
                revision_plan = json.loads(approval.revision_plan)
                
                # Re-run EDIT step with feedback
                print(f"\n🔄 Regenerating content with feedback...")
                content = self.edit(
                    skill_skeleton=skeleton.skill_skeleton,
                    parent_skills=understanding.parent_skills,
                    composition_strategy=plan.composition_strategy
                    # TODO: Pass revision feedback to edit step
                )
                
                # Re-package
                package = self.package(
                    skill_content=content.skill_content,
                    skill_metadata=plan.skill_metadata,
                    taxonomy_path=understanding.taxonomy_path,
                    capability_implementations=content.capability_implementations
                )
                
            else:  # rejected
                print(f"❌ Skill rejected")
                return {
                    "status": "rejected",
                    "reason": approval.revision_plan
                }
            
            iteration_count += 1
        
        print(f"⚠️  Maximum iterations ({max_iterations}) reached")
        return {
            "status": "max_iterations_reached",
            "message": f"Skill not approved after {max_iterations} iterations"
        }
    
    def _get_human_feedback(
        self,
        packaging_manifest: str,
        validation_report: Dict
    ) -> str:
        """Get human feedback on packaged skill.
        
        In production, this would integrate with a review UI.
        For now, returns auto-approval.
        """
        # TODO: Implement actual HITL interface
        # This could be:
        # - Web UI for review
        # - CLI prompts
        # - Integration with issue tracking
        # - Slack/email notifications
        
        return json.dumps({
            "status": "approved",
            "comments": "Automated approval - implement HITL interface",
            "reviewer": "system"
        })
```

### Day 12-14: Testing & Documentation

**File: tests/test_skill_creation.py**
```python
"""Integration tests for skill creation workflow."""
import pytest
import json
from pathlib import Path
import tempfile
import shutil

from src.taxonomy.manager import TaxonomyManager
from src.workflow.skill_creator import TaxonomySkillCreator


@pytest.fixture
def temp_taxonomy(tmp_path):
    """Create temporary taxonomy structure for testing."""
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    
    # Create minimal structure
    (skills_root / "_core").mkdir()
    (skills_root / "_templates").mkdir()
    (skills_root / "technical_skills").mkdir()
    
    # Create taxonomy meta
    meta = {
        "version": "0.1.0",
        "total_skills": 0,
        "statistics": {"by_type": {}}
    }
    with open(skills_root / "taxonomy_meta.json", 'w') as f:
        json.dump(meta, f)
    
    # Create core skill
    core_skill = {
        "skill_id": "core.reasoning",
        "version": "1.0.0",
        "type": "cognitive",
        "weight": "lightweight",
        "load_priority": "always",
        "always_loaded": True,
        "dependencies": [],
        "capabilities": ["reasoning"]
    }
    with open(skills_root / "_core" / "reasoning.json", 'w') as f:
        json.dump(core_skill, f)
    
    return skills_root


def test_taxonomy_manager_initialization(temp_taxonomy):
    """Test TaxonomyManager loads correctly."""
    manager = TaxonomyManager(temp_taxonomy)
    
    assert manager.meta['version'] == "0.1.0"
    assert "core.reasoning" in manager.metadata_cache
    assert manager.metadata_cache["core.reasoning"].always_loaded


def test_skill_exists_check(temp_taxonomy):
    """Test skill existence checking."""
    manager = TaxonomyManager(temp_taxonomy)
    
    assert not manager.skill_exists("technical_skills/programming/python")
    
    # Create a skill manually
    skill_dir = temp_taxonomy / "technical_skills/programming/python"
    skill_dir.mkdir(parents=True)
    (skill_dir / "metadata.json").write_text("{}")
    
    assert manager.skill_exists("technical_skills/programming/python")


def test_dependency_validation(temp_taxonomy):
    """Test dependency validation."""
    manager = TaxonomyManager(temp_taxonomy)
    
    # Valid dependency (core skill exists)
    valid, missing = manager.validate_dependencies(["core.reasoning"])
    assert valid
    assert len(missing) == 0
    
    # Invalid dependency
    valid, missing = manager.validate_dependencies(["nonexistent.skill"])
    assert not valid
    assert "nonexistent.skill" in missing


def test_circular_dependency_detection(temp_taxonomy):
    """Test circular dependency detection."""
    manager = TaxonomyManager(temp_taxonomy)
    
    # Add skills with circular dependencies for testing
    # This would require more setup, marking as TODO
    # TODO: Implement circular dependency test
    pass


@pytest.mark.integration
def test_full_skill_creation_workflow(temp_taxonomy):
    """Test complete skill creation from task to registration."""
    manager = TaxonomyManager(temp_taxonomy)
    creator = TaxonomySkillCreator(taxonomy_manager=manager)
    
    # Note: This test requires LLM access via DSPy
    # For CI/CD, mock the LLM responses or use cached completions
    
    task = "Create a Python async programming skill"
    user_context = {"user_id": "test_user"}
    
    result = creator.forward(
        task_description=task,
        user_context=user_context,
        auto_approve=True  # Skip HITL for testing
    )
    
    assert result['status'] == 'approved'
    assert 'skill_id' in result
    assert 'path' in result
    
    # Verify skill was registered
    assert manager.skill_exists(result['path'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**File: docs/architecture/skill-creation-workflow.md**
```markdown
# Skill Creation Workflow Architecture

## Overview

The skill creation workflow implements a 6-step process for generating skills dynamically based on user tasks, inspired by Anthropic's skill-creator pattern.

## Workflow Steps

### 1. UNDERSTAND
**Purpose**: Extract task context and map to taxonomy position

**Inputs**:
- Task description
- Currently mounted skills
- Relevant taxonomy branches

**Outputs**:
- Task intent analysis
- Proposed taxonomy path
- Parent/sibling skills for context
- Dependency analysis
- Confidence score

**Implementation**: `UnderstandTaskForSkill` DSPy signature

### 2. PLAN
**Purpose**: Design skill structure with taxonomy integration

**Inputs**:
- Task intent
- Taxonomy path
- Parent skills
- Dependency analysis

**Outputs**:
- Skill metadata (conforming to schema)
- Resolved dependencies
- Capability definitions
- Resource requirements
- Compatibility constraints
- Composition strategy

**Implementation**: `PlanSkillStructure` DSPy signature

### 3. INITIALIZE
**Purpose**: Create skill skeleton matching taxonomy standards

**Inputs**:
- Skill metadata
- Capabilities
- Taxonomy path

**Outputs**:
- Complete directory structure
- File placeholders
- Validation checklist

**Implementation**: `InitializeSkillSkeleton` DSPy signature

### 4. EDIT
**Purpose**: Generate comprehensive skill content

**Inputs**:
- Skill skeleton
- Parent skills (for consistency)
- Composition strategy

**Outputs**:
- Full SKILL.md content
- Capability implementations
- Usage examples
- Best practices
- Integration guide

**Implementation**: `EditSkillContent` DSPy signature

### 5. PACKAGE
**Purpose**: Validate and prepare for approval

**Inputs**:
- Skill content
- Skill metadata
- Taxonomy path
- Capability implementations

**Outputs**:
- Validation report
- Integration tests
- Packaging manifest
- Quality score

**Implementation**: `PackageSkillForApproval` DSPy signature

### 6. ITERATE
**Purpose**: HITL approval and evolution tracking

**Inputs**:
- Packaged skill
- Validation report
- Human feedback
- Usage analytics (optional)

**Outputs**:
- Approval status
- Revision plan (if needed)
- Evolution metadata
- Next steps

**Implementation**: `IterateSkillWithFeedback` DSPy signature

## Design Principles

### Progressive Disclosure
Skills are organized in layers of increasing detail:
1. **Metadata** (lightweight, always loaded)
2. **SKILL.md body** (loaded on demand)
3. **Resources** (lazy loaded only when needed)

### Degrees of Freedom
Content organization from high to low specificity:
- **High**: Natural language descriptions
- **Medium**: Pseudocode and algorithms
- **Low**: Executable scripts and code

### Conciseness
Every piece of information is challenged:
- Is this necessary?
- Can it be inferred from context?
- Does it add unique value?

## Integration with Taxonomy

The workflow ensures tight integration with the taxonomy:

1. **Path Validation**: Every skill knows its position
2. **Dependency Resolution**: All dependencies are verified
3. **Circular Detection**: Prevents dependency cycles
4. **Composition Patterns**: Skills understand their relationships
5. **Version Management**: Tracks evolution over time

## Quality Assurance

Multiple validation layers ensure quality:

- **Schema Conformance**: Metadata matches expected structure
- **Path Validity**: Taxonomy path is valid and unique
- **Dependency Check**: All dependencies resolvable
- **Documentation**: Complete and well-structured
- **Examples**: Executable and meaningful
- **Tests**: Comprehensive validation suite

## Extension Points

The workflow is designed for extensibility:

- Custom DSPy signatures for domain-specific skills
- Pluggable validation rules
- Alternative storage backends
- Different HITL interfaces
- Analytics integration

## Performance Considerations

- **Caching**: Taxonomy lookups are cached
- **Parallel Generation**: Multiple skills can be generated concurrently
- **Lazy Loading**: Resources loaded only when needed
- **Incremental Updates**: Only changed components regenerated
```

---

# PHASE 2: Core Workflow (Week 3-4)

## Week 3: Workflow Optimization & Validation

### Day 15-16: Skill Validation System

**File: src/validators/skill_validator.py**
```python
"""Comprehensive skill validation system."""
import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class SkillValidator:
    """Validates skills against taxonomy standards."""
    
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.metadata_schema = self._load_schema()
    
    def _load_schema(self) -> Dict:
        """Load JSON schema for metadata validation."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": [
                "skill_id",
                "version",
                "type",
                "weight",
                "load_priority",
                "dependencies",
                "capabilities"
            ],
            "properties": {
                "skill_id": {
                    "type": "string",
                    "pattern": "^[a-z0-9_]+\\.[a-z0-9_]+(\\.[a-z0-9_]+)*$"
                },
                "version": {
                    "type": "string",
                    "pattern": "^\\d+\\.\\d+\\.\\d+$"
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "cognitive",
                        "technical",
                        "domain",
                        "tool",
                        "mcp",
                        "specialization",
                        "task_focus",
                        "memory"
                    ]
                },
                "weight": {
                    "type": "string",
                    "enum": ["lightweight", "medium", "heavyweight"]
                },
                "load_priority": {
                    "type": "string",
                    "enum": ["always", "task_specific", "on_demand", "dormant"]
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "created_at": {"type": "string", "format": "date-time"},
                "last_modified": {"type": "string", "format": "date-time"}
            }
        }
        return schema
    
    def validate_metadata(self, metadata: Dict) -> Tuple[bool, List[str]]:
        """Validate skill metadata against schema."""
        errors = []
        
        try:
            jsonschema.validate(instance=metadata, schema=self.metadata_schema)
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
            return False, errors
        
        # Additional custom validations
        
        # Check skill_id format matches taxonomy path
        skill_id = metadata['skill_id']
        if not self._validate_skill_id_format(skill_id):
            errors.append(f"Invalid skill_id format: {skill_id}")
        
        # Validate version format
        if not self._validate_semver(metadata['version']):
            errors.append(f"Invalid version format: {metadata['version']}")
        
        # Check weight matches capabilities
        if not self._validate_weight_capabilities(
            metadata['weight'],
            metadata['capabilities']
        ):
            errors.append(
                f"Weight '{metadata['weight']}' inconsistent with "
                f"{len(metadata['capabilities'])} capabilities"
            )
        
        return len(errors) == 0, errors
    
    def validate_structure(self, skill_path: Path) -> Tuple[bool, List[str]]:
        """Validate skill directory structure."""
        errors = []
        
        # Required files
        required_files = ['metadata.json', 'SKILL.md']
        for filename in required_files:
            if not (skill_path / filename).exists():
                errors.append(f"Missing required file: {filename}")
        
        # Required directories
        required_dirs = ['capabilities', 'examples', 'tests', 'resources']
        for dirname in required_dirs:
            if not (skill_path / dirname).is_dir():
                errors.append(f"Missing required directory: {dirname}")
        
        # Validate metadata.json is valid JSON
        try:
            with open(skill_path / 'metadata.json', 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in metadata.json: {e}")
        except FileNotFoundError:
            pass  # Already reported above
        
        return len(errors) == 0, errors
    
    def validate_documentation(self, skill_md_path: Path) -> Tuple[bool, List[str]]:
        """Validate SKILL.md documentation completeness."""
        errors = []
        warnings = []
        
        if not skill_md_path.exists():
            return False, ["SKILL.md not found"]
        
        content = skill_md_path.read_text()
        
        # Required sections
        required_sections = [
            "# ",  # Title
            "## Overview",
            "## Capabilities",
            "## Dependencies",
            "## Usage Examples",
            "## Best Practices"
        ]
        
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: {section}")
        
        # Check for code examples
        if "```" not in content:
            warnings.append("No code examples found")
        
        # Check length (should be substantial but not excessive)
        if len(content) < 500:
            warnings.append("Documentation seems very brief (< 500 chars)")
        elif len(content) > 20000:
            warnings.append("Documentation seems very long (> 20000 chars)")
        
        return len(errors) == 0, errors + warnings
    
    def validate_examples(self, examples_path: Path) -> Tuple[bool, List[str]]:
        """Validate usage examples are present and well-formed."""
        errors = []
        
        if not examples_path.is_dir():
            return False, ["Examples directory not found"]
        
        example_files = list(examples_path.glob("*.md"))
        if len(example_files) == 0:
            errors.append("No example files found")
        
        for example_file in example_files:
            content = example_file.read_text()
            if "```" not in content:
                errors.append(f"Example {example_file.name} contains no code blocks")
        
        return len(errors) == 0, errors
    
    def validate_naming_conventions(self, skill_id: str, path: str) -> Tuple[bool, List[str]]:
        """Validate naming conventions are followed."""
        errors = []
        
        # skill_id should match path structure
        path_parts = path.replace('/', '.')
        if not skill_id.startswith(path_parts.replace('_', '.')):
            errors.append(
                f"skill_id '{skill_id}' doesn't match path structure '{path}'"
            )
        
        # Check for consistent naming (snake_case)
        if not skill_id.replace('.', '_').replace('_', '').islower():
            errors.append(f"skill_id '{skill_id}' should use lowercase and underscores")
        
        return len(errors) == 0, errors
    
    def validate_complete(self, skill_path: Path) -> Dict:
        """Run complete validation suite on a skill."""
        results = {
            "passed": True,
            "checks": [],
            "warnings": [],
            "errors": []
        }
        
        # Load metadata
        try:
            with open(skill_path / 'metadata.json', 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Cannot load metadata: {e}")
            return results
        
        # Run all validations
        validations = [
            ("metadata_schema", self.validate_metadata, metadata),
            ("structure", self.validate_structure, skill_path),
            ("documentation", self.validate_documentation, skill_path / "SKILL.md"),
            ("examples", self.validate_examples, skill_path / "examples"),
            ("naming", self.validate_naming_conventions, metadata['skill_id'], str(skill_path))
        ]
        
        for check_name, validator, *args in validations:
            try:
                passed, messages = validator(*args)
                results["checks"].append({
                    "name": check_name,
                    "status": "pass" if passed else "fail",
                    "messages": messages
                })
                
                if not passed:
                    results["passed"] = False
                    results["errors"].extend(messages)
                elif messages:
                    results["warnings"].extend(messages)
                    
            except Exception as e:
                results["passed"] = False
                results["checks"].append({
                    "name": check_name,
                    "status": "error",
                    "messages": [str(e)]
                })
                results["errors"].append(f"{check_name}: {e}")
        
        return results
    
    def _validate_skill_id_format(self, skill_id: str) -> bool:
        """Check skill_id follows dot-notation format."""
        import re
        pattern = r'^[a-z0-9_]+\.[a-z0-9_]+(\.[a-z0-9_]+)*$'
        return bool(re.match(pattern, skill_id))
    
    def _validate_semver(self, version: str) -> bool:
        """Validate semantic versioning format."""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _validate_weight_capabilities(self, weight: str, capabilities: List[str]) -> bool:
        """Validate weight classification matches capability count."""
        cap_count = len(capabilities)
        
        if weight == "lightweight" and cap_count > 5:
            return False
        elif weight == "medium" and (cap_count < 3 or cap_count > 10):
            return False
        elif weight == "heavyweight" and cap_count < 8:
            return False
        
        return True
```

### Day 17-18: DSPy Optimization

**File: src/workflow/optimizer.py**
```python
"""DSPy workflow optimization and caching."""
import dspy
from typing import Dict, List, Optional
import pickle
from pathlib import Path
import hashlib


class WorkflowOptimizer:
    """Optimizes DSPy workflow performance through caching and tuning."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hit_rate = {"hits": 0, "misses": 0}
    
    def cache_key(self, step: str, inputs: Dict) -> str:
        """Generate cache key from step name and inputs."""
        # Create deterministic hash from inputs
        input_str = f"{step}::{str(sorted(inputs.items()))}"
        return hashlib.md5(input_str.encode()).hexdigest()
    
    def get_cached(self, step: str, inputs: Dict) -> Optional[Dict]:
        """Retrieve cached result if available."""
        key = self.cache_key(step, inputs)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                self.hit_rate["hits"] += 1
                return pickle.load(f)
        
        self.hit_rate["misses"] += 1
        return None
    
    def cache_result(self, step: str, inputs: Dict, result: Dict):
        """Cache workflow step result."""
        key = self.cache_key(step, inputs)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
    
    def clear_cache(self):
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        total = self.hit_rate["hits"] + self.hit_rate["misses"]
        hit_rate = self.hit_rate["hits"] / total if total > 0 else 0
        
        return {
            "hits": self.hit_rate["hits"],
            "misses": self.hit_rate["misses"],
            "hit_rate": hit_rate,
            "cache_size": len(list(self.cache_dir.glob("*.pkl")))
        }
    
    def optimize_signatures(
        self,
        training_examples: List[dspy.Example],
        metric_fn: callable
    ):
        """Optimize DSPy signatures using training examples.
        
        This uses DSPy's built-in optimization to improve prompt quality.
        """
        # TODO: Implement signature optimization
        # This would use dspy.BootstrapFewShot or similar
        pass
```

### Day 19-21: CLI Tool

**File: src/cli/skill_cli.py**
```python
"""Command-line interface for skill management."""
import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from ..taxonomy.manager import TaxonomyManager
from ..workflow.skill_creator import TaxonomySkillCreator
from ..validators.skill_validator import SkillValidator

console = Console()


@click.group()
@click.option('--skills-root', default='./skills', help='Path to skills directory')
@click.pass_context
def cli(ctx, skills_root):
    """Agentic Skills System CLI."""
    ctx.ensure_object(dict)
    ctx.obj['skills_root'] = Path(skills_root)
    ctx.obj['taxonomy'] = TaxonomyManager(Path(skills_root))


@cli.command()
@click.pass_context
def info(ctx):
    """Display taxonomy information."""
    taxonomy = ctx.obj['taxonomy']
    meta = taxonomy.meta
    
    console.print("\n[bold cyan]Taxonomy Information[/bold cyan]")
    console.print(f"Version: {meta['version']}")
    console.print(f"Total Skills: {meta['total_skills']}")
    console.print(f"Last Updated: {meta['last_updated']}")
    
    if meta['statistics'].get('by_type'):
        table = Table(title="Skills by Type")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="magenta")
        
        for skill_type, count in meta['statistics']['by_type'].items():
            table.add_row(skill_type, str(count))
        
        console.print(table)


@cli.command()
@click.argument('task')
@click.option('--user-id', default='cli_user', help='User ID for context')
@click.option('--auto-approve', is_flag=True, help='Skip human approval')
@click.pass_context
def create(ctx, task, user_id, auto_approve):
    """Create a new skill from task description."""
    taxonomy = ctx.obj['taxonomy']
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)
    
    console.print(f"\n[bold green]Creating skill for task:[/bold green] {task}")
    
    with Progress() as progress:
        task_progress = progress.add_task("[cyan]Generating skill...", total=100)
        
        result = creator.forward(
            task_description=task,
            user_context={"user_id": user_id},
            auto_approve=auto_approve
        )
        
        progress.update(task_progress, completed=100)
    
    if result['status'] == 'approved':
        console.print(f"\n[bold green]✓ Skill created successfully![/bold green]")
        console.print(f"Skill ID: {result['skill_id']}")
        console.print(f"Path: {result['path']}")
        console.print(f"Quality: {result.get('quality_score', 0):.2f}")
    else:
        console.print(f"\n[bold red]✗ Skill creation failed[/bold red]")
        console.print(f"Status: {result['status']}")
        if 'message' in result:
            console.print(f"Message: {result['message']}")


@cli.command()
@click.argument('skill_path')
@click.pass_context
def validate(ctx, skill_path):
    """Validate a skill."""
    skills_root = ctx.obj['skills_root']
    validator = SkillValidator(schema_path=skills_root / "taxonomy_meta.json")
    
    full_path = skills_root / skill_path
    
    if not full_path.exists():
        console.print(f"[bold red]✗ Skill not found:[/bold red] {skill_path}")
        return
    
    console.print(f"\n[bold cyan]Validating skill:[/bold cyan] {skill_path}")
    
    results = validator.validate_complete(full_path)
    
    if results['passed']:
        console.print("[bold green]✓ All validations passed![/bold green]")
    else:
        console.print("[bold red]✗ Validation failed[/bold red]")
    
    # Display check results
    table = Table(title="Validation Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")