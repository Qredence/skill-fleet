# Refactored Structure

## Directory Layout

```
src/workflow/
├── __init__.py
├── signatures.py          # DSPy signatures (already exists)
├── modules.py             # DSPy modules for each step
├── programs.py            # DSPy programs (complete workflows)
├── skill_creator.py       # High-level orchestrator
└── feedback.py            # HITL feedback handlers
```

---

## File 1: `src/workflow/modules.py`

**DSPy Modules - Each step as a reusable component**

```python
"""DSPy modules for skill creation workflow steps.

Each module encapsulates one step of the workflow with its own
logic, validation, and error handling.
"""

import dspy
import json
from typing import Dict, List, Optional, Tuple
import logging

from .signatures import (
    UnderstandTaskForSkill,
    PlanSkillStructure,
    InitializeSkillSkeleton,
    EditSkillContent,
    PackageSkillForApproval,
    IterateSkillWithFeedback
)

logger = logging.getLogger(__name__)


class UnderstandModule(dspy.Module):
    """Module for Step 1: Understanding task and mapping to taxonomy."""
    
    def __init__(self):
        super().__init__()
        self.understand = dspy.ChainOfThought(UnderstandTaskForSkill)
    
    def forward(
        self,
        task_description: str,
        existing_skills: List[str],
        taxonomy_structure: Dict
    ) -> Dict:
        """Analyze task and determine taxonomy placement.
        
        Returns:
            Dict with task_intent, taxonomy_path, parent_skills, 
            dependency_analysis, and confidence_score
        """
        result = self.understand(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2)
        )
        
        return {
            'task_intent': result.task_intent,
            'taxonomy_path': result.taxonomy_path.strip(),
            'parent_skills': result.parent_skills,
            'dependency_analysis': result.dependency_analysis,
            'confidence_score': float(result.confidence_score)
        }


class PlanModule(dspy.Module):
    """Module for Step 2: Planning skill structure."""
    
    def __init__(self):
        super().__init__()
        self.plan = dspy.ChainOfThought(PlanSkillStructure)
    
    def forward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: List[Dict],
        dependency_analysis: str
    ) -> Dict:
        """Design skill structure with dependencies.
        
        Returns:
            Dict with skill_metadata, dependencies, capabilities,
            resource_requirements, compatibility_constraints,
            and composition_strategy
        """
        result = self.plan(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis
        )
        
        return {
            'skill_metadata': json.loads(result.skill_metadata),
            'dependencies': json.loads(result.dependencies),
            'capabilities': json.loads(result.capabilities),
            'resource_requirements': result.resource_requirements,
            'compatibility_constraints': result.compatibility_constraints,
            'composition_strategy': result.composition_strategy
        }


class InitializeModule(dspy.Module):
    """Module for Step 3: Initializing skill skeleton."""
    
    def __init__(self):
        super().__init__()
        self.initialize = dspy.ChainOfThought(InitializeSkillSkeleton)
    
    def forward(
        self,
        skill_metadata: Dict,
        capabilities: List[str],
        taxonomy_path: str
    ) -> Dict:
        """Create skill file structure.
        
        Returns:
            Dict with skill_skeleton and validation_checklist
        """
        result = self.initialize(
            skill_metadata=json.dumps(skill_metadata, indent=2),
            capabilities=json.dumps(capabilities, indent=2),
            taxonomy_path=taxonomy_path
        )
        
        return {
            'skill_skeleton': json.loads(result.skill_skeleton),
            'validation_checklist': result.validation_checklist
        }


class EditModule(dspy.Module):
    """Module for Step 4: Editing skill content."""
    
    def __init__(self):
        super().__init__()
        self.edit = dspy.ChainOfThought(EditSkillContent)
    
    def forward(
        self,
        skill_skeleton: Dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: Optional[str] = None
    ) -> Dict:
        """Generate comprehensive skill content.
        
        Args:
            skill_skeleton: Directory structure
            parent_skills: Context from related skills
            composition_strategy: How skill composes with others
            revision_feedback: Optional feedback for regeneration
        
        Returns:
            Dict with skill_content, capability_implementations,
            usage_examples, best_practices, and integration_guide
        """
        # TODO: Incorporate revision_feedback into prompt
        result = self.edit(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy
        )
        
        return {
            'skill_content': result.skill_content,
            'capability_implementations': result.capability_implementations,
            'usage_examples': result.usage_examples,
            'best_practices': result.best_practices,
            'integration_guide': result.integration_guide
        }


class PackageModule(dspy.Module):
    """Module for Step 5: Packaging and validation."""
    
    def __init__(self):
        super().__init__()
        self.package = dspy.ChainOfThought(PackageSkillForApproval)
    
    def forward(
        self,
        skill_content: str,
        skill_metadata: Dict,
        taxonomy_path: str,
        capability_implementations: str
    ) -> Dict:
        """Validate and package skill for approval.
        
        Returns:
            Dict with validation_report, integration_tests,
            packaging_manifest, and quality_score
        """
        result = self.package(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations
        )
        
        return {
            'validation_report': json.loads(result.validation_report),
            'integration_tests': result.integration_tests,
            'packaging_manifest': result.packaging_manifest,
            'quality_score': float(result.quality_score)
        }


class IterateModule(dspy.Module):
    """Module for Step 6: Iteration with human feedback."""
    
    def __init__(self):
        super().__init__()
        self.iterate = dspy.ChainOfThought(IterateSkillWithFeedback)
    
    def forward(
        self,
        packaged_skill: str,
        validation_report: Dict,
        human_feedback: str,
        usage_analytics: Optional[Dict] = None
    ) -> Dict:
        """Process human feedback and determine next steps.
        
        Returns:
            Dict with approval_status, revision_plan,
            evolution_metadata, and next_steps
        """
        result = self.iterate(
            packaged_skill=packaged_skill,
            validation_report=json.dumps(validation_report, indent=2),
            human_feedback=human_feedback,
            usage_analytics=json.dumps(usage_analytics or {})
        )
        
        return {
            'approval_status': result.approval_status.strip().lower(),
            'revision_plan': result.revision_plan,
            'evolution_metadata': json.loads(result.evolution_metadata),
            'next_steps': result.next_steps
        }
```

