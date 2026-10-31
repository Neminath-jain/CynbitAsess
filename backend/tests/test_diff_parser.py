"""Unit tests for Unified Git Diff Parser."""
import pytest
from app.services.diff_parser import DiffParserService


def test_parse_empty_diff() -> None:
    """Verify empty or whitespace diff returns clean empty ParsedDiff."""
    parser = DiffParserService()
    parsed = parser.parse("")
    assert parsed.total_files == 0
    assert parsed.files == []
    assert parsed.is_truncated is False


def test_parse_sample_python_diff(sample_python_diff: str) -> None:
    """Verify parsing single new Python file diff."""
    parser = DiffParserService()
    parsed = parser.parse(sample_python_diff)

    assert parsed.total_files == 1
    assert parsed.is_truncated is False
    assert parsed.total_additions == 14
    assert parsed.total_deletions == 0

    file_diff = parsed.files[0]
    assert file_diff.new_path == "app/calculator.py"
    assert file_diff.is_new_file is True
    assert len(file_diff.hunks) == 1

    hunk = file_diff.hunks[0]
    assert hunk.new_start == 1
    assert hunk.new_lines == 14
    assert len(hunk.lines) == 14

    # Check line numbers 1 to 14
    valid_lines = file_diff.get_valid_new_line_numbers()
    assert valid_lines == set(range(1, 15))

    # Formatted output check
    annotated = file_diff.format_for_analysis()
    assert "--- File: app/calculator.py ---" in annotated
    assert "L   1 + def divide(a, b):" in annotated


def test_parse_multi_file_modifications() -> None:
    """Verify parsing multiple files with additions, deletions, and context lines."""
    multi_diff = """diff --git a/src/auth.py b/src/auth.py
index 111..222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,4 +10,5 @@ def login():
     user = authenticate()
-    log_deprecated()
+    log_secure()
+    audit_event()
     return user
diff --git a/docs/README.md b/docs/README.md
deleted file mode 100644
--- a/docs/README.md
+++ /dev/null
@@ -1,3 +0,0 @@
-# Old Docs
-Deleted line 1
-Deleted line 2
"""
    parser = DiffParserService()
    parsed = parser.parse(multi_diff)

    assert parsed.total_files == 2
    auth_file = parsed.find_file("src/auth.py")
    assert auth_file is not None
    assert auth_file.additions == 2
    assert auth_file.deletions == 1

    readme_file = parsed.find_file("docs/README.md")
    assert readme_file is not None
    assert readme_file.is_deleted_file is True
    assert readme_file.deletions == 3


def test_diff_truncation_limits() -> None:
    """Verify max characters and max files limits trigger truncation safely."""
    # Test max_chars
    parser_small = DiffParserService(max_chars=50)
    parsed = parser_small.parse("diff --git a/a.py b/a.py\n+ long line content that exceeds fifty chars limit definitely")
    assert parsed.is_truncated is True

    # Test max_files
    multi_diff = """diff --git a/f1.py b/f1.py
--- a/f1.py
+++ b/f1.py
@@ -1,1 +1,1 @@
+a
diff --git a/f2.py b/f2.py
--- a/f2.py
+++ b/f2.py
@@ -1,1 +1,1 @@
+b
"""
    parser_max_files = DiffParserService(max_files=1)
    parsed_files = parser_max_files.parse(multi_diff)
    assert parsed_files.is_truncated is True
    assert parsed_files.total_files == 1
