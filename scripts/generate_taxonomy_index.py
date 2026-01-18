"""Generate the taxonomy_index.json from the taxonomy mapping report.

This script parses reports/taxonomy-map.md and converts it into the
skills/taxonomy_index.json format using the new TaxonomyIndex models.
"""

import logging
from pathlib import Path

from skill_fleet.taxonomy.models import CategoryNode, SkillEntry, TaxonomyIndex


def parse_markdown_table(md_content):
    """Simple parser for the specific markdown table format in the report."""
    rows = []
    lines = md_content.splitlines()
    in_table = False

    for line in lines:
        if line.strip().startswith("| Skill ID"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.strip().startswith("|---"):
            continue
        if line.strip().startswith("| :---"):
            continue
        if not line.strip().startswith("|"):
            continue

        # Parse logic
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 3:
            skill_id_raw = parts[0].replace("**", "").replace("`", "")
            current_path = parts[1].replace("`", "")
            canonical_path = parts[2].replace("`", "").replace("skills/", "")  # Rel to skills root
            facets_raw = parts[3] if len(parts) > 3 else ""

            # Simple handling for the drafts case with "..."
            if "..." in current_path:
                print(f"Skipping incomplete draft path: {current_path}")
                continue

            # Handle N/A
            if "(N/A" in current_path:
                print(f"Skipping N/A path for {skill_id_raw}")
                continue

            # Parse facets
            facets = {}
            if facets_raw:
                for f in facets_raw.split(","):
                    if ":" in f:
                        k, v = f.split(":", 1)
                        facets[k.strip()] = v.strip()

            # Canonical path usually implies the structure
            # e.g. python/async -> python.async

            # Strip "skills/" prefix from current_path if present for consistency
            if current_path.startswith("skills/"):
                current_path = current_path[7:]

            rows.append(
                {
                    "skill_id": skill_id_raw,
                    "current_path": current_path,
                    "canonical_path": canonical_path,
                    "facets": facets,
                }
            )

    return rows


def build_taxonomy_tree(skills_data):
    """Build the logical tree from canonical paths."""
    tree = {}

    for item in skills_data:
        path_parts = item["canonical_path"].split("/")
        # We assume the canonical path implies the taxonomy structure
        # e.g., "python/async" -> python -> async

        current_level = tree
        for _, part in enumerate(path_parts[:-1]):  # Last part is the skill itself, usually?
            # Actually, the canonical path IS the skill location.
            # So if canonical is "python/async", does "async" become a leaf category
            # containing the skill, or is "async" the skill ID?

            # In the new model:
            # skills = flat list.
            # taxonomy_tree = logical hierarchy of CATEGORIES.

            # If canonical path is "python/async", is "python" the category?
            # Yes.

            if part not in current_level:
                current_level[part] = {"description": f"{part.title()} Category", "children": {}}

            # Move down
            current_level = current_level[part]["children"]

    # Function to recursively convert dicts to CategoryNode models
    def convert_to_nodes(d):
        nodes = {}
        for k, v in d.items():
            nodes[k] = CategoryNode(
                description=v["description"], children=convert_to_nodes(v["children"])
            )
        return nodes

    return convert_to_nodes(tree)


def main():
    """Main execution entry point."""
    root = Path(__file__).parents[1]
    report_path = root / "reports/taxonomy-map.md"
    index_path = root / "skills/taxonomy_index.json"

    if not report_path.exists():
        logging.error("Error: %s not found", report_path)
        return

    print("Parsing mapping...")
    content = report_path.read_text(encoding="utf-8")
    mapping_data = parse_markdown_table(content)

    print(f"Found {len(mapping_data)} skills")

    # Build Skills Inventory
    skills_inventory = {}
    for item in mapping_data:
        # Determine taxonomy location (dot notation) from canonical path
        # e.g. python/async -> python.async
        # NOTE: If canonical path is "python/async", "async" is the folder name.
        # The logic taxonomy location might be just "python".
        parts = item["canonical_path"].split("/")
        location = ".".join(parts[:-1]) if len(parts) > 1 else "root"

        entry = SkillEntry(
            canonical_path=item["canonical_path"],
            taxonomy_location=location,
            aliases=[item["current_path"]],  # The legacy path is the alias
            facets=item["facets"],
            status="active",
        )
        skills_inventory[item["skill_id"]] = entry

    # Build Logical Tree
    taxonomy_tree = build_taxonomy_tree(mapping_data)

    # Construct Full Index
    index = TaxonomyIndex(version="1.0.0", taxonomy_tree=taxonomy_tree, skills=skills_inventory)

    print("Writing index...")
    index_path.write_text(index.model_dump_json(indent=2), encoding="utf-8")
    print(f"Success! Written to {index_path}")


if __name__ == "__main__":
    main()
