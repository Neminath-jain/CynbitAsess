"""Unit tests for LLM client adapter, repair retry, and rule facts injection."""
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.adapters.llm_client import MockLLMClient, OpenAICompatibleLLMClient, get_llm_client
from app.config import Settings
from app.domain.exceptions import LLMServiceError
from app.services.sanitizer import InputSanitizerService


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


def test_get_llm_client_factory_and_env_config() -> None:
    """Verify factory returns appropriate client and reads base URL / model from settings."""
    mock_settings = Settings(LLM_PROVIDER="mock")
    client_mock = get_llm_client(mock_settings)
    assert isinstance(client_mock, MockLLMClient)

    custom_settings = Settings(
        LLM_PROVIDER="openai",
        LLM_API_KEY="test-key-123",
        LLM_BASE_URL="https://custom.openai.api/v1",
        LLM_MODEL="gpt-4o-custom",
    )
    client_openai = get_llm_client(custom_settings)
    assert isinstance(client_openai, OpenAICompatibleLLMClient)
    assert client_openai.base_url == "https://custom.openai.api/v1"
    assert client_openai.model == "gpt-4o-custom"


@pytest.mark.asyncio
async def test_openai_repair_retry_success() -> None:
    """Verify that when 1st attempt returns malformed JSON, repair retry succeeds on valid JSON."""
    settings = Settings(LLM_PROVIDER="openai", LLM_API_KEY="dummy")
    client = OpenAICompatibleLLMClient(settings)

    # 1st response: malformed JSON
    resp1 = MagicMock()
    resp1.choices = [MagicMock(message=MagicMock(content="Invalid {json..."))]

    # 2nd response (retry): valid JSON
    valid_payload = {
        "summary": "Review complete after repair.",
        "general_feedback": "Looks good.",
        "findings": [],
    }
    resp2 = MagicMock()
    resp2.choices = [MagicMock(message=MagicMock(content=json.dumps(valid_payload)))]

    client.client.chat.completions.create = AsyncMock(side_effect=[resp1, resp2])  # type: ignore[method-assign]

    result = await client.analyze(sanitized_envelope="<diff></diff>", raw_diff="+ print(1)")
    assert result.summary == "Review complete after repair."
    assert client.client.chat.completions.create.call_count == 2  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_openai_repair_retry_fails_safely() -> None:
    """Verify that when repair retry also fails, LLMServiceError is raised safely."""
    settings = Settings(LLM_PROVIDER="openai", LLM_API_KEY="dummy")
    client = OpenAICompatibleLLMClient(settings)

    resp_bad = MagicMock()
    resp_bad.choices = [MagicMock(message=MagicMock(content="still {not json}"))]

    client.client.chat.completions.create = AsyncMock(return_value=resp_bad)  # type: ignore[method-assign]

    with pytest.raises(LLMServiceError):
        await client.analyze(sanitized_envelope="<diff></diff>", raw_diff="+ print(1)")

    assert client.client.chat.completions.create.call_count == 2  # type: ignore[attr-defined]
