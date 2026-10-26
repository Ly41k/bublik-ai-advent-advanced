# Git staging preflight r2 и оставшийся план публикации

Base main: `3c2ed09a2e5c9e35a70e18b11dfe0a29a675db66`, tree
`6964256fd812028900ed1fc121aa63b47ba53f25`. Remote HEAD повторно проверен.
В base нет day-02/. Day 1 tree: `ba4f0fc673214937a8ad76bee613d7d43837f2e9`.

## Разрешённый scope

Задача BUBLIK-D2-RESEARCHER-FINAL-DECISION разрешила staging preflight.
Создан отдельный Work checkout от точного base, исходное состояние CLEAN.
Локальная review-ветка — `review/day-02-course-delivery-r2`. Состояние Mac checkout
не проверялось; старый Mac audit не объявляется актуальным.

В index добавляются только явные пути из evidence/publication-allowlist.json,
prefix day-02/. Не используются git add ., git add -A и force-add. Исходные
архивы, raw history, auth, screenshots и forensic-данные не копируются в checkout.

Preflight проверяет actual Git status, staged path list, modes/blob SHA/content
SHA, staged diff против HEAD, отсутствие unstaged drift, gitignore positive и
negative probes, privacy именно bytes из index. Все 167 Day 1 tracked files
сравниваются с чистым base. Полный отчёт и final index fingerprint находятся в
control-review/ review ZIP, вне staged дерева. Сохранение отчёта не меняет index.

App — отдельная Day 2 учебная копия. Day 1, root source/tests/README/Rules и locks
не изменяются. Исторические source и task-only evidence r1 сохраняются; текущие
решения и delivery docs обновлены отдельно. Diff r1 → r2 приложен в review ZIP.

## После независимого Control review

1. Control проверяет конкретный staged набор, manifest и оставшееся literal
   first-run ограничение Bug Fix; финальный Course Minimum решает отдельно.
2. Перед commit сверить HEAD, branch и index fingerprint с reviewed report.
   При drift остановиться и проверить новый diff.
3. Только после отдельного разрешения выполнить commit/push и создать Draft PR
   с DRAFT_PR_RU.md, base main. Заголовок не объявляет Day 2 PASS.
4. При публикации с Mac или другого checkout staging нужно проверить заново:
   Work index не считается индексом другой машины.

Commit, push, PR и merge в этой задаче NOT_RUN. Merge не входит в план.
Researcher v4 User ACCEPTED; v5 DEFERRED / NOT_RUN, Turn 11 CANCELLED.
Исторические FAIL/BLOCKED и missing receipt сохраняются. Day 3 не начат.
