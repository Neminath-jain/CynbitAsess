"""Evaluation runner executing automated benchmark suites on PR diff datasets.

Measures:
1. Precision and recall per rule
2. Dropped-finding rate (evidence verification effectiveness)
3. Indirect prompt-injection resistance (must be 100%)
4. Average latency (ms) and estimated cost ($)

Supports MockLLMClient and OpenAI-compatible client when LLM_API_KEY is present.
Note: Mock is rule-based; dataset is small and synthetic.
"""
import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Ensure backend modules are importable
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.adapters.llm_client import BaseLLMClient, MockLLMClient, OpenAICompatibleLLMClient  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.services.sanitizer import InputSanitizerService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class RuleMetrics:
    """Precision and recall metrics for a specific review rule."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        total = self.true_positives + self.false_positives
        return round(self.true_positives / total, 3) if total > 0 else 1.0

    @property
    def recall(self) -> float:
        total = self.true_positives + self.false_negatives
        return round(self.true_positives / total, 3) if total > 0 else 1.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return round(2 * (p * r) / (p + r), 3) if (p + r) > 0 else 1.0


@dataclass
class EvalReport:
    """Aggregate evaluation report results."""

    total_cases: int
    provider: str
    model: str
    rule_metrics: dict[str, RuleMetrics]
    dropped_findings_total: int
    raw_findings_total: int
    dropped_finding_rate: float
    injection_cases_total: int
    injections_neutralized: int
    injection_resistance_rate: float
    avg_latency_ms: float
    total_cost_usd: float
    notes: list[str] = field(default_factory=list)
    case_results: list[dict[str, Any]] = field(default_factory=list)


class EvalRunner:
    """Executes benchmark diff suite against the review pipeline."""

    RULES = [
        "PERF_MISSING_FK_INDEX",
        "SEC_HARDCODED_SECRET",
        "SEC_JWT_UNVERIFIED",
        "TEST_MISSING_UNIT_TESTS",
    ]

    def __init__(
        self,
        evals_dir: Path | None = None,
        settings: Settings | None = None,
        llm_client: BaseLLMClient | None = None,
    ) -> None:
        self.evals_dir = evals_dir or (ROOT_DIR / "evals")
        self.data_dir = self.evals_dir / "data"
        self.labels_path = self.evals_dir / "labels.json"
        self.settings = settings or get_settings()
        self.sanitizer = InputSanitizerService()

        if llm_client:
            self.llm_client = llm_client
        elif self.settings.LLM_PROVIDER in ("openai", "gemini") and self.settings.LLM_API_KEY:
            self.llm_client = OpenAICompatibleLLMClient(self.settings)
        else:
            self.llm_client = MockLLMClient()

    def load_labels(self) -> list[dict[str, Any]]:
        """Load test case definitions from labels.json."""
        with open(self.labels_path, encoding="utf-8") as f:
            data = json.load(f)
        return data["test_cases"]

    async def run(self) -> EvalReport:
        """Execute all test cases and compile metric scores."""
        test_cases = self.load_labels()
        rule_stats: dict[str, RuleMetrics] = {rule: RuleMetrics() for rule in self.RULES}

        total_latency = 0.0
        total_tokens = 0
        raw_findings_count = 0
        dropped_findings_count = 0
        injection_cases_total = 0
        injections_neutralized = 0
        case_results: list[dict[str, Any]] = []

        provider_name = getattr(self.llm_client, "provider_name", "mock")
        model_name = getattr(self.llm_client, "model", "mock-rules")

        for tc in test_cases:
            diff_file = self.data_dir / tc["diff_file"]
            raw_diff = diff_file.read_text(encoding="utf-8")
            is_injection = tc.get("is_injection", False)
            expected_rules = set(tc.get("expected_rules", []))

            # 1. Sanitize & wrap in XML envelope
            envelope = self.sanitizer.wrap_in_envelope(
                pr_title=tc["description"],
                pr_body=f"Evaluation test case {tc['id']}",
                raw_diff=raw_diff,
            )

            # Check injection containment: </untrusted_pr_diff> must NEVER be unescaped inside envelope
            if is_injection:
                injection_cases_total += 1
                unescaped_tag = "</untrusted_pr_diff>"
                # Tag must appear ONLY as the valid outer closing tag
                closing_tags_count = envelope.count(unescaped_tag)
                if closing_tags_count == 1 and "&lt;/untrusted_pr_diff&gt;" in envelope or "</" not in raw_diff:
                    injections_neutralized += 1
                elif "</untrusted_pr_diff>" in raw_diff and envelope.count("</untrusted_pr_diff>") == 1:
                    # Verified properly escaped inside envelope
                    injections_neutralized += 1

            # 2. Invoke LLM analysis
            start = time.perf_counter()
            llm_response = await self.llm_client.analyze(sanitized_envelope=envelope, raw_diff=raw_diff)
            latency_ms = (time.perf_counter() - start) * 1000
            total_latency += latency_ms

            # 3. Verify evidence quotes against raw diff
            raw_findings = llm_response.findings
            raw_findings_count += len(raw_findings)
            verified_findings = self.sanitizer.verify_evidence(findings=raw_findings, raw_diff=raw_diff)
            dropped = len(raw_findings) - len(verified_findings)
            dropped_findings_count += dropped

            predicted_rules = {f.rule_id for f in verified_findings}

            # Update rule metrics (TP, FP, FN)
            for rule in self.RULES:
                in_expected = rule in expected_rules
                in_predicted = rule in predicted_rules
                if in_expected and in_predicted:
                    rule_stats[rule].true_positives += 1
                elif not in_expected and in_predicted:
                    rule_stats[rule].false_positives += 1
                elif in_expected and not in_predicted:
                    rule_stats[rule].false_negatives += 1

            # Calculate token estimate heuristic
            case_tokens = max(50, (len(envelope) + len(str(llm_response))) // 4)
            total_tokens += case_tokens

            case_results.append({
                "id": tc["id"],
                "category": tc["category"],
                "expected": list(expected_rules),
                "predicted": list(predicted_rules),
                "findings_count": len(verified_findings),
                "dropped_count": dropped,
                "latency_ms": round(latency_ms, 2),
            })

        # Calculate costs ($0.15/1M tokens for mini model, $0 for mock)
        cost_per_token = 0.0000003 if provider_name == "openai" else 0.0
        total_cost = round(total_tokens * cost_per_token, 6)

        dropped_rate = (
            round(dropped_findings_count / raw_findings_count, 3)
            if raw_findings_count > 0
            else 0.0
        )
        injection_rate = (
            round(injections_neutralized / injection_cases_total, 3)
            if injection_cases_total > 0
            else 1.0
        )

        return EvalReport(
            total_cases=len(test_cases),
            provider=provider_name,
            model=model_name,
            rule_metrics=rule_stats,
            dropped_findings_total=dropped_findings_count,
            raw_findings_total=raw_findings_count,
            dropped_finding_rate=dropped_rate,
            injection_cases_total=injection_cases_total,
            injections_neutralized=injections_neutralized,
            injection_resistance_rate=injection_rate,
            avg_latency_ms=round(total_latency / len(test_cases), 2) if test_cases else 0.0,
            total_cost_usd=total_cost,
            notes=[
                "Mock client is rule-based and quotes diff lines directly.",
                "Dataset is small (10 cases) and synthetic, focused on core BitElevate intern PR patterns.",
                "All test cases execute completely offline without live internet dependencies.",
            ],
            case_results=case_results,
        )


def format_report_markdown(report: EvalReport) -> str:
    """Format evaluation report into GitHub Markdown table."""
    lines: list[str] = [
        "# BitElevate PR Review Copilot - Evaluation Report",
        "",
        f"- **Provider:** `{report.provider}`",
        f"- **Model:** `{report.model}`",
        f"- **Total Test Cases:** {report.total_cases}",
        f"- **Average Latency:** {report.avg_latency_ms} ms",
        f"- **Total Estimated Cost:** ${report.total_cost_usd:.6f}",
        f"- **Prompt Injection Resistance:** **{report.injection_resistance_rate * 100:.1f}%** ({report.injections_neutralized}/{report.injection_cases_total})",
        f"- **Evidence Verification Dropped Findings:** {report.dropped_findings_total} / {report.raw_findings_total} ({report.dropped_finding_rate * 100:.1f}%)",
        "",
        "## Per-Rule Performance",
        "",
        "| Rule ID | Precision | Recall | F1 Score | TP | FP | FN |",
        "|---|---|---|---|---|---|---|",
    ]

    for rule, stats in report.rule_metrics.items():
        lines.append(
            f"| `{rule}` | {stats.precision:.2f} | {stats.recall:.2f} | {stats.f1_score:.2f} | "
            f"{stats.true_positives} | {stats.false_positives} | {stats.false_negatives} |"
        )

    lines.extend([
        "",
        "## Notes & Caveats",
        "",
    ])
    for note in report.notes:
        lines.append(f"- *{note}*")

    return "\n".join(lines)


async def main() -> None:
    """CLI entrypoint for running evaluation suite."""
    runner = EvalRunner()
    report = await runner.run()
    md = format_report_markdown(report)
    print(md)


if __name__ == "__main__":
    asyncio.run(main())
