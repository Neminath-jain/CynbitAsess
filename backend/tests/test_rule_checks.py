"""Unit tests for deterministic rule checks."""
from app.domain.models import CommentSeverity
from app.services.checks.rule_checks import run_rule_checks


def test_rule_checks_empty_diff() -> None:
    """Verify empty diff returns zero check results."""
    assert run_rule_checks("") == []
    assert run_rule_checks("   \n  ") == []


def test_rule_checks_detects_all_four_rules() -> None:
    """Verify rule checks identify missing FK index, secret, unverified JWT, and missing tests."""
    sample_diff = """diff --git a/app/models.py b/app/models.py
new file mode 100644
--- /dev/null
+++ b/app/models.py
@@ -0,0 +1,12 @@
+from sqlalchemy import Column, Integer, ForeignKey
+
+class Profile:
+    id = Column(Integer, primary_key=True)
+    user_id = Column(Integer, ForeignKey('users.id'))
+    db_password = "super_secret_password_12345"
+
+def decode(raw_tok):
+    import jwt
+    return jwt.decode(raw_tok, verify=False)
+"""
    results = run_rule_checks(sample_diff)
    rule_map = {r.rule_id: r for r in results}

    assert "PERF_MISSING_FK_INDEX" in rule_map
    assert rule_map["PERF_MISSING_FK_INDEX"].severity == CommentSeverity.WARNING
    assert "ForeignKey" in rule_map["PERF_MISSING_FK_INDEX"].evidence_quote

    assert "SEC_HARDCODED_SECRET" in rule_map
    assert rule_map["SEC_HARDCODED_SECRET"].severity == CommentSeverity.CRITICAL
    assert "super_secret_password_12345" in rule_map["SEC_HARDCODED_SECRET"].evidence_quote

    assert "SEC_JWT_UNVERIFIED" in rule_map
    assert rule_map["SEC_JWT_UNVERIFIED"].severity == CommentSeverity.CRITICAL
    assert "verify=False" in rule_map["SEC_JWT_UNVERIFIED"].evidence_quote

    assert "TEST_MISSING_UNIT_TESTS" in rule_map
    assert rule_map["TEST_MISSING_UNIT_TESTS"].severity == CommentSeverity.WARNING

    # Test conversion to Finding schema
    finding = rule_map["PERF_MISSING_FK_INDEX"].to_finding()
    assert finding.rule_id == "PERF_MISSING_FK_INDEX"
