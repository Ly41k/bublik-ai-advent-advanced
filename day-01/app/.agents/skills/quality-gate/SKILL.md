---
name: quality-gate
description: Run Bublik's fixed compile/import/Ruff/pytest checks and preserve command results. Use for Bublik validation or after Bublik code changes. Do not install dependencies, repair code, run controlled generations, or use on unrelated projects.
---

# Bublik quality gate

Skill marker: `BUBLIK_QUALITY_GATE_V1_20261020`.

Require `repo_root` (actual absolute project root) and `report_path` (explicit
path under `local-evidence/` or `weeks/week-01/evidence/day-01/`). Validate before
tools. If absent, return BLOCKED / MISSING_REQUIRED_INPUT, missing field names
and performed_actions=0. Do not guess a report path.

1. Read this skill; include its marker in the result.
2. From repo_root, run with the installed venv:

   ```bash
   .venv/bin/python scripts/run_checks.py --output <report_path>
   ```

3. Read the saved report. Capture the real runner exit code and each check's
   exit code. Output text alone does not establish success.
4. Return QualityGateResult with status (PASS/FAIL/BLOCKED), skill_marker,
   report_path, runner_exit_code, checks (array of name/exit_code).
   PASS needs all five checks and runner exit 0. Count tests from observed output.
   Preserve failing results and return FAIL if any check fails.

Do not edit source/tests/Rules/config/locks/runner, install/update packages,
overwrite reports, spawn agents or use external APIs. This procedure validates;
it does not repair. Missing tooling means BLOCKED with the observed error.
