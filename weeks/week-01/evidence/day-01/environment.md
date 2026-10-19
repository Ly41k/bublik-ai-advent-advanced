# Gate 0 environment record

## Mac — user-reported command results, 2026-10-19

| Command | Reported result |
| --- | --- |
| `codex --version` | `codex-cli 0.163.0` |
| `codex login status` | `Logged in using ChatGPT` |
| `python3 --version` | `Python 3.13.3` |

These commands were executed by the user on the Mac. The Work agent did not
execute them remotely. No authentication data or private configuration was copied.
Keep Codex **0.163.0** unchanged across the experiment. Installation is complete.
Actual discovery of project rules, skills, and agent TOMLs remains a Gate 2 check.

## Linux Work — directly observed

- OS / architecture: Linux x86_64.
- Initially available Python: **3.12.14** (host runtime; not the baseline test interpreter).
- Isolated task interpreter installed for Gate 1: **CPython 3.13.3**, Linux x86_64.
- Codex CLI: not on PATH; no Linux CLI session was launched.
- Git: 2.51.1. Dependency resolver used for authoring: uv 0.12.23.
- Baseline checks use the project's `.venv`, created with isolated Python 3.13.3.
- Exact dependency versions and command results are recorded in `baseline-checks.txt`.
- No Mac test result is inferred from Linux success, even with matching Python versions.

## Repository access — observed in Gate 0

- Existing repository: `Ly41k/bublik-ai-advent-advanced`, public, not archived.
- Connector metadata reports pull/push/admin permissions.
- Branch-list response: `[]`.
- Commit-list response: HTTP 409, `Git Repository is empty.`
- A subsequent read-only `git ls-remote` completed successfully with no refs.
- Gate 1 initializes a local working copy and attaches the existing origin;
  it does not create another GitHub repository or publish a commit.

## Work native subagent smoke checks — observed in Gate 0

Two native `collaboration.spawn_agent` calls used `fork_turns="none"`.
They do not establish project TOML discovery or OS-level isolation.

Missing-input result (no tool calls observed before the final response):

```json
{"status":"BLOCKED","result_type":"ArchitectureReport","error_code":"MISSING_REQUIRED_INPUT","missing_fields":["task_spec"],"performed_actions":0}
```

With all required inputs, a second native agent returned `SUCCESS`,
`result_type=ArchitectureReport`, after one real shell check. It observed the
then-current Linux Python 3.12.14, absent Codex CLI, absent root AGENTS.md,
and absent project `.agents/skills`. Those file checks describe Gate 0 only.

Built-in `openai-docs` instructions were genuinely read through the skill tool.
This does not prove activation of a future project `quality-gate` skill.

## Gate boundaries

Gate 1 builds the service. Gate 2 creates and verifies global/local instructions,
the project skill and native subagent configuration in Codex CLI 0.163.0.
Controlled generations, model/effort selection, acceptance-test freeze, and
prompt hashing have not occurred. No model usage totals or costs are invented.
