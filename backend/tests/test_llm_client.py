"""Unit tests for LLM client adapter and mock findings generation."""
import pytest
from app.adapters.llm_client import MockLLMClient, OpenAICompatibleLLMClient, get_llm_client
from app.config import Settings
from app.services.sanitizer import InputSanitizerService


@pytest.mark.asyncio
async def None_test_placeholder() -> None:
    pass


@pytest.mark.asyncio
async def test_mock_llm_client_covers_all_four_patterns_and_evidence_check() -> None:
    """Verify MockLLMClient detects missing FK index, hardcoded secret, unverified JWT, and missing tests,

    and that every finding's evidence quote appears in the diff and passes verify_evidence.
    """
    diff_with_all_patterns = """diff --git a/app/models.py b/app/models.py
new file mode 100644
--- /dev/null
+++ b/app/models.py
@@ -0,0 +1,18 @@
+from sqlalchemy import Column, Integer, ForeignKey
+
+class Order:
+    id = Column(Integer, primary_key=True)
+    user_id = Column(Integer, ForeignKey("users.id"))
+    api_key = "sk_live_1234567890abcdef"
+
+def decode_token(tok):
+    import jwt
+    return jwt.decode(tok, verify=False)
+"""

    client = MockLLMClient()
    response = await client.analyze(sanitized_envelope="<untrusted_pr_diff>...</untrusted_pr_diff>", raw_diff=diff_with_all_patterns)

    rule_ids = {f.rule_id for f in response.findings}
    assert "PERF_MISSING_FK_INDEX" in rule_ids
    assert "SEC_HARDCODED_SECRET" in rule_ids
    assert "SEC_JWT_UNVERIFIED" in rule_ids
    assert "TEST_MISSING_UNIT_TESTS" in rule_ids

    # Verify evidence check passes for all findings!
    sanitizer = InputSanitizerService()
    verified = sanitizer.verify_evidence(response.findings, diff_with_all_patterns)
    assert len(verified) == len(response.findings)


def test_get_llm_client_factory() -> None:
    """Verify factory returns appropriate client based on LLM_PROVIDER."""
    mock_settings = Settings(LLM_PROVIDER="mock")
    client_mock = get_llm_client(mock_settings)
    assert isinstance(client_mock, MockLLMClient)

    openai_settings = Settings(LLM_PROVIDER="openai", LLM_API_KEY="test-key")
    client_openai = get_llm_client(openai_settings)
    assert isinstance(client_openai, OpenAICompatibleLLMClient)
