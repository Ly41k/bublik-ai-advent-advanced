# Day 14 — Actual Results (Owner Mac + Offline Control)

## Latest integrated live run: `DAY14_MINIMAL_INTEGRATED_T1_T2_T3_R1`

Owner-supplied terminal output (not independently fetched private Mac logs):

| Stage | Evidence | Verdict |
|---|---|---|
| Gateway health | `GATEWAY_HEALTH=PASS` | PASS |
| LLM Generator | `CALL_1_HTTP=200`, `CALL_1_ORIGIN=OPENAI_API` | PASS |
| Generator output | T1 `tokenStore.protect(token)`; T2 `logger.log("request.accepted")`; T3 `client.get(SECURE_ENDPOINT)` | Exact whitelist PASS |
| Kotlin/JVM T1 | `T1_GENERATED_KOTLIN_TEST_PASS` | PASS |
| Kotlin/JVM T2 | `T2_GENERATED_KOTLIN_TEST_PASS` | PASS |
| Kotlin/JVM T3 | `T3_GENERATED_KOTLIN_TEST_PASS` | PASS |
| Compilation/tests aggregate | `ALL_THREE_GENERATED_KOTLIN_CHECKS_PASS`; `KOTLIN_TRUSTED_WHITELIST_EXECUTION=PASS` | PASS |
| LLM Security Reviewer | `CALL_2_HTTP=200`, `CALL_2_ORIGIN=OPENAI_API` | PASS |
| Audit reconciliation | `AUDIT_2_OF_2=PASS`, `AUDIT_RECORDS=2`, allow/allow, 200/200 | PASS (owner log) |
| Severity | T1 LOW, T2 CLEAN, T3 LOW | `WARN_ALLOW_NO_GIT` |
| Overall | `RESULT=INTEGRATED_DEMO_PASS` | PASS, educational subset |
| Gateway shutdown | `GATEWAY_STOPPED=true` | PASS (owner log) |
| Git | `GIT=HOLD` | No publication |

### Reviewer judgments, in model's own terms

```text
T1: LOW | Token protection is delegated; its security properties are not shown.
T2: CLEAN | Logs a fixed message and checks only that the email is nonblank.
T3: LOW | Uses the trusted HTTPS endpoint; TLS validation is not established here.
```

The reviewer evaluates the actual source **after** Kotlin compile/tests, but only the three pre-authorized expressions can reach that stage. T2's simple accepted-event logging is not a demonstration of capturing **all** HTTP requests; T3 uses a `ProbeApiClient` and an `.invalid` HTTPS URL rather than real network traffic.

### Measured cost from this integration (Gateway estimates)

- Generator `0.00003640 USD`.
- Security Reviewer `0.00004950 USD`.
- Integrated run total **`0.00008590 USD`**.
- Owner consent ceiling `$0.01` for this run. The script does not establish an account-level API billing hard cap. No automatic retries were reported.

The run directory reported by the owner:

```text
~/BUBLIK-D14-DAY13-LAB/d14-ft-minimal-integrated-r1/
  one-shot-ledger.jsonl
  gateway-audit.jsonl
  result.json
```

These filenames/paths are recorded for provenance only. **Their bytes were not provided**, so no independent hash validation of Mac evidence is claimed.

## Prior real fast-track evidence (separate from integrated run)

| Run | Evidence | Gateway cost USD |
|---|---|---:|
| Initial Reviewer, manually supplied unsafe code | T1 HIGH plaintext token; T2 MEDIUM PII; T3 MEDIUM HTTP | 0.00003440 |
| T1 Generator | Generated `tokenStore.protect(token)`; later compiled/tested in manually supplied wrapper | 0.00001930 |
| Final Reviewer, manually supplied fixed snippets | T1 LOW; T2 CLEAN; T3 LOW | 0.00004480 |
| **Earlier 3 calls subtotal** | Separate sessions, not part of integrated two-call run | **0.00009850** |
| **All 5 owner-reported real LLM calls** | Earlier 3 + integrated 2 | **0.00018440** |

Additional owner-observed local Kotlin checks: trusted compiler smoke PASS; T1 SAFE/UNSAFE PASS; T2 SAFE/UNSAFE PASS; T3 SAFE/UNSAFE PASS; T1 generated method compile/functional/protect-only PASS. Jansi `noexec` warning did not prevent compilation/tests. Past independent offline baseline: R13-R2 `235 PASS/11 SKIP`, R14 `24/24 PASS`; not substitutes for live runs.

## Restrictions

1. **Generator scope:** exact trusted whitelist of three simple Kotlin statements. Unrecognized model code is rejected; not general-purpose generation/execution.
2. **Tests:** Kotlin/JVM mocked components only, no Android Keystore, no real HTTP, no actual PII logging backend or broad request logging.
3. **Security Reviewer:** model's advisory judgment. LOW findings are deliberately retained and allowed with warning.
4. **HIGH repair:** earlier manual HIGH → corrected → re-review shown, but integrated automatic bounded repair on HIGH/CRITICAL has **NOT_RUN**.
5. **Lint and Git:** no independent Kotlin lint process, no commit, no PR or merge.
6. **Source audit:** model usage, ledger and Gateway audit reported by owner; no byte-level independent Mac readback in this package.

**Final control scope:** `DAY14_COURSE_MINIMUM_INTEGRATED_DEMO_PASS_WITH_LIMITATIONS`. Broader task completion and instructor acceptance not independently established.