---

## File 2: `src/workflow/programs.py`

**DSPy Programs - Complete workflows**

```python
"""DSPy programs for complete skill creation workflows.

Programs compose multiple modules into end-to-end workflows
with proper error handling and state management.
"""

import dspy
from typing import Dict, Optional
import logging

from .modules import (
    UnderstandModule,
    PlanModule,
    InitializeModule,
    EditModule,
    PackageModule,
    IterateModule
)

logger = logging.getLogger(__name__)


class SkillCreationProgram(dspy.Module):
    """Complete skill creation program (Steps 1-5).
    
    This program executes the core creation workflow without
    the HITL iteration step.
    """
    
    def __init__(self):
        super().__init__()
        self.understand = UnderstandModule()
        self.plan = PlanModule()
        self.initialize = InitializeModule()
        self.edit = EditModule()
        self.package = PackageModule()
    
    def forward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: callable
    ) -> Dict:
        """Execute Steps 1-5 of skill creation.
        
        Args:
            task_description: User's task description
            existing_skills: Currently mounted skills
            taxonomy_structure: Relevant taxonomy branches
            parent_skills_getter: Function to get parent skills for a path
        
        Returns:
            Dict with all outputs from Steps 1-5
        """
        
        # Step 1: UNDERSTAND
        understanding = self.understand(
            task_description=task_description,
            existing_skills=existing_skills,
            taxonomy_structure=taxonomy_structure
        )
        
        # Step 2: PLAN
        parent_skills = parent_skills_getter(understanding['taxonomy_path'])
        plan = self.plan(
            task_intent=understanding['task_intent'],
            taxonomy_path=understanding['taxonomy_path'],
            parent_skills=parent_skills,
            dependency_analysis=understanding['dependency_analysis']
        )
        
        # Step 3: INITIALIZE
        skeleton = self.initialize(
            skill_metadata=plan['skill_metadata'],
            capabilities=plan['capabilities'],
            taxonomy_path=understanding['taxonomy_path']
        )
        
        # Step 4: EDIT
        content = self.edit(
            skill_skeleton=skeleton['skill_skeleton'],
            parent_skills=understanding['parent_skills'],
            composition_strategy=plan['composition_strategy']
        )
        
        # Step 5: PACKAGE
        package = self.package(
            skill_content=content['skill_content'],
            skill_metadata=plan['skill_metadata'],
            taxonomy_path=understanding['taxonomy_path'],
            capability_implementations=content['capability_implementations']
        )
        
        return {
            'understanding': understanding,
            'plan': plan,
            'skeleton': skeleton,
            'content': content,
            'package': package
        }


class SkillRevisionProgram(dspy.Module):
    """Program for revising existing skill content (Steps 4-5).
    
    Used when iteration requires content regeneration.
    """
    
    def __init__(self):
        super().__init__()
        self.edit = EditModule()
        self.package = PackageModule()
    
    def forward(
        self,
        skeleton: Dict,
        parent_skills: str,
        composition_strategy: str,
        plan: Dict,
        taxonomy_path: str,
        revision_feedback: Optional[str] = None
    ) -> Dict:
        """Regenerate and repackage skill content.
        
        Returns:
            Dict with revised content and package
        """
        
        # Step 4: EDIT (with feedback)
        content = self.edit(
            skill_skeleton=skeleton['skill_skeleton'],
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
            revision_feedback=revision_feedback
        )
        
        # Step 5: PACKAGE
        package = self.package(
            skill_content=content['skill_content'],
            skill_metadata=plan['skill_metadata'],
            taxonomy_path=taxonomy_path,
            capability_implementations=content['capability_implementations']
        )
        
        return {
            'content': content,
            'package': package
        }


class QuickSkillProgram(dspy.Module):
    """Streamlined program for rapid skill generation.
    
    Optimized for speed with minimal validation, useful for
    bootstrap and development scenarios.
    """
    
    def __init__(self):
        super().__init__()
        self.understand = UnderstandModule()
        self.plan = PlanModule()
        self.edit = EditModule()
    
    def forward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: callable
    ) -> Dict:
        """Quick skill generation (Steps 1-2-4 only).
        
        Skips initialization and packaging for speed.
        """
        
        # Step 1: UNDERSTAND
        understanding = self.understand(
            task_description=task_description,
            existing_skills=existing_skills,
            taxonomy_structure=taxonomy_structure
        )
        
        # Step 2: PLAN
        parent_skills = parent_skills_getter(understanding['taxonomy_path'])
        plan = self.plan(
            task_intent=understanding['task_intent'],
            taxonomy_path=understanding['taxonomy_path'],
            parent_skills=parent_skills,
            dependency_analysis=understanding['dependency_analysis']
        )
        
        # Step 4: EDIT (skip initialization)
        skeleton = {
            'skill_skeleton': {
                'root_path': f"skills/{understanding['taxonomy_path']}/",
                'files': [],
                'directories': ['capabilities/', 'examples/', 'tests/', 'resources/']
            }
        }
        
        content = self.edit(
            skill_skeleton=skeleton['skill_skeleton'],
            parent_skills=understanding['parent_skills'],
            composition_strategy=plan['composition_strategy']
        )
        
        return {
            'understanding': understanding,
            'plan': plan,
            'content': content
        }
```

