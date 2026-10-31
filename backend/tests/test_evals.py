import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from evals.runner import EvalRunner, format_report_markdown


@pytest.mark.asyncio
async def test_eval_runner_benchmark_execution() -> None:
    """Verify evaluation runner processes all synthetic test cases and measures 100% injection defense."""
    runner = EvalRunner()
    report = await runner.run()

    # 10 test cases: 4 planted defects, 3 clean PRs, 3 prompt-injection attacks
    assert report.total_cases == 10
    assert report.provider == "mock"
    assert report.model == "mock-rules"

    # Injection containment must be 100%
    assert report.injection_cases_total == 3
    assert report.injections_neutralized == 3
    assert report.injection_resistance_rate == 1.0

    # Rule metrics: precision and recall
    for rule in ("PERF_MISSING_FK_INDEX", "SEC_HARDCODED_SECRET", "SEC_JWT_UNVERIFIED", "TEST_MISSING_UNIT_TESTS"):
        stats = report.rule_metrics[rule]
        assert stats.true_positives == 1
        assert stats.false_positives == 0
        assert stats.false_negatives == 0
        assert stats.precision == 1.0
        assert stats.recall == 1.0
        assert stats.f1_score == 1.0

    # Markdown report generation
    md = format_report_markdown(report)
    assert "# BitElevate PR Review Copilot - Evaluation Report" in md
    assert "**Prompt Injection Resistance:** **100.0%**" in md
    assert "| `PERF_MISSING_FK_INDEX` | 1.00 | 1.00 |" in md
    assert "| `SEC_HARDCODED_SECRET` | 1.00 | 1.00 |" in md
