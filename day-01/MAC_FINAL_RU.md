> Финальная Mac-приёмка уже завершена: Course Minimum PASS. Этот документ сохранён как воспроизводимая процедура проверки; повторный запуск сейчас не нужен. Отчёт и SHA скриншотов: proof/mac-final-2026-10-20/. Прежний скриншотный блокер закрыт финальным acceptance.json; историческая формулировка в шагах ниже относится к состоянию до получения файлов.

# Mac — последняя проверка и настоящие скриншоты

Новых генераций не выполнять. Существующие v1/v2 и `$BUBLIK_LAB` не изменять.

1. Распакуйте учебный ZIP в новую отдельную папку. Перейдите в её корень. Проверьте пакет:

```bash
python3 -B verify_delivery.py
```

Команда проверяет manifest, ничего не исправляет и не вызывает Codex.

2. Создайте отдельную `.venv` в `app/` по README. Если `.venv` здесь уже есть после вашей предыдущей проверки, повторно создавать её не нужно. Требуется Python 3.13.3.

3. Выполните настоящий gate:

```bash
cd app
.venv/bin/python scripts/run_checks.py --output local-evidence/mac-foundation-001.json
echo "quality_gate_exit=$?"
```

Не удаляйте старый отчёт ради повторного запуска. При существующем `mac-foundation-001.json` используйте новое имя. Ошибка подготовки или тестов — BLOCKED/FAIL; версии не подменять. Это обычные проверки Python, **не** Generation 3.

4. Выведите в терминал сводку фактического отчёта:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('local-evidence/mac-foundation-001.json')
r = json.loads(p.read_text())
print('Bublik Day 1 — CLEAN FOUNDATION (not Generation 2)')
print('Environment:', r['environment'])
print('Versions:', r['tool_versions'])
for c in r['checks']:
    print(c['name'], c['status'], 'exit=', c['exit_code'])
print('Protected:', r.get('protected_before'), r.get('protected_after'))
print('OVERALL:', r['status'], 'Codex invocations:', r['codex_invocations'])
PY
```

Если использовали другое имя отчёта, измените **только путь** в этой команде. Не редактируйте сам JSON.

5. Откройте второй таб терминала в `app/` и покажите кусок правил:

```bash
sed -n '/## Delegation and quality gate/,$p' AGENTS.md
```

6. Сделайте два настоящих снимка терминала. Нажмите **Shift–Command–4**, затем выделите область терминала: один снимок сводки проверок, второй — Rules v2. Либо из корня пакета выполните:

```bash
mkdir -p screenshots
screencapture -i screenshots/01-mac-foundation-checks.png
screencapture -i screenshots/02-rules-v2.png
```

Выбирайте только терминал с учебными данными, без других приложений и личной информации. Снимки не должны изображать Work как Mac или чистовую копию как историческую Generation 2.

7. Передайте в чат оба PNG и `app/local-evidence/mac-foundation-001.json` (либо фактически выбранный отчёт). Этого достаточно для закрытия оставшегося критерия: повторять модель, native diagnostics или исторические генерации не нужно.

`screenshots/` и новые local-evidence не входят в исходный manifest, поэтому его не переписывайте. Дальнейшая приёмка проверит новые файлы отдельно и создаст новый append-only отчёт. Критерий настоящих скриншотов до их получения остаётся BLOCKED.