---

## File 3: `src/workflow/feedback.py`

**Human-in-the-loop feedback handlers**

```python
"""Human feedback handlers for skill approval workflow."""

import json
from typing import Dict, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class FeedbackHandler(ABC):
    """Abstract base class for feedback handlers."""
    
    @abstractmethod
    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: Dict
    ) -> str:
        """Get human feedback on packaged skill.
        
        Returns:
            JSON string with feedback structure:
            {
                "status": "approved" | "needs_revision" | "rejected",
                "comments": "...",
                "reviewer": "...",
                "timestamp": "..."
            }
        """
        pass


class AutoApprovalHandler(FeedbackHandler):
    """Automatic approval based on validation results."""
    
    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: Dict
    ) -> str:
        """Auto-approve if validation passed, otherwise request revision."""
        
        if validation_report.get('passed'):
            return json.dumps({
                "status": "approved",
                "comments": "Validation passed - auto-approved",
                "reviewer": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            errors = validation_report.get('errors', [])
            return json.dumps({
                "status": "needs_revision",
                "comments": f"Validation errors: {', '.join(errors[:3])}",
                "suggested_changes": errors,
                "reviewer": "system",
                "timestamp": datetime.utcnow().isoformat()
            })


class CLIFeedbackHandler(FeedbackHandler):
    """Interactive CLI feedback collection."""
    
    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: Dict
    ) -> str:
        """Collect feedback via command-line prompts."""
        
        from rich.console import Console
        from rich.prompt import Prompt, Confirm
        from rich.table import Table
        
        console = Console()
        
        # Display validation results
        console.print("\n[bold cyan]Skill Review[/bold cyan]")
        
        validation_status = "✓ PASSED" if validation_report.get('passed') else "✗ FAILED"
        console.print(f"Validation: {validation_status}")
        console.print(f"Quality Score: {validation_report.get('quality_score', 0):.2f}")
        
        if validation_report.get('warnings'):
            console.print(f"\n[yellow]Warnings:[/yellow]")
            for warning in validation_report['warnings'][:5]:
                console.print(f"  ⚠ {warning}")
        
        if validation_report.get('errors'):
            console.print(f"\n[red]Errors:[/red]")
            for error in validation_report['errors'][:5]:
                console.print(f"  ✗ {error}")
        
        # Get decision
        console.print("\n[bold]Review Decision:[/bold]")
        console.print("1. Approve")
        console.print("2. Request Revision")
        console.print("3. Reject")
        
        choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")
        
        status_map = {"1": "approved", "2": "needs_revision", "3": "rejected"}
        status = status_map[choice]
        
        comments = Prompt.ask("Comments (optional)", default="")
        reviewer = Prompt.ask("Reviewer name", default="human")
        
        return json.dumps({
            "status": status,
            "comments": comments,
            "reviewer": reviewer,
            "timestamp": datetime.utcnow().isoformat()
        })


class WebhookFeedbackHandler(FeedbackHandler):
    """Send skill for review via webhook and wait for response."""
    
    def __init__(self, webhook_url: str, timeout: int = 3600):
        self.webhook_url = webhook_url
        self.timeout = timeout
    
    def get_feedback(
        self,
        packaging_manifest: str,
        validation_report: Dict
    ) -> str:
        """Post to webhook and wait for approval response."""
        
        import requests
        import time
        
        # Post review request
        review_data = {
            "manifest": packaging_manifest,
            "validation": validation_report,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=review_data,
                timeout=10
            )
            review_id = response.json().get('review_id')
            
            # Poll for decision
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                status_response = requests.get(
                    f"{self.webhook_url}/{review_id}",
                    timeout=5
                )
                
                if status_response.json().get('status') != 'pending':
                    return json.dumps(status_response.json())
                
                time.sleep(30)  # Poll every 30 seconds
            
            # Timeout
            return json.dumps({
                "status": "needs_revision",
                "comments": "Review timeout - please review manually",
                "reviewer": "system",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Webhook feedback error: {e}")
            return json.dumps({
                "status": "needs_revision",
                "comments": f"Feedback system error: {str(e)}",
                "reviewer": "system",
                "timestamp": datetime.utcnow().isoformat()
            })


def create_feedback_handler(handler_type: str = "auto", **kwargs) -> FeedbackHandler:
    """Factory function for creating feedback handlers.
    
    Args:
        handler_type: Type of handler ("auto", "cli", "webhook")
        **kwargs: Additional arguments for specific handlers
    
    Returns:
        FeedbackHandler instance
    """
    handlers = {
        "auto": AutoApprovalHandler,
        "cli": CLIFeedbackHandler,
        "webhook": WebhookFeedbackHandler
    }
    
    handler_class = handlers.get(handler_type)
    if not handler_class:
        raise ValueError(f"Unknown handler type: {handler_type}")
    
    return handler_class(**kwargs)
```

