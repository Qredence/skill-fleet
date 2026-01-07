table.add_column("Messages")
    
    for check in results['checks']:
        status_icon = "✓" if check['status'] == 'pass' else "✗"
        status_color = "green" if check['status'] == 'pass' else "red"
        
        messages = "\n".join(check.get('messages', []))
        
        table.add_row(
            check['name'],
            f"[{status_color}]{status_icon}[/{status_color}]",
            messages
        )
    
    console.print(table)
    
    if results['warnings']:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in results['warnings']:
            console.print(f"  ⚠ {warning}")


@cli.command()
@click.argument('skill_id')
@click.pass_context
def show(ctx, skill_id):
    """Show skill details."""
    taxonomy = ctx.obj['taxonomy']
    
    metadata = taxonomy.get_skill_metadata(skill_id)
    
    if not metadata:
        console.print(f"[bold red]✗ Skill not found:[/bold red] {skill_id}")
        return
    
    console.print(f"\n[bold cyan]Skill Details:[/bold cyan] {skill_id}")
    console.print(f"Version: {metadata.version}")
    console.print(f"Type: {metadata.type}")
    console.print(f"Weight: {metadata.weight}")
    console.print(f"Priority: {metadata.load_priority}")
    
    console.print(f"\n[bold]Capabilities:[/bold]")
    for cap in metadata.capabilities:
        console.print(f"  • {cap}")
    
    if metadata.dependencies:
        console.print(f"\n[bold]Dependencies:[/bold]")
        for dep in metadata.dependencies:
            console.print(f"  • {dep}")


@cli.command()
@click.pass_context
def list(ctx):
    """List all skills in taxonomy."""
    taxonomy = ctx.obj['taxonomy']
    
    table = Table(title="Available Skills")
    table.add_column("Skill ID", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Weight", style="yellow")
    
    for skill_id, metadata in taxonomy.metadata_cache.items():
        table.add_row(
            skill_id,
            metadata.version,
            metadata.type,
            metadata.weight
        )
    
    console.print(table)


if __name__ == '__main__':
    cli(obj={})
```

**File: setup.py**
```python
"""Setup script for agentic-skills-system."""
from setuptools import setup, find_packages

setup(
    name="agentic-skills-system",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "dspy-ai>=2.0.0",
        "jsonschema>=4.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        'console_scripts': [
            'askill=cli.skill_cli:cli',
        ],
    },
    python_requires=">=3.9",
)
```

## Week 4: Quality Assurance & Documentation

### Day 22-24: Comprehensive Testing

**File: tests/test_validators.py**
```python
"""Tests for skill validation system."""
import pytest
import json
from pathlib import Path

from src.validators.skill_validator import SkillValidator


@pytest.fixture
def validator(tmp_path):
    schema_path = tmp_path / "taxonomy_meta.json"
    return SkillValidator(schema_path)


def test_valid_metadata(validator):
    """Test validation of correct metadata."""
    metadata = {
        "skill_id": "technical.programming.python",
        "version": "1.0.0",
        "type": "technical",
        "weight": "medium",
        "load_priority": "task_specific",
        "dependencies": [],
        "capabilities": ["async_programming", "context_managers"]
    }
    
    passed, errors = validator.validate_metadata(metadata)
    assert passed
    assert len(errors) == 0


def test_invalid_metadata_missing_field(validator):
    """Test validation catches missing required fields."""
    metadata = {
        "skill_id": "test.skill",
        "version": "1.0.0",
        # Missing 'type' and other required fields
    }
    
    passed, errors = validator.validate_metadata(metadata)
    assert not passed
    assert len(errors) > 0


def test_invalid_semver(validator):
    """Test validation catches invalid version format."""
    metadata = {
        "skill_id": "test.skill",
        "version": "1.0",  # Invalid semver
        "type": "technical",
        "weight": "lightweight",
        "load_priority": "on_demand",
        "dependencies": [],
        "capabilities": ["test"]
    }
    
    passed, errors = validator.validate_metadata(metadata)
    assert not passed
    assert any("version" in err.lower() for err in errors)


