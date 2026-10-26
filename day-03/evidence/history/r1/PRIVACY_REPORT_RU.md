# Privacy report — candidate r1

**PASS в указанном объёме проверки.** Просмотрены состав поставки и MCP/app logs; проверены 91 файлов до добавления этого отчёта и manifest по известным сигнатурам GitHub/OpenAI токенов, JWT и приватных ключей. Совпадений: 0. Запрещённых путей: 0. Подробности: PRIVACY_REPORT.json.

В архив не включены `.git`, `.codex`, credentials/auth.json, env-файлы, приватные Codex journals, browser profiles, SQLite/databases, venv/node_modules, caches/pyc и machine-bound конфигурации. Screenshots отсутствуют. Все MCP calls направлялись на локальный тестовый сервис; персональные данные не вводились.

Сырые execution logs сохранены без изменения: в них есть временные пути `/workspace`, `/tmp` и путь установленного Python. Это диагностика текущего запуска; файлы конфигурации хоста не копировались. Единственный добавленный агент получил только контракт и исходники Day 3, без credentials.

Git scope: 269 защищённых tracked файлов Day 1/2 сверены с Git blob SHA; несовпадений 0. Изменений вне day-03/: 0. Репозиторий не опубликован.
