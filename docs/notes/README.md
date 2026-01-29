# Documentation Notes

**Last Updated**: 2026-01-25

## Purpose

This directory contains implementation notes, summaries, and reference material that doesn't fit into other documentation categories. These are working documents that provide context for development decisions.

## What Belongs Here

### Implementation Notes
- Technical details about specific implementations
- Design rationales and trade-offs
- Performance observations and benchmarks
- Integration notes for external services

### Reference Material
- Quick reference guides
- Code snippets and patterns
- Configuration examples
- Troubleshooting notes

## What Does NOT Belong Here

### Use Main Documentation Instead
- **User-facing guides** → [Getting Started](../getting-started/)
- **Architecture documentation** → [Architecture](../architecture/)
- **API reference** → [API Documentation](../api/)
- **Contributing guidelines** → [Development](../development/)

### Archive Outdated Content
- **Historical notes** → [Archive](../archive/README.md)
- **Superseded information** → Archive or delete

## File Organization

Notes should be organized by topic with descriptive filenames:

```
notes/
├── implementation/     # Implementation details
├── performance/        # Performance notes
├── integration/        # External service integration
└── reference/          # Quick reference material
```

## Creating New Notes

When creating a new note:

1. **Use descriptive filenames** (e.g., `caching-strategy.md` not `notes.md`)
2. **Include date** in the document header
3. **Cross-reference** related documentation
4. **Keep focused** on a single topic
5. **Consider** if it should be in main docs instead

## Template

```markdown
# Note Title

**Date**: YYYY-MM-DD
**Author**: Your Name
**Status**: Draft/Final

## Context
Why this note exists.

## Content
The actual note content.

## References
Links to related documentation or code.
```

## Maintenance

Notes should be:
- **Reviewed periodically** for relevance
- **Updated** when implementations change
- **Archived** when no longer relevant
- **Deleted** when superseded by main docs

## See Also

- **[Documentation Index](../index.md)** - Main documentation
- **[Archive](../archive/README.md)** - Historical content