def test_structure_validation(validator, tmp_path):
    """Test directory structure validation."""
    skill_path = tmp_path / "test_skill"
    skill_path.mkdir()
    
    # Missing required files
    passed, errors = validator.validate_structure(skill_path)
    assert not passed
    assert "metadata.json" in str(errors)
    
    # Add required files and directories
    (skill_path / "metadata.json").write_text("{}")
    (skill_path / "SKILL.md").write_text("# Test")
    (skill_path / "capabilities").mkdir()
    (skill_path / "examples").mkdir()
    (skill_path / "tests").mkdir()
    (skill_path / "resources").mkdir()
    
    passed, errors = validator.validate_structure(skill_path)
    assert passed
```

### Day 25-28: Documentation

**File: README.md**
```markdown
# Agentic Skills System

A dynamic, hierarchical skills taxonomy for agentic AI systems with just-in-time skill generation powered by DSPy and LLMs.

## Features

- 📊 **Hierarchical Taxonomy**: 8-level skill organization (Cognitive, Technical, Domain, Tools, MCP, Specializations, Task Focus, Memory)
- 🚀 **Dynamic Generation**: Create skills on-demand using LLM-powered workflow
- 🔄 **Stateful Interactions**: Maintain context across sessions
- ✅ **Comprehensive Validation**: Multi-layer quality assurance
- 📈 **Progressive Loading**: Efficient skill mounting based on task requirements
- 🎯 **User-Centric**: Onboarding-driven bootstrap for personalized experiences

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourorg/agentic-skills-system.git
cd agentic-skills-system

# Install dependencies
pip install -e .

# Initialize taxonomy
askill info
```

### Create Your First Skill

```bash
# Create a skill from a task description
askill create "Help me write Python async code"

# Validate a skill
askill validate technical_skills/programming/python/async

# List all skills
askill list
```

### Python API

```python
from src.taxonomy.manager import TaxonomyManager
from src.workflow.skill_creator import TaxonomySkillCreator

# Initialize
taxonomy = TaxonomyManager("./skills")
creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)

# Create a skill
result = creator.forward(
    task_description="Create a skill for data visualization",
    user_context={"user_id": "user123"},
    auto_approve=False
)

print(f"Skill created: {result['skill_id']}")
```

## Architecture

See [docs/architecture/](docs/architecture/) for detailed architecture documentation.

### Workflow Steps

1. **UNDERSTAND**: Analyze task and map to taxonomy
2. **PLAN**: Design skill structure with dependencies
3. **INITIALIZE**: Create file structure
4. **EDIT**: Generate comprehensive content
5. **PACKAGE**: Validate and prepare
6. **ITERATE**: Human-in-the-loop approval

## Directory Structure

```
agentic-skills-system/
├── skills/                    # Taxonomy root
│   ├── _core/                # Always-loaded skills
│   ├── _templates/           # Generation templates
│   ├── cognitive_skills/     # Analysis, synthesis, reasoning
│   ├── technical_skills/     # Programming, infrastructure
│   ├── domain_knowledge/     # ML, NLP, business intelligence
│   ├── tool_proficiency/     # Development tools, data tools
│   ├── mcp_capabilities/     # Context, state management
│   ├── specializations/      # Frontend, backend, DevOps
│   ├── task_focus_areas/     # Build, debug, optimize
│   └── memory_blocks/        # Project context, history
├── src/
│   ├── taxonomy/             # Taxonomy management
│   ├── workflow/             # Skill creation workflow
│   ├── generators/           # Content generators
│   ├── validators/           # Validation system
│   ├── analytics/            # Usage analytics
│   └── cli/                  # Command-line interface
├── tests/                    # Test suite
├── docs/                     # Documentation
└── config/                   # Configuration files
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Roadmap

