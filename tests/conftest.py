"""Global pytest configuration and fixtures."""

import os

# Set development environment for all tests to allow wildcard CORS
# and other development-friendly defaults.
# This must happen before any imports that use settings
os.environ["SKILL_FLEET_ENV"] = "development"
os.environ["SKILL_FLEET_CORS_ORIGINS"] = "*"
