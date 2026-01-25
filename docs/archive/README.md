# Documentation Archive

**Archived Date**: 2026-01-25

## Purpose

This directory contains historical documentation that has been superseded by newer content or is no longer actively maintained. Files are kept here for reference purposes.

## What's Archived

### Historical Notes (January 2025 cleanup)
Historical implementation notes and phase completion summaries moved to `historical-notes/`:

- **Phase completion notes**: PHASE1_COMPLETE.md, PHASE2_COMPLETE.md
- **Implementation summaries**: JOB_PERSISTENCE_*, FASTAPI_INTEGRATION, DATABASE_SYNC_SUMMARY
- **Update summaries**: UPDATE_SUMMARY.md, PHASE_0_FOUNDATION.md
- **Bug fix notes**: ASYNC_IO_BLOCKING_FIX, FIX_STREAMING_500, RUN_SOLUTION
- **Feature completion**: INK_UPGRADE_COMPLETE, GEPA_SETUP_COMPLETE, TUI_READY
- **Documentation restructuring**: Old DOCUMENTATION_RESTRUCTURING.md (superseded by current docs)

**Note**: These are preserved for historical context but reference current documentation for accurate information.

### Pre-Restructure Documentation
Documents that describe the architecture before the FastAPI-centric restructure (completed January 2025):

- **Legacy workflow patterns** - Replaced by workflow orchestrators
- **Old import paths** - Updated in [Import Path Guide](../development/IMPORT_PATH_GUIDE.md)
- **Pre-domain layer patterns** - Replaced by DDD patterns documented in [Domain Layer](../architecture/DOMAIN_LAYER.md)

### Historical Planning Documents
Planning documents that have been completed or superseded:

- **Cleanup plans** - Executed and completed
- **Migration notes** - Incorporated into current documentation
- **Legacy API references** - Replaced by current v2 API documentation

## Migration Guide

If you're looking for information that used to be in the archive:

| Archived Topic | Current Location |
|----------------|------------------|
| Import patterns | [Import Path Guide](../development/IMPORT_PATH_GUIDE.md) |
| API v1/v2 confusion | [API Migration Guide](../api/MIGRATION_V1_TO_V2.md) |
| Domain entities | [Domain Layer Architecture](../architecture/DOMAIN_LAYER.md) |
| Service layer | [Service Layer Architecture](../architecture/SERVICE_LAYER.md) |
| Caching strategy | [Caching Layer Architecture](../architecture/CACHING_LAYER.md) |
| Conversational interface | [Conversational Interface](../architecture/CONVERSATIONAL_INTERFACE.md) |

## Why Archive?

Documentation is archived when:

1. **Superseded**: Newer, more accurate documentation exists
2. **Outdated**: Describes deprecated patterns or APIs
3. **Completed**: Planning documents for finished work
4. **Historical**: Preserved for context but not actively maintained

## Using Archived Content

Archived content is provided **as-is** without updates. It may:

- Reference deprecated import paths
- Describe outdated architectural patterns
- Contain broken links to moved content
- Use obsolete API endpoints

**Use archived content for:**
- Understanding historical context
- Researching past decisions
- Recovering information from old links

**For current information, always refer to the main documentation index.**

## See Also

- **[Documentation Index](../index.md)** - Current documentation
- **[Restructuring Status](../architecture/restructuring-status.md)** - Architecture evolution