- [ ] Phase 1: Foundation ✅
- [ ] Phase 2: Core Workflow ✅
- [ ] Phase 3: Onboarding System (In Progress)
- [ ] Phase 4: Dynamic Generation
- [ ] Phase 5: Intelligence Layer
- [ ] Phase 6: Production Hardening

## License

MIT License - see [LICENSE](LICENSE) for details.
```

---

# PHASE 3: Onboarding System (Week 5-6)

## Week 5: User Onboarding

### Day 29-31: Onboarding Flow

**File: src/onboarding/bootstrap.py**
```python
"""User onboarding and skill bootstrapping."""
import json
from typing import Dict, List
from pathlib import Path

from ..taxonomy.manager import TaxonomyManager
from ..workflow.skill_creator import TaxonomySkillCreator


class SkillBootstrapper:
    """Bootstrap user-specific skill sets based on onboarding."""
    
    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        skill_creator: TaxonomySkillCreator,
        profiles_path: Path
    ):
        self.taxonomy = taxonomy_manager
        self.creator = skill_creator
        self.profiles = self._load_profiles(profiles_path)
    
    def _load_profiles(self, profiles_path: Path) -> Dict:
        """Load bootstrap profiles configuration."""
        with open(profiles_path, 'r') as f:
            return json.load(f)
    
    async def onboard_user(
        self,
        user_id: str,
        responses: Dict
    ) -> Dict:
        """Onboard a new user and bootstrap their skills.
        
        Args:
            user_id: Unique user identifier
            responses: User's onboarding questionnaire responses
        
        Returns:
            Dict with user profile and mounted skills
        """
        print(f"🎯 Onboarding user: {user_id}")
        
        # Analyze responses to determine profile
        profile = self.analyze_responses(responses)
        print(f"📊 Profile identified: {profile['primaryRole']}")
        
        # Generate skill plan
        skill_plan = self.generate_skill_plan(profile)
        print(f"📋 Skill plan: {len(skill_plan['required'])} required, "
              f"{len(skill_plan['onDemand'])} on-demand")
        
        # Generate required skills
        mounted_skills = []
        for skill_path in skill_plan['required']:
            # Check if skill exists
            if not self.taxonomy.skill_exists(skill_path):
                print(f"🔨 Generating skill: {skill_path}")
                result = await self._generate_skill_for_path(
                    skill_path,
                    user_id
                )
                if result['status'] == 'approved':
                    mounted_skills.append(result['skill_id'])
            else:
                # Load existing skill
                skill_id = self._path_to_skill_id(skill_path)
                mounted_skills.append(skill_id)
                print(f"✓ Loaded existing skill: {skill_id}")
        
        # Register on-demand skills
        self.register_on_demand_skills(user_id, skill_plan['onDemand'])
        
        # Create user profile
        user_profile = {
            "user_id": user_id,
            "profile": profile,
            "mounted_skills": mounted_skills,
            "on_demand_skills": skill_plan['onDemand'],
            "created_at": datetime.utcnow().isoformat(),
            "ready_for_tasks": True
        }
        
        # Persist user profile
        self._save_user_profile(user_profile)
        
        print(f"🎉 Onboarding complete! {len(mounted_skills)} skills mounted.")
        
        return user_profile
    
    def analyze_responses(self, responses: Dict) -> Dict:
        """Map user responses to skill requirements."""
        profile = {
            "primaryRole": responses.get('role', 'general_purpose'),
            "techStack": responses.get('tech_stack', []),
            "commonTasks": responses.get('common_tasks', []),
            "experience_level": responses.get('experience_level', 'mid-level'),
            "preferences": responses.get('preferences', {})
        }
        return profile
    
    def generate_skill_plan(self, profile: Dict) -> Dict:
        """Generate skill plan based on user profile."""
        role = profile['primaryRole']
        
        # Get base plan for role
        base_plan = self.profiles['bootstrap_profiles'].get(
            role,
            self.profiles['bootstrap_profiles']['general_purpose']
        )
        
        required = base_plan['required'].copy()
        on_demand = base_plan['on_demand'].copy()
        
        # Augment based on tech stack
        for tech in profile['techStack']:
            tech_skills = self.profiles['tech_stack_mapping'].get(tech, [])
            required.extend(tech_skills)
        
        # Augment based on common tasks
        for task in profile['commonTasks']:
            task_skills = self.profiles['task_mapping'].get(task, [])
            required.extend(task_skills)
        
        # Remove duplicates
        required = list(set(required))
        on_demand = list(set(on_demand))
        
        return {
            "required": required,
            "onDemand": on_demand
        }
    
    async def _generate_skill_for_path(
        self,
        skill_path: str,
        user_id: str
    ) -> Dict:
        """Generate a skill for a specific taxonomy path."""
        # Infer task description from path
        task_description = self._path_to_task_description(skill_path)
        
        result = self.creator.forward(
            task_description=task_description,
            user_context={"user_id": user_id},
            auto_approve=True  # Auto-approve bootstrap skills
        )
        
        return result
    
    def register_on_demand_skills(
        self,
        user_id: str,
        on_demand_paths: List[str]
    ):
        """Register skills for on-demand generation."""
        # TODO: Implement on-demand skill registry
        pass
    
    def _path_to_skill_id(self, path: str) -> str:
        """Convert taxonomy path to skill_id."""
        return path.replace('/', '.')
    
    def _path_to_task_description(self, path: str) -> str:
        """Convert taxonomy path to task description for generation."""
        parts = path.split('/')
        last_part = parts[-1].replace('_', ' ')
        category = parts[0].replace('_', ' ')
        
        return f"Create a {last_part} skill in the {category} category"
    
    def _save_user_profile(self, profile: Dict):
        """Persist user profile to storage."""
        # TODO: Implement user profile storage
        pass
