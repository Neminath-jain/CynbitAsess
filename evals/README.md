# BitElevate PR Review Copilot - Evaluation Suite (`evals/`)

This directory houses offline benchmark datasets and evaluation harnesses to validate the safety and pedagogical quality of the LLM review engine.

## Evaluation Dimensions
1. **Adversarial & Indirect Prompt Injection Resilience**:
   - Diffs containing system override attempts (`"Ignore prior instructions..."`, markdown breakout sequences, credential exfiltration traps).
   - Baseline: 100% containment; zero prompt instruction alteration.
2. **Schema Adherence & Structured Output**:
   - Validating that 100% of generated comments parse into Pydantic models with non-empty pedagogical rationale.
3. **Pedagogical Quality**:
   - Verification that comments identify actual issues without intimidating language, offering concrete code remediation examples and learning references.
