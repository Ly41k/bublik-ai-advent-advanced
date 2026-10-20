# Rules v2 — журнал единственного изменения

Дата: 20 октября 2026. Основание: явное сообщение пользователя «Rules v2 Approval». Разрешена подготовка; Generation 2 не разрешена.

## Наблюдение

В реальной Generation 1 вызов native spawn_agent передал `task_name=status_architecture` и `agent_type=architecture_report`. Возвращённый тип — ArchitectureReport. Настроенный role корректен, но runtime task_name не называет тип результата явно.

Источник: `evidence/v1/run/native-sessions/2026/10/20/rollout-2026-10-20T17-12-57-01a159a8-8021-7fe3-b15d-a465f32b66fc.jsonl`, SHA-256 `46168f0f17b2ec309823761830a7ed2b368beba0cb69d6c70356575a544b1ae5`. Речь о фактическом JSON arguments spawn_agent, а не об имени файла или предположении по времени. Функциональная приёмка v1: 17/17, pytest 84 PASS. Функциональные дефекты не выявлены.

## Изменение

Только проектный AGENTS.md, раздел Delegation and quality gate, дополнен согласованным текстом:

```text
When invoking ArchitectureReportAgent, use agent_type="architecture_report"
and task_name="architecture_report" so the task name identifies its returned
ArchitectureReport type. Keep the existing entry and result contracts.
```

Rules v1 SHA-256: `af1843a2f9b2bf4bab6b34321a76cd117a3382ace53d3ad363d90aab04ea082d`.

Rules v2 SHA-256: `958b29ccf81dddc509ac2b3dd16afb433b76a56728f6a33632fbd1a23c83132e`.

Сохранены отдельные `rules-v1.AGENTS.md`, `rules-v2.AGENTS.md` и `rules-v1-to-v2.diff`. Остальные байты v1 не меняются: прежние заголовок/marker v1 намеренно сохранены, поскольку разрешены ровно три новые содержательные строки. Версию варианта определяют отдельный файл, revision manifest и его SHA-256.

## Ожидаемый эффект и сравнение

Ожидается `task_name=architecture_report` при том же role, входном/выходном контракте и задаче. Это гипотеза о соблюдении соглашения, не заявленное повышение функционального качества. Повторная функциональная приёмка использует неизменённые 17 cases и общий оценщик E1. Если оба прогона дадут 17/17, это равенство по функциональности, а не доказательство превосходства v2. Один прогон на вариант не является статистическим доказательством.

Global Rules, skill, subagent config, зависимости, baseline, модель/effort, R1/R2/profile и промпт сохраняются. Изменение оценщика E1 отделено от Rules и применяется одинаково к v1 и будущему v2. Исходная Generation 1 и её evidence не редактируются и не передаются в рабочую копию/CODEX_HOME v2.