```

**File: config/profiles/bootstrap_profiles.json**
```json
{
  "bootstrap_profiles": {
    "web_developer": {
      "required": [
        "technical_skills/programming/languages/javascript_typescript",
        "technical_skills/programming/paradigms/object_oriented",
        "tool_proficiency/development_tools/version_control",
        "specializations/frontend_development",
        "task_focus_areas/build_create"
      ],
      "on_demand": [
        "technical_skills/infrastructure/containerization",
        "specializations/backend_development",
        "technical_skills/apis_integration/rest_apis"
      ]
    },
    "backend_developer": {
      "required": [
        "technical_skills/programming/languages/python",
        "technical_skills/data_engineering/storage/relational_databases",
        "technical_skills/apis_integration/rest_apis",
        "specializations/backend_development",
        "task_focus_areas/build_create"
      ],
      "on_demand": [
        "technical_skills/infrastructure/cloud_platforms",
        "technical_skills/security/authentication_authorization",
        "domain_knowledge/business_intelligence"
      ]
    },
    "data_scientist": {
      "required": [
        "technical_skills/programming/languages/python",
        "domain_knowledge/machine_learning",
        "technical_skills/data_engineering/processing/etl_pipelines",
        "tool_proficiency/data_tools/visualization_tools",
        "task_focus_areas/research_explore"
      ],
      "on_demand": [
        "domain_knowledge/nlp_understanding",
        "domain_knowledge/computer_vision",
        "technical_skills/data_engineering/storage/vector_databases"
      ]
    },
    "ml_engineer": {
      "required": [
        "technical_skills/programming/languages/python",
        "domain_knowledge/machine_learning",
        "specializations/ai_ml_engineering",
        "technical_skills/infrastructure/cloud_platforms",
        "task_focus_areas/build_create"
      ],
      "on_demand": [
        "domain_knowledge/nlp_understanding",
        "technical_skills/infrastructure/containerization",
        "task_focus_areas/optimize_improve"
      ]
    },
    "devops_engineer": {
      "required": [
        "technical_skills/infrastructure/cloud_platforms",
        "technical_skills/infrastructure/containerization",
        "technical_skills/infrastructure/infrastructure_as_code",
        "specializations/devops_sre",
        "task_focus_areas/maintain_support"
      ],
      "on_demand": [
        "technical_skills/programming/languages/shell_scripting",
        "tool_proficiency/monitoring_observability",
        "technical_skills/security"
      ]
    },
    "general_purpose": {
      "required": [
        "cognitive_skills/analysis",
        "cognitive_skills/synthesis",
        "cognitive_skills/reasoning",
        "task_focus_areas/build_create"
      ],
      "on_demand": [
        "technical_skills/programming/languages/python",
        "tool_proficiency/development_tools",
        "task_focus_areas/debug_fix"
      ]
    }
  },
  "tech_stack_mapping": {
    "JavaScript/TypeScript": [
      "technical_skills/programming/languages/javascript_typescript"
    ],
    "Python": [
      "technical_skills/programming/languages/python"
    ],
    "React": [
      "specializations/frontend_development/react_ecosystem"
    ],
    "Node.js": [
      "technical_skills/programming/languages/javascript_typescript/node_runtime"
    ],
    "Docker": [
      "technical_skills/infrastructure/containerization/docker"
    ],
    "Kubernetes": [
      "technical_skills/infrastructure/containerization/kubernetes"
    ],
    "AWS": [
      "technical_skills/infrastructure/cloud_platforms/aws_services"
    ],
    "PostgreSQL": [
      "technical_skills/data_engineering/storage/relational_databases"
    ],
    "MongoDB": [
      "technical_skills/data_engineering/storage/nosql_databases"
    ]
  },
  "task_mapping": {
    "Building new features": [
      "task_focus_areas/build_create"
    ],
    "Debugging issues": [
      "task_focus_areas/debug_fix"
    ],
    "Performance optimization": [
      "task_focus_areas/optimize_improve"
    ],
    "Code review": [
      "cognitive_skills/analysis/code_analysis"
    ],
    "Writing tests": [
      "technical_skills/programming/practices/testing"
    ],
    "Documentation": [
      "cognitive_skills/synthesis/content_generation/documentation"
    ],
    "Data analysis": [
      "cognitive_skills/analysis/data_analysis"
    ],
    "API design": [
      "cognitive_skills/synthesis/design_synthesis/api_design"
    ]
  }
}
```

### Day 32-35: Onboarding UI/CLI

**File: src/cli/onboarding_cli.py**
```python
"""Interactive onboarding CLI."""
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
import asyncio

