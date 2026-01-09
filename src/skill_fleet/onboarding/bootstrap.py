"""User onboarding and skill bootstrapping."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ..taxonomy.manager import TaxonomyManager
from ..workflow.skill_creator import TaxonomySkillCreator


class SkillBootstrapper:
    """Bootstrap user-specific skill sets based on onboarding."""

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        skill_creator: TaxonomySkillCreator,
        profiles_path: Path,
    ):
        self.taxonomy = taxonomy_manager
        self.creator = skill_creator
        self.profiles = self._load_profiles(profiles_path)

    def _load_profiles(self, profiles_path: Path) -> dict:
        """Load bootstrap profiles configuration."""
        with open(profiles_path) as f:
            return json.load(f)

    async def onboard_user(self, user_id: str, responses: dict) -> dict:
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
        print(
            f"📋 Skill plan: {len(skill_plan['required'])} required, "
            f"{len(skill_plan['onDemand'])} on-demand"
        )

        # Generate required skills
        mounted_skills = []
        for skill_path in skill_plan["required"]:
            # Check if skill exists
            if not self.taxonomy.skill_exists(skill_path):
                print(f"🔨 Generating skill: {skill_path}")
                result = await self._generate_skill_for_path(skill_path, user_id)
                if result.get("status") == "approved":
                    skill_id = result["skill_id"]
                    mounted_skills.append(skill_id)
                    # track_usage is already called in TaxonomySkillCreator.forward for creation
            else:
                # Load existing skill
                skill_id = self._path_to_skill_id(skill_path)
                mounted_skills.append(skill_id)
                print(f"✓ Loaded existing skill: {skill_id}")

                # Track usage of existing skill during onboarding
                self.taxonomy.track_usage(
                    skill_id=skill_id,
                    user_id=user_id,
                    success=True,
                    metadata={"event_type": "onboarding_mount"},
                )

        # Register on-demand skills
        self.register_on_demand_skills(user_id, skill_plan["onDemand"])

        # Create user profile
        user_profile = {
            "user_id": user_id,
            "profile": profile,
            "mounted_skills": mounted_skills,
            "on_demand_skills": skill_plan["onDemand"],
            "created_at": datetime.now(UTC).isoformat(),
            "ready_for_tasks": True,
        }

        # Persist user profile
        self._save_user_profile(user_profile)

        print(f"🎉 Onboarding complete! {len(mounted_skills)} skills mounted.")

        return user_profile

    def analyze_responses(self, responses: dict) -> dict:
        """Map user responses to skill requirements."""
        profile = {
            "primaryRole": responses.get("role", "general_purpose"),
            "techStack": responses.get("tech_stack", []),
            "commonTasks": responses.get("common_tasks", []),
            "experience_level": responses.get("experience_level", "mid-level"),
            "preferences": responses.get("preferences", {}),
        }
        return profile

    def generate_skill_plan(self, profile: dict) -> dict:
        """Generate skill plan based on user profile."""
        role = profile["primaryRole"]

        # Get base plan for role
        base_plan = self.profiles["bootstrap_profiles"].get(
            role, self.profiles["bootstrap_profiles"]["general_purpose"]
        )

        required = base_plan["required"].copy()
        on_demand = base_plan["on_demand"].copy()

        # Augment based on tech stack
        for tech in profile["techStack"]:
            tech_skills = self.profiles["tech_stack_mapping"].get(tech, [])
            required.extend(tech_skills)

        # Augment based on common tasks
        for task in profile["commonTasks"]:
            task_skills = self.profiles["task_mapping"].get(task, [])
            required.extend(task_skills)

        # Remove duplicates
        required = list(set(required))
        on_demand = list(set(on_demand))

        return {"required": required, "onDemand": on_demand}

    async def _generate_skill_for_path(self, skill_path: str, user_id: str) -> dict:
        """Generate a skill for a specific taxonomy path."""
        # Infer task description from path
        task_description = self._path_to_task_description(skill_path)

        result = self.creator.forward(
            task_description=task_description,
            user_context={"user_id": user_id},
            auto_approve=True,  # Auto-approve bootstrap skills
        )

        return result

    def register_on_demand_skills(self, user_id: str, on_demand_paths: list[str]):
        """Register skills for on-demand generation."""
        # TODO: Implement on-demand skill registry
        pass

    def _path_to_skill_id(self, path: str) -> str:
        """Convert taxonomy path to skill_id."""
        return path.replace("/", ".")

    def _path_to_task_description(self, path: str) -> str:
        """Convert taxonomy path to task description for generation."""
        parts = path.split("/")
        last_part = parts[-1].replace("_", " ")
        category = parts[0].replace("_", " ")

        return f"Create a {last_part} skill in the {category} category"

    def _save_user_profile(self, profile: dict):
        """Persist user profile to storage."""
        # TODO: Implement user profile storage
        pass
