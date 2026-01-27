"""Global pytest configuration and fixtures."""

import os

# Set development environment for all tests to allow wildcard CORS,
# SQLite database fallback, and other development-friendly defaults.
# This must happen before any imports that use settings
os.environ["SKILL_FLEET_ENV"] = "development"
os.environ["SKILL_FLEET_CORS_ORIGINS"] = "*"

# Use in-memory SQLite for tests unless DATABASE_URL is explicitly set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./test_skill_fleet.db"
