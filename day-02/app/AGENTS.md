# Bublik Day 2 Project Rules

Source: accepted Day 1 Project and Global Rules at main 3c2ed09a2e5c9e35a70e18b11dfe0a29a675db66.
Python 3.13.3; FastAPI/Pydantic; immutable domain; TaskRepository Protocol;
TaskService owns business decisions; main alone wires infrastructure.
Use typed functions, absolute imports, snake_case and PascalCase. Domain uses
stdlib only; no reverse layer imports. No silent errors or invented success.
Preserve existing tests, dependencies, lockfiles and protected manifests.
Only the current profile's developerInstructions determine allowed actions.
Day 1 generations and agent delegation are historical, never auto-run them.
No commit/push/publish, global config changes, extra agents, network tools or SQLite.
Use $quality-gate for validation; trusted controller performs final checks.
