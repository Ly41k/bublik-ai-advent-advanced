# Retained offline regression sources

These files are byte-identical copies of the already accepted E1/native-trace v2.0.3 and contract-test sources, plus their import dependencies. They are not a new model launcher. Run only `../tooling_regressions.py` with the foundation virtualenv.

`src/bublik/application/service.py` is the historical baseline fixture for source-reference validation. The service actually run by the foundation is `../app/src/bublik/`.

Do not invoke the legacy collector or diagnostic CLI from this reduced fixture tree. Real native trace extraction still uses the original complete Gate 2 package with its unchanged manifest chain. Regression tests use synthetic sessions and never prove a new real Codex invocation.
