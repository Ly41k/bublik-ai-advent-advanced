# Week 1 — deferred maximum

Do not implement this backlog before Course Minimum is accepted.
No item currently has implementation PASS or Bublik Ready status.

| ID | Capability / purpose | Boundary | Dependency | Risk / safety | Size | Priority | Status | Evidence / next check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | Detect conflicting Rules | Report contradictions, not a policy engine | Gate 2 rules | False assurance from text-only checks | Small | High | PLANNED | None; inspect actual precedence |
| M02 | Typed agent routing | Narrow result contracts and dispatch | Native agent proof | Inputs, tool access, shared files | Medium | High | PLANNED | Gate 0 smoke only; verify configured agent |
| M03 | Agent profiles | Explicit responsibilities and permissions | Proven runtime knobs | Instruction vs enforced restrictions | Medium | Medium | PLANNED | None; define one needed profile |
| M04 | FSM / recovery | Explicit task transitions | Real workflow need | Stuck or repeated execution | Medium | Medium | PLANNED | None; choose a concrete failing flow |
| M05 | Executable invariants | Gate selected external actions | Permission design | Fail-open behavior | Medium | High | PLANNED | None; define one enforceable invariant |
| M06 | Skill versions/contracts | Track repeated procedures | One working skill | Stale instructions | Small | Medium | PLANNED | None; Gate 2 first |
| M07 | Hooks | Deterministic pre/post checks | Runtime hook support | Hidden side effects | Medium | Medium | PLANNED | None; demonstrate a necessary hook |
| M08 | Permission boundaries | Tool limits and audit | Runtime capabilities | Secret exposure, broad access | Medium | High | PLANNED | None; separate enforcement from guidance |
| M09 | Observability | Cost, time, trace and refusal reasons | Actual telemetry | Private paths/log contents | Medium | Medium | PLANNED | Baseline logs only; inspect available telemetry |
| M10 | MCP / memory / retrieval / local models | Only a concrete future task | Accepted minimum | Scope and data exposure | Large | Later | DEFERRED | None; reassess after minimum |

Bublik Ready assessment is separate: extension without stable-core changes,
permissions, isolation, graceful failure/recovery, tests and evidence. No
implementation-readiness claim is made by this document.