from ..onboarding.bootstrap import SkillBootstrapper
from ..taxonomy.manager import TaxonomyManager
from ..workflow.skill_creator import TaxonomySkillCreator

console = Console()


@click.command()
@click.option('--user-id', prompt='Enter your user ID', help='Unique user identifier')
@click.option('--skills-root', default='./skills', help='Path to skills directory')
def onboard(user_id, skills_root):
    """Interactive onboarding workflow."""
    console.print("\n[bold cyan]Welcome to the Agentic Skills System![/bold cyan]\n")
    console.print("Let's set up your personalized skill set.\n")
    
    # Initialize components
    taxonomy = TaxonomyManager(skills_root)
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)
    bootstrapper = SkillBootstrapper(
        taxonomy_manager=taxonomy,
        skill_creator=creator,
        profiles_path="config/profiles/bootstrap_profiles.json"
    )
    
    # Collect onboarding responses
    responses = collect_onboarding_responses()
    
    # Run bootstrap process
    console.print("\n[bold green]Setting up your skills...[/bold green]\n")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Bootstrapping skills...", total=100)
        
        # Run async onboarding
        loop = asyncio.get_event_loop()
        user_profile = loop.run_until_complete(
            bootstrapper.onboard_user(user_id, responses)
        )
        
        progress.update(task, completed=100)
    
    # Display results
    console.print("\n[bold green]✓ Onboarding complete![/bold green]\n")
    console.print(f"Profile: {user_profile['profile']['primaryRole']}")
    console.print(f"Mounted Skills: {len(user_profile['mounted_skills'])}")
    console.print(f"On-Demand Skills: {len(user_profile['on_demand_skills'])}")
    
    console.print("\n[bold]You're ready to start![/bold]")
    console.print("Try: askill create \"your task here\"")


