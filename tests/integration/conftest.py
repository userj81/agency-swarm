"""Configuration for integration tests that require API keys."""

import os

import pytest

# Importing agency_swarm triggers .env loading via python-dotenv
import agency_swarm  # noqa: F401

# Skip integration tests if API key is not available
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY not found in environment", allow_module_level=True)
