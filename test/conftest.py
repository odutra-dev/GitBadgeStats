import os

# Ensure GITHUB_TOKEN is present in test environment if not configured
if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"