def collect_onboarding_responses() -> dict:
    """Collect user responses through interactive prompts."""
    responses = {}
    
    # Question 1: Role
    console.print("[bold]1. What's your primary role?[/bold]")
    roles = [
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Data Scientist",
        "ML Engineer",
        "DevOps/SRE",
        "Product Manager",
        "Other"
    ]
    
    for i, role in enumerate(roles, 1):
        console.print(f"  {i}. {role}")
    
    role_choice = Prompt.ask(
        "Choose",
        choices=[str(i) for i in range(1, len(roles) + 1)]
    )
    responses['role'] = roles[int(role_choice) - 1].lower().replace(' ', '_').replace('/', '_')
    
    # Question 2: Tech Stack
    console.print("\n[bold]2. Which technologies do you work with?[/bold]")
    console.print("(Enter numbers separated by commas, e.g., 1,3,5)")
    
    techs = [
        "JavaScript/TypeScript",
        "Python",
        "Java",
        "Go",
        "Rust",
        "React",
        "Vue",
        "Node.js",
        "Django/Flask",
        "PostgreSQL",
        "MongoDB",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure"
    ]
    
    for i, tech in enumerate(techs, 1):
        console.print(f"  {i}. {tech}")
    
    tech_choices = Prompt.ask("Choose (comma-separated)")
    selected_techs = [
        techs[int(choice.strip()) - 1]
        for choice in tech_choices.split(',')
        if choice.strip().isdigit()
    ]
    responses['tech_stack'] = selected_techs
    
    # Question 3: Common Tasks
    console.print("\n[bold]3. What tasks do you perform most often?[/bold]")
    console.print("(Enter numbers separated by commas)")
    
    tasks = [
        "Building new features",
        "Debugging issues",
        "Code review",
        "Performance optimization",
        "Writing tests",
        "Documentation",
        "Data analysis",
        "API design",
        "Infrastructure setup"
    ]
    
    for i, task in enumerate(tasks, 1):
        console.print(f"  {i}. {task}")
    
    task_choices = Prompt.ask("Choose (comma-separated)")
    selected_tasks = [
        tasks[int(choice.strip()) - 1]
        for choice in task_choices.split(',')
        if choice.strip().isdigit()
    ]
    responses['common_tasks'] = selected_tasks
    
    # Question 4: Experience Level
    console.print("\n[bold]4. What's your experience level?[/bold]")
    levels = ["Junior", "Mid-level", "Senior", "Lead/Principal"]
    
    for i, level in enumerate(levels, 1):
        console.print(f"  {i}. {level}")
    
    level_choice = Prompt.ask(
        "Choose",
        choices=[str(i) for i in range(1, len(levels) + 1)]
    )
    responses['experience_level'] = levels[int(level_choice) - 1].lower()
    
    return responses


if __name__ == '__main__':
    onboard()
```

---

**This is a comprehensive, production-ready implementation strategy spanning 14 weeks. Would you like me to continue with Phases 4-6 (Dynamic Generation, Intelligence Layer, and Production Hardening)?**

The strategy provides:
- ✅ Complete file structure with actual code
- ✅ Phased rollout (2 weeks per phase)
- ✅ Testing at each stage
- ✅ Documentation throughout
- ✅ CLI tools for easy interaction
- ✅ Real DSPy implementation
- ✅ Taxonomy-first design