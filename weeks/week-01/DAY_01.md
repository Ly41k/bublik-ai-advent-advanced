# Day 1 — Rules: Gate 1 delivery

**Gate 1 implementation and Linux validation: PASS.**
**Overall Day 1: PARTIAL — Gates 2–6 have not been executed.**

## Delivered baseline

- Separate local repository linked to the existing `Ly41k/bublik-ai-advent-advanced` origin.
- FastAPI factory with `GET /health`, `POST /tasks`, `GET /tasks/{task_id}`.
- Immutable domain Task, typed errors, application service, repository protocol,
  isolated in-memory storage, explicit Pydantic DTOs and DI.
- 38 tests covering domain validation, service behavior, repository semantics,
  API contracts/errors, application isolation, and import boundaries.
- Ruff lint/format and pytest configuration, Python 3.13.3 target,
  universal uv lock and hashed pip-compatible dependency export.
- Five real code examples referenced by path and symbol in
  `docs/BASELINE_CODE_EXAMPLES.md`.
- Repeatable check runner recording command/exit codes, package versions,
  source/config hashes, and sanitized stdout/stderr.
- Self-contained Git bundle handoff; no remote commit has been published.

## Actual verification

Execution environment: **Linux x86_64, isolated CPython 3.13.3, project .venv**.
The pre-existing Linux host Python 3.12.14 is not the interpreter used here.

| Check | Result | Evidence |
| --- | --- | --- |
| Compile src/tests/scripts | PASS, exit 0 | `evidence/day-01/baseline-checks.txt` |
| Import and instantiate app | PASS, exit 0 | Same log |
| Ruff lint | PASS, exit 0 | Same log |
| Ruff format check | PASS, exit 0 | Same log |
| pytest | PASS, 38 tests, exit 0 | Same log |
| Package dependency consistency | PASS; `pip check` found no broken requirements | Direct Linux setup check; reproduced in delivery verification |
| Manual dependency-direction review | PASS within baseline scope | Review below; AST tests enforce listed imports |
| Mac Python/Codex installation | User-confirmed: 3.13.3 / CLI 0.163.0 / ChatGPT login | `evidence/day-01/environment.md` |
| Mac baseline test execution | NOT RUN | Run handoff commands and review resulting log |

Direct package pins in the current lock include FastAPI 0.149.0,
Pydantic 2.14.1, Uvicorn 0.54.0, httpx2 2.15.1, pytest 9.1.1, Ruff 0.17.1,
Hatchling 1.27.0 and editables 0.5. Both lockfiles must remain unchanged.

Manual review: domain imports only stdlib plus its own typed errors;
application consumes domain/Protocol without framework/storage imports;
API delegates persistence to the service and maps only expected lookup errors;
the factory owns concrete wiring and per-app state. No mutable global task
dictionary, hardcoded credential, broad exception swallowing, external API
client, or previous-course runtime dependency exists in the source.
AST checks cover ordinary static imports, not arbitrary dynamic import behavior.

## Baseline identity and transfer

The tag `baseline/day01-foundation` identifies BASE_SHA. The following
evidence-only commit stores `evidence/day-01/baseline-sha.txt` and
`baseline-core.sha256`, avoiding a self-referential commit hash.
Both controlled runs must start from that tagged source baseline plus their
approved Rules overlays, with common skill/config/agent versions frozen in Gate 2.

The exported bundle includes local history and the baseline tag. Delivery
checks verify bundle restoration, core checksums and source equality. See
`docs/MAC_HANDOFF.md`; perform Mac tests before any controlled generation.

## Strict acceptance state

| Requirement | Current state |
| --- | --- |
| R01 Independent executable project | PASS on Linux |
| R02 Rules v1/v2 | NOT RUN; Gate 2 onward |
| R03 Stack/architecture/tree/naming/patterns in final Rules | PARTIAL: documented in README, AGENTS.md not created yet |
| R04 Actual global/local/module instruction loading | NOT RUN in CLI 0.163.0 |
| R05 Real code examples | Prepared: five path/symbol references; insertion in Rules pending |
| R06 Antipatterns in Rules | NOT RUN |
| R07 Typical file template in Rules | NOT RUN |
| R08 Project skill and actual usage | NOT RUN |
| R09 Configured native subagent | PARTIAL: Work native smoke passed; CLI/TOML proof pending |
| R10 Immutable control prompt | Task approved; final text/hash not yet frozen |
| R11 Two independent generations | NOT RUN |
| R12 Quality Gate for both generations | NOT RUN; baseline-only checks passed |
| R13 Rules v2 grounded in v1 findings | NOT RUN |
| R14 Comparison and final evidence | NOT RUN |
| R15 Reproducibility | Linux environment/locks/handoff prepared; Mac reproduction pending |

## Remaining work / blockers

No blocker remains for the delivered Linux baseline. Gate 2 still requires
Mac execution and actual project instruction/skill/subagent integration in
CLI 0.163.0. It also freezes the final prompt, acceptance tests and generation
settings. Absence of this proof prevents claiming Course Minimum PASS.

No controlled generation, project AGENTS.md/skill/agent creation, global
Codex configuration change, push, PR publication or merge was performed in Gate 1.
The maximum backlog remains deferred in `MAXIMUM.md`.
