"""Pytest shared fixtures and test configuration."""
from typing import Generator
import pytest
import os


@pytest.fixture(autouse=True)
def setup_test_env() -> Generator[None, None, None]:
    """Ensure safe testing environment variables."""
    old_env = os.environ.copy()
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["LLM_API_KEY"] = "test-mock-key"
    os.environ["GITHUB_TOKEN"] = "test-github-token"
    os.environ["GITHUB_WEBHOOK_SECRET"] = "test-webhook-secret"
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def sample_python_diff() -> str:
    """Provide a standard git diff representing an intern PR in Python."""
    return """diff --git a/app/calculator.py b/app/calculator.py
new file mode 100644
index 0000000..8a91234
--- /dev/null
+++ b/app/calculator.py
@@ -0,0 +1,14 @@
+def divide(a, b):
+    # Warning: Missing zero division check
+    return a / b
+
+def execute_user_query(query_str):
+    import sqlite3
+    conn = sqlite3.connect("test.db")
+    cursor = conn.cursor()
+    # SQL injection vulnerability
+    cursor.execute("SELECT * FROM users WHERE name = '" + query_str + "'")
+    return cursor.fetchall()
+
+def unused_function():
+    pass
"""
