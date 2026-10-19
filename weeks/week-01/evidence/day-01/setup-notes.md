# Gate 1 setup findings before the baseline freeze

These are implementation/setup checks, not controlled v1/v2 generations.

1. Initial editable installation with `--no-build-isolation` failed because
   Hatchling's editable backend required `editables`, which was not yet in
   the development lock. It is now pinned in build and dev requirements.
2. Initial pytest collection failed under warnings-as-errors: Starlette 1.9.0
   deprecates the old `httpx` TestClient backend. The installed Starlette source
   and official TestClient documentation were inspected; dev requirements now
   use `httpx2`. No warning suppression was introduced.
3. Initial Ruff checks found one long/unformatted tuple in the architecture
   test. It was formatted before final verification and baseline freezing.

Final authoritative check results are in `baseline-checks.txt`. No failing
controlled generation was repaired or replaced: neither generation has run.

Primary references consulted:

- https://fastapi.tiangolo.com/tutorial/testing/
- https://starlette.dev/testclient/
- https://docs.pydantic.dev/latest/concepts/validators/

The locked installed versions, rather than an unversioned tutorial, determine
the dependency set used by the final baseline.
