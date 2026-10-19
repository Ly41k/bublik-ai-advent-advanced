# Transfer Gate 1 to the Mac without pushing

The delivery ZIP contains a self-contained Git bundle, this handoff, baseline
and delivery commit identifiers, and `SHA256SUMS`. It contains no `.venv`,
Python runtime, caches, credential files, or personal Codex configuration.
Keep the original ZIP as received.

## 1. Restore a new local working directory

Open Terminal in the folder containing the downloaded ZIP:

```bash
unzip bublik-day01-gate1.zip -d bublik-day01-gate1-transfer
cd bublik-day01-gate1-transfer
shasum -a 256 -c SHA256SUMS
git clone bublik-day01-baseline.bundle bublik-ai-advent-advanced
cd bublik-ai-advent-advanced
git remote set-url origin https://github.com/Ly41k/bublik-ai-advent-advanced.git
git status --short --untracked-files=all
git rev-parse baseline/day01-foundation
cat weeks/week-01/evidence/day-01/baseline-sha.txt
shasum -a 256 -c weeks/week-01/evidence/day-01/baseline-core.sha256
```

The two baseline SHA values must match, the worktree must be clean, and every
core-file checksum must pass. Choose a new destination if either extraction
or clone directory already exists; do not overwrite existing work.
Setting `origin` only records a URL locally and does not push anything.

`main` includes a later evidence-only commit; the lightweight tag
`baseline/day01-foundation` identifies the immutable source baseline used by
both future generations. `baseline-sha.txt` lives in the evidence commit so
that no file needs to contain the hash of its own Git commit.

## 2. Confirm the existing Mac tools

```bash
codex --version
codex login status
python3 --version
```

Expected: `codex-cli 0.163.0`, `Logged in using ChatGPT`, `Python 3.13.3`.
Do not reinstall or upgrade Codex. Do not copy authentication files into Git.

## 3. Install exactly the frozen environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python scripts/run_checks.py --output local-evidence/mac-baseline-checks.txt
git status --short --untracked-files=all
```

The dependency installation needs the package index. Checks run in process
with FastAPI TestClient and do not need a public server or external API.
Only checks actually run on the Mac count as Mac evidence. Return
`local-evidence/mac-baseline-checks.txt` for review; it is intentionally ignored
until reviewed and copied into the final evidence set.

## 4. Stop before the experiment

Do not launch the status-change control prompt yet. Gate 2 must:

1. Inspect existing global instructions/configuration without exposing secrets.
2. Create Rules v1 from actual baseline code and a small quality-gate skill.
3. Configure `architecture_report` returning `ArchitectureReport` and test
   successful invocation plus missing-input refusal without tool execution.
4. Demonstrate the actual loading of global/project instructions, skill,
   and agent configuration in **Codex CLI 0.163.0**.
5. Freeze the control prompt, acceptance tests, model, reasoning effort,
   runtime configuration and common skill/agent definitions.
6. Prepare clean independent source copies from the same baseline tag.

Use fresh sessions for v1 and v2. Keep previous generation evidence out of the
next generation's accessible working context. Separate clones separate Git
histories; they do not themselves provide OS-level file-access isolation.

No push, PR publication, merge, model-provider API payment, or global
configuration replacement is authorized by these handoff commands.
