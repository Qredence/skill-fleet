#!/usr/bin/env python3
"""Auto-fix broken markdown links."""

import re
from pathlib import Path

root = Path('.').resolve()

# Fix mappings
FIXES = {
    'CONTRIBUTING.md': 'docs/development/CONTRIBUTING.md',    'LICENSE': 'LICENSE',    'agentskills-compliance.md': 'docs/concepts/agentskills-compliance.md',    'api-reference.md': 'docs/api/endpoints.md',    'cli-reference.md': 'docs/guides/cli.md',    'docs/agentskills-compliance.md': 'docs/concepts/agentskills-compliance.md',    'docs/api-reference.md': 'docs/api/endpoints.md',    'docs/api/': 'docs/api/index.md',    'docs/cli-reference.md': 'docs/guides/cli.md',    'docs/cli/': 'docs/guides/cli.md',    'docs/getting-started/': 'docs/getting-started/index.md',    'docs/overview.md': 'docs/index.md',    'docs/skill-creator-guide.md': 'docs/getting-started/skill-creation-guidelines.md',    'getting-started/index.md': 'docs/getting-started/index.md',    'overview.md': 'docs/index.md',    'skill-creator-guide.md': 'docs/getting-started/skill-creation-guidelines.md',
}

def fix_file(filepath):
    """Fix links in a single file."""
    content = filepath.read_text()
    original = content
    
    pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    
    def replace_link(match):
        text = match.group(1)
        url = match.group(2).strip()
        
        # Check for exact match
        url_clean = url.split('#')[0].split('?')[0]
        if url_clean in FIXES:
            new_url = FIXES[url_clean]
            # Preserve anchor
            if '#' in url:
                new_url += '#' + url.split('#')[1]
            print(f"  Fix: [{text}]({url}) → [{text}]({new_url})")
            return f"[{text}]({new_url})"
        
        return match.group(0)
    
    new_content = pattern.sub(replace_link, content)
    
    if new_content != original:
        filepath.write_text(new_content)
        return True
    return False

# Files to fix
files_to_fix = [
    'AGENTS.md',    'README.md',    'docs/api/api-reference.md',    'docs/architecture/DATABASE_SYNC.md',    'docs/concepts/agentskills-compliance.md',    'docs/getting-started/skill-creation-guidelines.md',    'plans/archive/implementation-phase-final.md',    'plans/archive/overview.md',
]

print("Fixing broken links...")
fixed_count = 0

for filepath in files_to_fix:
    path = root / filepath
    if path.exists():
        print(f"\n{filepath}")
        if fix_file(path):
            fixed_count += 1
    else:
        print(f"⚠️  File not found: {filepath}")

print(f"\n✅ Fixed links in {fixed_count} files")
