# Публичный export и исключённые материалы

Candidate собран по явному whitelist. Шесть исходных архивов сохранены отдельно
и не включены в ZIP для GitHub. Их hashes и результат manifest audit указаны
в `evidence/source-archives.json`.

Публично поставляются только учебный app source, инструкции двух профилей,
существующие pure controller components, inert console source references,
task-only sanitized результаты, проверяемая metadata и новая документация.
Бизнес-код компании, личная переписка и содержимое auth files для этого export
не требуются и не добавляются.

## Исключённые source members

В [evidence/excluded-files.json](evidence/excluded-files.json) перечислены
**1702 source members**, не скопированные в public candidate, с относительным
именем внутри исходного архива и причиной. Это только каталог исключений,
а не содержимое исключённых файлов. Одинаковые материалы в разных архивных
версиях считаются отдельными members; числа не означают уникальные события.

| Категория | Members | Решение |
|---|---:|---|
| Полные private history/budget journals | 17 | Не публикуются; нет raw JSONL и replay text |
| Native transport и machine-bound evidence | 87 | Не публикуются account/session/RPC outputs, payloads и private runner probes |
| Исторические platform/recovery/admission материалы | 794 | Не включаются machine-bound launchers, snapshots и forensic/support данные; работа по ним не возобновляется |
| Оригинальные screenshot pixels | 10 | 8 основных исторических views и 2 appendix остаются приватными; исходные hashes доступны в реестре |
| Synthetic fixtures | 20 | Не используются как доказательство реального model run |
| Прочие неминимальные исторические support materials | 774 | Исключены из Course Minimum export |

Не все исключённые файлы содержат секреты: отчёт различает privacy и отсутствие
необходимости в минимальной поставке. Auth/credentials не переносились. Старые
global settings, личные account updates, native state databases и исходные
архивы не входят в publication whitelist.

## Sanitization

- Из task-only ответов и native stdout удалены конкретные machine home,
  временные runtime/workspace paths и контрольные маркеры частной истории.
  Вместо них стоят явные placeholders.
- В logs сохранены фактические exit codes, expected RED assertions, counts
  и последующий GREEN. В ответах не изменены FAIL/BLOCKED/PASS.
- Original screenshot pixels не редактировались и не публикуются; новые
  «доказательные screenshots» не создавались. Учебное evidence представлено logs.
- Hash chains полных журналов и 10 реальных RPC replay проверены приватно
  при сборке; публичны только metadata и hashes. Сам public package не даёт
  возможности заново проверить всю исключённую историю.

`evidence/file-provenance.json` связывает byte-identical source copies и
sanitized projections с исходными members/SHA. `assembly-redactions.json`
фиксирует категории замен. Sanitized files не объявляются оригиналами,
и их новые hashes не подставляются вместо старых historical hashes.

Финальный targeted scan проверяет candidate на machine paths, токены известных
форматов, JWT, private keys, bearer values, e-mail и запрещённые binary/raw-history
exports. Дополнительно проверяется весь allowlist. Это scoped privacy review,
а не математическое доказательство отсутствия любых возможных секретов.
Все native account/auth payloads исключены независимо от regex-результата.

Данная проверка не является новым исследованием ACL/SQLite или восстановлением
утраченных файлов. Ни один historical source/evidence файл не перезаписан.
