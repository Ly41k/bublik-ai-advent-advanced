# Publication staging — NOT_AUTHORIZED

Ровно 19 source/test/prompt/policy/docs путей подготовлены по allowlist принятого R2 release.
Code/tests/prompt/policy byte-identical; пять разрешённых Markdown документов обновлены по
owner-reported результатам 29.10.2026. Состав/hash manifest и evidence находятся вне публичного дерева
в отдельном Control Review пакете. Их нельзя автоматически добавлять к этим 19 путям.

В публичное дерево не входят data/, review/, reference/, make_candidates.py, ZIP evidence, weights,
cache, screenshots/video, raw logs, consent/rights/review sidecars или private outputs. Не включены
eval texts/gold/IDs/hashes, индивидуальные predictions, backup, owner paths/credentials или adapter.
Строки имён private output файлов внутри неизменного source — interface contracts, не private artifacts.
Тестовые IDs/строки и human positives — явно SYNTHETIC/TEST DOUBLE, не реальные eval или approvals.

Source-specific local-use/derivative rights подтверждены владельцем; это не independent legal audit.
Публичное распространение dataset/adapter остаётся unreviewed/not authorized. Модельные параметры,
код и агрегаты здесь не являются permission публиковать private inputs или weights.

Source integrity и public-subset validation не разрешают Git add/commit/push, PR, ready/merge или
publication. Текущий статус — staging pending Control Review, Git/publication NOT_RUN.
Нужен отдельный допуск на следующий Git stage и live-проверка refs/tree перед возможными записями.
Фактическая передача private dataset/adapter преподавателю ещё не подтверждена.

Privacy scan проверяет только staged19, известные risky path/secret/data patterns и документационные
изменения. Он не сравнивает с недоступным private corpus и не гарантирует абсолютное отсутствие утечки.
При missing corpus/reference public tests честно SKIP, не PASS. Historical P9R4 остаётся SUSPENDED/HOLD.
