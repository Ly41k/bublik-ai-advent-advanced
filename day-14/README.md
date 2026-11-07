# Day 14 — Kotlin Generation + Security Review (Integrated Course-Minimum Demo)

**Status:** `INTEGRATED_EDUCATIONAL_DEMO_PASS_WITH_LIMITATIONS` based on the **owner-provided Mac terminal output**. **Git:** `HOLD` (no branch, commit or PR authorized). A general arbitrary-code agent, real Android security, and automatic HIGH repair loop are **not demonstrated**.

## What was achieved

One real integrated demonstration on the owner's Mac ran the following order for the three tasks:

```text
T1 / T2 / T3 task descriptions
  -> LLM Generator via real Day 13 Gateway (HTTP 200)
  -> exact-expression whitelist for three Kotlin statements
  -> Kotlin/JVM compilation and functional tests in network-disabled Docker
  -> separate LLM Security Reviewer via same Day 13 Gateway (HTTP 200)
  -> parsed per-task severity + WARN_ALLOW_NO_GIT decision
```

The Generator returned exactly:

```kotlin
T1=tokenStore.protect(token)
T2=logger.log("request.accepted")
T3=client.get(SECURE_ENDPOINT)
```

The fixed trusted `SECURE_ENDPOINT` is `https://api.example.invalid/profile`. **No HTTP request was sent**: `ProbeApiClient` intercepted the call. The storage and logging implementations were test doubles. The three generated statements were not used as an unconstrained Kotlin program; the runner only compiles them if they precisely match its trusted whitelist. The surrounding Kotlin classes and test scaffolding are prewritten.

## Runner and tests

- [`BUBLIK_D14_MINIMAL_INTEGRATED_R1.py`](BUBLIK_D14_MINIMAL_INTEGRATED_R1.py) — original R1 integrated runner, unchanged (SHA256 `4c048d20d0e24f6df7e6a67ad77b5eb0a386b8bb4819b57f80c07732f5e6c3e6`)
- [`test_integrated_offline.py`](test_integrated_offline.py) — original R1 offline contract suite, unchanged (SHA256 `4503f437c83c1a5148b65e180e4b8f4f21c3cba64b536a3db74c99e64c3cabc8`)
- Offline suite: **19/19 PASS** in this documentation environment. Owner Mac: actual integrated run **PASS** as shown in provided terminal output.
- The script was designed for a specific owner's Mac (`~/BUBLIK-D14-DAY13-LAB`, pinned Colima Docker image, `~/Downloads/BUBLIK_D13_FINAL_PUBLIC_SOURCE.zip`). It is **not** a hosted service or turnkey partner endpoint.
- The original one-shot ledger and Gateway audit are private on the owner Mac. **Do not re-run the same grant or erase/reuse the directory.**

## Security boundaries

- Docker: pinned `gradle:8.14.6-jdk17` image; `--network none`, read-only root, all capabilities removed, `no-new-privileges`, CPU/RAM/PID bounds, `noexec` tmpfs and no host mounts. That proves execution of **whitelisted trusted content**, not sandbox safety for arbitrary generated programs.
- Day 13 Gateway: two real model calls (`origin=OPENAI_API`), `audit=allow,allow`, status 200, measured Gateway usage/cost; the audit `allow` describes Gateway policy, **not code security**.
- Severity: T1 LOW (token protection delegation unverified), T2 CLEAN (no PII in shown log message), T3 LOW (HTTPS configured but TLS validation unverified). Overall `WARN_ALLOW_NO_GIT`.
- Initial earlier review found HIGH/MEDIUM/MEDIUM; a manually steered prior repair demonstration reduced to LOW/CLEAN/LOW. **Automatic HIGH/CRITICAL repair and a second review after such an integrated HIGH remain NOT_RUN.**
- A dedicated independent lint tool is not part of the minimal integrated demonstration; exact-expression filtering, Kotlin compile and runtime assertions are present.
- No Android Keystore implementation, complete HTTP request logging, real network call, or certificate-validation test is shown.

## Evidence & publication

See `RESULTS.md`, `EVIDENCE_MATRIX.md`, `COURSE_CHECKLIST.md` and the separate `CONTROL_DECISION_RU.md`. All **live** evidence comes from owner-supplied terminal output; raw private audit/ledger JSONL and report JSON are not included or byte-verified here. Prior offline Control baselines are distinct from this live demonstration.

**Dispositions:** `INTEGRATED_DEMO_PASS`, `DAY14_COURSE_MINIMUM_DEMO_EVIDENCED_WITH_LIMITATIONS`; not `DAY14_GENERAL_AGENT_COMPLETE` or `GIT_PUBLISHED`.
