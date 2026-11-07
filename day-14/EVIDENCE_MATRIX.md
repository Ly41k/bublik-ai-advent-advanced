# Day 14 — Evidence Matrix, Integrated R3

| ID | Claim | Grounding | Status / limit |
|---|---|---|---|
| I01 | First true single-session integrated sequence for T1/T2/T3 | Owner's `DAY14_MINIMAL_INTEGRATED_T1_T2_T3_R1` terminal output | **PASS** in allowed-expression educational scope |
| I02 | Code Generator routed through Day 13 Gateway | `CALL_1_HTTP=200`, `ORIGIN=OPENAI_API` | **PASS** (owner-observed) |
| I03 | Generated expressions match whitelist | T1 protect / T2 fixed log / T3 trusted endpoint | **PASS**, generator tightly constrained |
| I04 | All 3 Kotlin candidates compile and functionally test | `T1/2/3_GENERATED_KOTLIN_TEST_PASS`, `ALL_THREE...PASS` | **PASS**, owner-observed, mocks only |
| I05 | Separate LLM Security Reviewer after Kotlin tests | `CALL_2_HTTP=200`, source runner stage order | **PASS** for shared grouped review |
| I06 | Three individual severity findings validated | T1 LOW, T2 CLEAN, T3 LOW | **PASS** for model output; no formal security proof |
| I07 | Severity gate applied to actual review | `SEVERITY_GATE=WARN_ALLOW_NO_GIT` | **PASS**, HIGH branch tested only offline |
| I08 | Two audit events match two calls | `AUDIT_2_OF_2=PASS`, allow/allow, 200/200 | **PASS per owner log**, raw JSONL not fetched |
| I09 | One-shot ledger and report present | Owner-reported Mac paths | **Reported**, bytes not uploaded |
| I10 | Real prior initial findings and manual correction | Earlier three separate Gateway calls + Kotlin checks | **PASS as separately observed**, not an integrated repair |
| I11 | Runner offline contract safety | 19/19 tests from original bundled suite in this environment | **PASS**, not live Mac sandbox attestation |
| I12 | Historical R13-R2 offline control | Independent review 235 PASS / 11 SKIP | **ACCEPTED OFFLINE**, synthetic receipts |
| I13 | Historical R14 Gateway adapter | Independent review 24/24 | **ACCEPTED OFFLINE** |
| I14 | Independent static source inspection of integrated runner | This Control staging checks exact parser, call order, stop/no retry, gate | **PASS for disclosed scope** |
| I15 | Arbitrary LLM Kotlin execution | Explicitly forbidden in runner | **NOT_RUN/NOT_AUTHORIZED** |
| I16 | Automatic HIGH/CRITICAL repair → new tests → review | No live execution | **NOT_RUN** |
| I17 | Generic lint, Android Keystore, real HTTP, full logging | Not in course-minimum demo | **NOT_PROVEN** |
| I18 | Git branch/PR/merge | `GIT=HOLD` | **NOT_RUN** |

The integrated run cost was `$0.00008590` according to the owner logs. Historical additional three calls cost `$0.00009850`; combined five-call estimates `$0.00018440`, excluding any other earlier requests. These are Gateway-reported figures, not a billing invoice.
