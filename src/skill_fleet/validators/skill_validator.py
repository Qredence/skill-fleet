"""Skill validation utilities for taxonomy and agentskills.io compliance."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of a validation step."""

    passed: bool
    errors: list[str]
    warnings: list[str]


class SkillValidator:
    """Validates skill metadata, directory structure, and agentskills.io compliance."""

    _TYPE_ENUM = {
        "cognitive",
        "technical",
        "domain",
        "tool",
        "mcp",
        "specialization",
        "task_focus",
        "memory",
    }
    _WEIGHT_ENUM = {"lightweight", "medium", "heavyweight"}
    _PRIORITY_ENUM = {"always", "task_specific", "on_demand", "dormant"}

    # Pre-compiled regex patterns for performance
    _SKILL_ID_PATTERN = re.compile(r"^[a-z0-9_]+(?:/[a-z0-9_]+)*$")
    _SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
    _SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    _SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

    def __init__(self, skills_root: Path) -> None:
        self.skills_root = Path(skills_root)
        self.required_files = ["metadata.json", "SKILL.md"]
        self.required_dirs = ["capabilities", "examples", "tests", "resources"]
        self._load_template_overrides()

    def _resolve_existing_path_within_dir(
        self, *, base_dir: Path, candidate: Path, label: str
    ) -> tuple[Path | None, str | None]:
        """Resolve a path and enforce it stays within base_dir.

        This is defense-in-depth against path traversal and symlink escapes.
        The caller should pass a *resolved* base_dir.
        """
        if candidate.is_symlink():
            return None, f"{label} must not be a symlink"

        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            return None, f"{label} not found"

        try:
            resolved.relative_to(base_dir)
        except ValueError:
            return None, f"{label} path not allowed"

        return resolved, None

    def _resolve_existing_path_within_skills_root(
        self, *, candidate: Path, label: str
    ) -> tuple[Path | None, str | None]:
        """Resolve a path and enforce it stays within skills_root."""
        skills_root_resolved = self.skills_root.resolve()
        candidate_resolved, err = self._resolve_existing_path_within_dir(
            base_dir=skills_root_resolved,
            candidate=candidate,
            label=label,
        )
        if err is not None:
            return None, err
        return candidate_resolved, None

    def _load_template_overrides(self) -> None:
        template_path = self.skills_root / "_templates" / "skill_template.json"
        template_resolved, err = self._resolve_existing_path_within_skills_root(
            candidate=template_path,
            label="skill_template.json",
        )
        if err is not None:
            return
        try:
            template = json.loads(template_resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        directory_structure = template.get("directory_structure")
        if isinstance(directory_structure, list):
            # Only keep safe, single-segment directory names
            safe_dirs: list[str] = []
            for d in directory_structure:
                if not isinstance(d, str):
                    continue
                # Normalize any trailing slash before validation
                d_normalized = d.rstrip("/")
                if d_normalized and self._is_safe_path_component(d_normalized):
                    safe_dirs.append(d_normalized)
            if safe_dirs:
                self.required_dirs = safe_dirs

        required_files = template.get("required_files")
        if isinstance(required_files, list):
            # Only keep safe, single-segment file names
            safe_files: list[str] = []
            for f in required_files:
                if not isinstance(f, str):
                    continue
                if self._is_safe_path_component(f):
                    safe_files.append(f)
            if safe_files:
                self.required_files = safe_files

    def validate_metadata(self, metadata: dict[str, Any]) -> ValidationResult:
        """Validate required metadata fields and their basic formats."""
        errors: list[str] = []
        warnings: list[str] = []

        required_fields = [
            "skill_id",
            "version",
            "type",
            "weight",
            "load_priority",
            "dependencies",
            "capabilities",
        ]

        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required metadata field: {field}")

        if errors:
            return ValidationResult(False, errors, warnings)

        skill_id = str(metadata.get("skill_id", ""))
        if not self._validate_skill_id_format(skill_id):
            errors.append(f"Invalid skill_id format: {skill_id}")

        version = str(metadata.get("version", ""))
        if not self._validate_semver(version):
            errors.append(f"Invalid version format: {version}")

        skill_type = str(metadata.get("type", ""))
        if skill_type not in self._TYPE_ENUM:
            errors.append(f"Invalid type: {skill_type}")

        weight = str(metadata.get("weight", ""))
        if weight not in self._WEIGHT_ENUM:
            errors.append(f"Invalid weight: {weight}")

        load_priority = str(metadata.get("load_priority", ""))
        if load_priority not in self._PRIORITY_ENUM:
            errors.append(f"Invalid load_priority: {load_priority}")

        dependencies = metadata.get("dependencies")
        if not isinstance(dependencies, list):
            errors.append("dependencies must be a list")

        capabilities = metadata.get("capabilities")
        if not isinstance(capabilities, list):
            errors.append("capabilities must be a list")
        elif len(capabilities) == 0:
            warnings.append("capabilities list is empty")

        if isinstance(capabilities, list) and weight in self._WEIGHT_ENUM:
            if not self._validate_weight_capabilities(weight, capabilities):
                warnings.append(
                    f"Weight '{weight}' may not match capability count ({len(capabilities)})"
                )

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_structure(self, skill_dir: Path) -> ValidationResult:
        """Validate that a directory skill has the expected files and folders.

        Security: This method implements defense-in-depth against path traversal:
        1. Resolves skill_dir and validates it's within skills_root
        2. Validates each filename/dirname component before use
        3. Re-validates resolved paths are within skill_dir
        4. Uses _is_safe_path_component() to reject malicious patterns
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Resolve and constrain skill_dir to the configured skills_root to
        # protect against path traversal and misuse of this method.
        skill_dir_resolved = skill_dir.resolve()
        skills_root_resolved = self.skills_root.resolve()
        try:
            skill_dir_resolved.relative_to(skills_root_resolved)
        except ValueError:
            errors.append("Skill directory not allowed")
            return ValidationResult(False, errors, warnings)

        for filename in self.required_files:
            # Validate filename to prevent path traversal attacks
            if not self._is_safe_path_component(filename):
                errors.append(f"Invalid required file name: {filename}")
                continue
            file_path = (skill_dir_resolved / filename).resolve()
            # Ensure resolved path is within skill_dir
            try:
                file_path.relative_to(skill_dir_resolved)
            except ValueError:
                errors.append(f"Invalid required file path: {filename}")
                continue
            if not file_path.exists():
                errors.append(f"Missing required file: {filename}")

        for dirname in self.required_dirs:
            # Validate dirname to prevent path traversal attacks
            if not self._is_safe_path_component(dirname):
                errors.append(f"Invalid required directory name: {dirname}")
                continue
            dir_path = (skill_dir_resolved / dirname).resolve()
            # Ensure resolved path is within skill_dir
            try:
                dir_path.relative_to(skill_dir_resolved)
            except ValueError:
                errors.append(f"Invalid required directory path: {dirname}")
                continue
            if not dir_path.is_dir():
                errors.append(f"Missing required directory: {dirname}")

        metadata_path = (skill_dir_resolved / "metadata.json").resolve()
        try:
            metadata_path.relative_to(skill_dir_resolved)
        except ValueError:
            errors.append("Invalid metadata.json path")
            return ValidationResult(False, errors, warnings)
        if metadata_path.exists():
            try:
                json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON in metadata.json: {exc}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_documentation(self, skill_md_path: Path) -> ValidationResult:
        """Validate expected documentation sections and basic markdown structure."""
        errors: list[str] = []
        warnings: list[str] = []

        skill_md_resolved, err = self._resolve_existing_path_within_skills_root(
            candidate=skill_md_path,
            label="SKILL.md",
        )
        if err is not None:
            return ValidationResult(False, [err], [])

        content = skill_md_resolved.read_text(encoding="utf-8")

        # Check for agentskills.io compliant frontmatter
        if not content.startswith("---"):
            warnings.append("Missing YAML frontmatter (agentskills.io compliance)")

        # Get body content (after frontmatter)
        body_content = content
        if content.startswith("---"):
            end_marker = content.find("---", 3)
            if end_marker != -1:
                body_content = content[end_marker + 3 :]

        required_sections = [
            "## Overview",
            "## Capabilities",
            "## Dependencies",
            "## Usage Examples",
        ]

        for section in required_sections:
            if section not in body_content:
                warnings.append(f"Missing section: {section}")

        if "```" not in body_content:
            warnings.append("No code blocks found")

        if len(body_content.strip()) < 200:
            warnings.append("Documentation is very brief")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_frontmatter(self, skill_md_path: Path) -> ValidationResult:
        """Validate SKILL.md has valid agentskills.io compliant YAML frontmatter.

        Per agentskills.io spec:
        - name: required, 1-64 chars, lowercase alphanumeric + hyphens
        - description: required, 1-1024 chars
        - license: optional
        - compatibility: optional, max 500 chars
        - metadata: optional, key-value pairs
        - allowed-tools: optional, space-delimited list
        """
        errors: list[str] = []
        warnings: list[str] = []

        skill_md_resolved, err = self._resolve_existing_path_within_skills_root(
            candidate=skill_md_path,
            label="SKILL.md",
        )
        if err is not None:
            return ValidationResult(False, [err], [])

        content = skill_md_resolved.read_text(encoding="utf-8")

        # Check for frontmatter
        if not content.startswith("---"):
            return ValidationResult(False, ["Missing YAML frontmatter"], [])

        # Find closing ---
        end_marker = content.find("---", 3)
        if end_marker == -1:
            return ValidationResult(False, ["Invalid YAML frontmatter (no closing ---)"], [])

        yaml_content = content[3:end_marker].strip()

        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return ValidationResult(False, [f"Invalid YAML in frontmatter: {e}"], [])

        if not isinstance(frontmatter, dict):
            return ValidationResult(False, ["Frontmatter must be a YAML mapping"], [])

        # Validate required fields
        if "name" not in frontmatter:
            errors.append("Missing required field: name")
        else:
            name = str(frontmatter["name"])
            name_valid, name_error = self._validate_skill_name(name)
            if not name_valid:
                errors.append(f"Invalid name: {name_error}")

        if "description" not in frontmatter:
            errors.append("Missing required field: description")
        else:
            description = str(frontmatter["description"])
            if len(description) < 1:
                errors.append("Description cannot be empty")
            elif len(description) > 1024:
                errors.append(f"Description exceeds 1024 characters ({len(description)})")

        # Validate optional fields
        if "compatibility" in frontmatter:
            compat = str(frontmatter["compatibility"])
            if len(compat) > 500:
                warnings.append(f"Compatibility field exceeds 500 characters ({len(compat)})")

        if "metadata" in frontmatter:
            if not isinstance(frontmatter["metadata"], dict):
                warnings.append("metadata field should be a key-value mapping")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_skill_name(self, name: str) -> tuple[bool, str | None]:
        """Validate skill name per agentskills.io spec.

        Requirements:
        - 1-64 characters
        - Lowercase letters, numbers, and hyphens only
        - Must not start or end with hyphen
        - No consecutive hyphens
        """
        if not name:
            return False, "Name cannot be empty"

        if len(name) > 64:
            return False, f"Name exceeds 64 characters (got {len(name)})"

        if not self._SKILL_NAME_PATTERN.match(name):
            return False, "Name must be lowercase alphanumeric with single hyphens between segments"

        return True, None

    def validate_examples(self, examples_path: Path) -> ValidationResult:
        """Validate example markdown files under a skill's examples directory."""
        errors: list[str] = []
        warnings: list[str] = []

        examples_resolved, err = self._resolve_existing_path_within_skills_root(
            candidate=examples_path,
            label="Examples directory",
        )
        if err is not None:
            return ValidationResult(False, [err], [])
        if not examples_resolved.is_dir():
            return ValidationResult(False, ["Examples directory not found"], [])

        example_files = list(examples_resolved.glob("*.md"))
        if len(example_files) == 0:
            warnings.append("No example markdown files found")
        else:
            for example_file in example_files:
                if example_file.is_symlink():
                    warnings.append(f"Example {example_file.name} is a symlink and was skipped")
                    continue
                try:
                    example_file_resolved = example_file.resolve()
                    example_file_resolved.relative_to(examples_resolved)
                except (FileNotFoundError, ValueError):
                    warnings.append(f"Example {example_file.name} path not allowed and was skipped")
                    continue

                content = example_file_resolved.read_text(encoding="utf-8")
                if "```" not in content:
                    warnings.append(f"Example {example_file.name} contains no code blocks")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_naming_conventions(self, skill_id: str, path: str) -> ValidationResult:
        """Validate that skill_id matches its on-disk taxonomy path and naming rules."""
        errors: list[str] = []
        warnings: list[str] = []

        if skill_id != path:
            warnings.append(f"skill_id '{skill_id}' does not match path '{path}'")

        if not self._validate_skill_id_format(skill_id):
            errors.append(f"skill_id '{skill_id}' should use lowercase/underscore path segments")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_complete(self, skill_path: Path) -> dict[str, Any]:
        """Run the full validation suite for either a directory-skill or file-skill."""
        results = {"passed": True, "checks": [], "warnings": [], "errors": []}

        skill_path = skill_path.resolve()
        skills_root_resolved = self.skills_root.resolve()
        try:
            # Ensure the skill_path is within the configured skills_root
            skill_path.relative_to(skills_root_resolved)
        except ValueError:
            results["passed"] = False
            results["errors"].append("Skill path not allowed")
            return results

        if skill_path.is_file() and skill_path.suffix == ".json":
            metadata = json.loads(skill_path.read_text(encoding="utf-8"))
            meta_result = self.validate_metadata(metadata)
            results["checks"].append(
                {
                    "name": "metadata",
                    "status": "pass" if meta_result.passed else "fail",
                    "messages": meta_result.errors,
                }
            )
            results["warnings"].extend(meta_result.warnings)
            results["errors"].extend(meta_result.errors)
            results["passed"] = meta_result.passed
            return results

        if not skill_path.is_dir():
            results["passed"] = False
            results["errors"].append("Skill path not found")
            return results

        metadata_candidate = skill_path / "metadata.json"
        metadata_resolved, err = self._resolve_existing_path_within_dir(
            base_dir=skill_path,
            candidate=metadata_candidate,
            label="metadata.json",
        )
        if err is not None:
            results["passed"] = False
            results["errors"].append(err)
            return results

        try:
            metadata = json.loads(metadata_resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results["passed"] = False
            results["errors"].append(f"Invalid JSON in metadata.json: {exc}")
            return results
        meta_result = self.validate_metadata(metadata)
        results["checks"].append(
            {
                "name": "metadata",
                "status": "pass" if meta_result.passed else "fail",
                "messages": meta_result.errors,
            }
        )
        results["warnings"].extend(meta_result.warnings)
        results["errors"].extend(meta_result.errors)

        structure_result = self.validate_structure(skill_path)
        results["checks"].append(
            {
                "name": "structure",
                "status": "pass" if structure_result.passed else "fail",
                "messages": structure_result.errors,
            }
        )
        results["warnings"].extend(structure_result.warnings)
        results["errors"].extend(structure_result.errors)

        doc_result = self.validate_documentation(skill_path / "SKILL.md")
        results["checks"].append(
            {
                "name": "documentation",
                "status": "pass" if doc_result.passed else "warn",
                "messages": doc_result.errors,
            }
        )
        results["warnings"].extend(doc_result.warnings)
        results["errors"].extend(doc_result.errors)

        # agentskills.io frontmatter validation
        frontmatter_result = self.validate_frontmatter(skill_path / "SKILL.md")
        results["checks"].append(
            {
                "name": "frontmatter",
                "status": "pass" if frontmatter_result.passed else "warn",
                "messages": frontmatter_result.errors,
            }
        )
        # Frontmatter issues are warnings (for backward compatibility with existing skills)
        results["warnings"].extend(frontmatter_result.errors)
        results["warnings"].extend(frontmatter_result.warnings)

        examples_result = self.validate_examples(skill_path / "examples")
        results["checks"].append(
            {
                "name": "examples",
                "status": "pass" if examples_result.passed else "warn",
                "messages": examples_result.errors,
            }
        )
        results["warnings"].extend(examples_result.warnings)
        results["errors"].extend(examples_result.errors)

        rel_path = str(skill_path.relative_to(self.skills_root))
        naming_result = self.validate_naming_conventions(metadata.get("skill_id", ""), rel_path)
        results["checks"].append(
            {
                "name": "naming",
                "status": "pass" if naming_result.passed else "warn",
                "messages": naming_result.errors,
            }
        )
        results["warnings"].extend(naming_result.warnings)
        results["errors"].extend(naming_result.errors)

        results["passed"] = len(results["errors"]) == 0
        return results

    def _validate_skill_id_format(self, skill_id: str) -> bool:
        return bool(self._SKILL_ID_PATTERN.match(skill_id))

    def _validate_semver(self, version: str) -> bool:
        return bool(self._SEMVER_PATTERN.match(version))

    def _validate_weight_capabilities(self, weight: str, capabilities: list[str]) -> bool:
        cap_count = len(capabilities)
        if weight == "lightweight" and cap_count > 5:
            return False
        if weight == "medium" and (cap_count < 3 or cap_count > 10):
            return False
        if weight == "heavyweight" and cap_count < 8:
            return False
        return True

    def _is_safe_path_component(self, component: str) -> bool:
        """Validate that a path component is safe and doesn't allow traversal attacks.

        Rules:
        - Cannot be empty
        - Cannot contain path separators (/ or \\)
        - Cannot contain null bytes
        - Cannot be "." or ".."
        - Cannot contain ".." anywhere
        - Must match _SAFE_PATH_PATTERN exactly
        """
        if not component:
            return False

        if "\0" in component:
            return False

        if "/" in component or "\\" in component:
            return False

        if component in (".", ".."):
            return False

        if ".." in component:
            return False

        return bool(self._SAFE_PATH_PATTERN.fullmatch(component))
