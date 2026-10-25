---
name: quality-gate
description: Validate the isolated Bublik Day 2 runtime using the host-provided trusted runner.
---

Require explicit trusted_runner, app_root and report_path. Missing inputs return
BLOCKED / MISSING_REQUIRED_INPUT without executing anything. Never guess paths.
Run the supplied Python interpreter with trusted_runner --app app_root --output
report_path. Read the real report and return status/check exit codes. Preserve
failures. Do not edit old tests/locks/Rules/manifests, install, delegate or retry.
This procedure provides programming checks, never full Day 2 acceptance by itself.