---

## File 4: `src/workflow/skill_creator.py` (Refactored)

**High-level orchestrator - Much cleaner!**

```python
"""High-level skill creation orchestrator.

This module provides the main interface for skill creation,
coordinating DSPy programs, taxonomy operations, and feedback.
"""

import dspy
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

from .programs import SkillCreationProgram, SkillRevisionProgram
from .modules import IterateModule
from .feedback import FeedbackHandler, create_feedback_handler
from ..taxonomy.manager import TaxonomyManager
from ..validators.skill_validator import SkillValidator

logger = logging.getLogger(__name__)


class SkillCreator:
    """High-level orchestrator for skill creation.
    
    Coordinates DSPy programs, taxonomy management, validation,
    and human feedback to create skills end-to-end.
    """
    
    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        feedback_handler: Optional[FeedbackHandler] = None,
        validator: Optional[SkillValidator] = None,
        lm: Optional[dspy.LM] = None,
        verbose: bool = True
    ):
        """Initialize skill creator.
        
        Args:
            taxonomy_manager: Taxonomy management instance
            feedback_handler: Handler for human feedback (default: auto-approval)
            validator: Skill validator (creates default if None)
            lm: Language model (uses dspy.settings if None)
            verbose: Whether to print progress
        """
        self.taxonomy = taxonomy_manager
        self.verbose = verbose
        
        # Initialize feedback handler
        self.feedback_handler = feedback_handler or create_feedback_handler("auto")
        
        # Initialize validator
        self.validator = validator or SkillValidator(
            schema_path=taxonomy_manager.skills_root / "taxonomy_meta.json"
        )
        
        # Configure LM
        if lm:
            dspy.settings.configure(lm=lm)
        
        # Initialize DSPy programs
        self.creation_program = SkillCreationProgram()
        self.revision_program = SkillRevisionProgram()
        self.iterate_module = IterateModule()
        
        # Statistics
        self.stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "avg_iterations": 0.0
        }
    
    def create_skill(
        self,
        task_description: str,
        user_context: Dict,
        max_iterations: int = 3
    ) -> Dict:
        """Create a new skill from task description.
        
        Args:
            task_description: User's task or capability requirement
            user_context: Dict with user_id and other context
            max_iterations: Maximum HITL iterations
        
        Returns:
            Result dictionary with status and metadata
        """
        self.stats["total"] += 1
        
        if self.verbose:
            self._print_header("Skill Creation")
            print(f"📝 Task: {task_description}")
            print(f"👤 User: {user_context.get('user_id', 'unknown')}\n")
        
        try:
            # Execute main creation program
            result = self.creation_program(
                task_description=task_description,
                existing_skills=self.taxonomy.get_mounted_skills(
                    user_context.get('user_id', 'default')
                ),
                taxonomy_structure=self.taxonomy.get_relevant_branches(
                    task_description
                ),
                parent_skills_getter=self.taxonomy.get_parent_skills
            )
            
            understanding = result['understanding']
            plan = result['plan']
            package = result['package']
            
            # Check if skill exists
            if self.taxonomy.skill_exists(understanding['taxonomy_path']):
                return {"status": "exists", "path": understanding['taxonomy_path']}
            
            # Validate dependencies
            if not self._validate_plan(plan):
                return {"status": "error", "message": "Invalid dependencies"}
            
            # Check initial validation
            if not package['validation_report']['passed']:
                return {
                    "status": "validation_failed",
                    "errors": package['validation_report'].get('errors', [])
                }
            
            # HITL iteration
            approval = self._iterate_for_approval(
                result=result,
                max_iterations=max_iterations
            )
            
            if approval['status'] == 'approved':
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            return approval
            
        except Exception as e:
            logger.exception("Error creating skill")
            self.stats["failed"] += 1
            return {"status": "error", "message": str(e)}
    
    def _validate_plan(self, plan: Dict) -> bool:
        """Validate skill plan (dependencies, circular refs)."""
        
        dep_ids = [d if isinstance(d, str) else d.get('skill_id') 
                   for d in plan['dependencies']]
        
        # Check dependencies exist
        valid, missing = self.taxonomy.validate_dependencies(dep_ids)
        if not valid:
            if self.verbose:
                print(f"❌ Missing dependencies: {missing}")
            return False
        
        # Check for cycles
        has_cycle, path = self.taxonomy.detect_circular_dependencies(
            plan['skill_metadata']['skill_id'],
            dep_ids
        )
        if has_cycle:
            if self.verbose:
                print(f"❌ Circular dependency: {' → '.join(path)}")
            return False
        
        return True
    
    def _iterate_for_approval(
        self,
        result: Dict,
        max_iterations: int
    ) -> Dict:
        """Iterate with human feedback until approved or max iterations."""
        
        understanding = result['understanding']
        plan = result['plan']
        skeleton = result['skeleton']
        content = result['content']
        package = result['package']
        
        for iteration in range(1, max_iterations + 1):
            if self.verbose:
                print(f"\n📋 Iteration {iteration}/{max_iterations}")
            
            # Get human feedback
            feedback = self.feedback_handler.get_feedback(
                package['packaging_manifest'],
                package['validation_report']
            )
            
            # Process feedback
            decision = self.iterate_module(
                packaged_skill=package['packaging_manifest'],
                validation_report=package['validation_report'],
                human_feedback=feedback
            )
            
            if decision['approval_status'] == 'approved':
                # Register skill
                success = self.taxonomy.register_skill(
                    path=understanding['taxonomy_path'],
                    metadata=plan['skill_metadata'],
                    content=content['skill_content'],
                    evolution=decision['evolution_metadata']
                )
                
                if success:
                    if self.verbose:
                        print(f"✅ Skill approved and registered!")
                    
                    return {
                        "status": "approved",
                        "skill_id": plan['skill_metadata']['skill_id'],
                        "path": understanding['taxonomy_path'],
                        "version": plan['skill_metadata']['version'],
                        "quality_score": package['quality_score'],
                        "iterations": iteration
                    }
                else:
                    return {"status": "error", "message": "Registration failed"}
            
            elif decision['approval_status'] == 'needs_revision':
                if iteration < max_iterations:
                    # Revise and repackage
                    if self.verbose:
                        print("🔄 Revising skill...")
                    
                    revised = self.revision_program(
                        skeleton=skeleton,
                        parent_skills=understanding['parent_skills'],
                        composition_strategy=plan['composition_strategy'],
                        plan=plan,
                        taxonomy_path=understanding['taxonomy_path'],
                        revision_feedback=decision['revision_plan']
                    )
                    
                    content = revised['content']
                    package = revised['package']
            
            else:  # rejected
                return {
                    "status": "rejected",
                    "reason": decision['revision_plan'],
                    "iterations": iteration
                }
        
        return {
            "status": "max_iterations",
            "message": f"Not approved after {max_iterations} iterations"
        }
    
    def _print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def get_stats(self) -> Dict:
        """Get creation statistics."""
        return self.stats.copy()


# Convenience function
def create_skill(
    task_description: str,
    user_id: str = "default",
    skills_root: str = "./skills",
    verbose: bool = True
) -> Dict:
    """Convenience function for quick skill creation."""
    from ..taxonomy.manager import TaxonomyManager
    
    taxonomy = TaxonomyManager(Path(skills_root))
    creator = SkillCreator(taxonomy_manager=taxonomy, verbose=verbose)
    
    return creator.create_skill(
        task_description=task_description,
        user_context={"user_id": user_id}
    )
```

---

## Summary of Improvements

### Before (Monolithic)
- ❌ 600+ lines in one file
- ❌ Mixed concerns (orchestration + logic)
- ❌ Hard to test individual steps
- ❌ Difficult to extend/customize

### After (Modular)
- ✅ **4 focused files** (~150-200 lines each)
- ✅ **Clear separation**: Modules → Programs → Orchestrator
- ✅ **Testable**: Each module/program is independent
- ✅ **Extensible**: Easy to add new programs or feedback handlers
- ✅ **DSPy best practices**: Proper use of Module and Program abstractions
- ✅ **Reusable**: Mix and match modules for different workflows

### Benefits
1. **Testing**: Test each module in isolation
2. **Optimization**: Optimize individual programs with DSPy
3. **Customization**: Replace feedback handlers easily
4. **Maintenance**: Changes are localized
5. **Readability**: Each file has single responsibility

This is much better! 🎉