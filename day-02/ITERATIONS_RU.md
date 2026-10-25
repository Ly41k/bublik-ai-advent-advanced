# Неудачные попытки и отдельные доработки

Original execution и последующая проверка сохранённого результата — разные
оценки. Эта поставка сохраняет обе. Никакой исторический файл не перезаписан.

| Turn | Профиль | Original execution / model | Что произошло и что доработано |
|---|---|---|---|
| 1 | Bug Fix v1 | FAIL / BLOCKED | Найдена причина Task.status и создан regression; pytest import bublik завершился exit 4. Fix не завершён. В v2 уточнены cwd, venv, PYTHONPATH и collection/RED/GREEN |
| 2 | Bug Fix v2 | FAIL / BLOCKED | Модель создала fix и 13-case regression, получила RED 10/3 и GREEN 13; полный Gate остановился на `No module named quality`. Отдельно проверен сохранённый patch на Mac: PASS; original FAIL сохранён |
| 3 | Researcher v1 | FAIL / PASS | Исследование и Markdown получены, исходный host validator отклонил результат. Сохранённые ответ, citations и Markdown отдельно проверены: PASS. Ошибка harness не приписана новому поведению модели |
| 4 | Researcher v1 | FAIL / BLOCKED | Модель отказала из-за интерпретации runtime read scope. В v2 уточнено различие разрешённого cwd и общего запрета private parent; обход permissions не разрешён |
| 5 | Researcher v2 | PASS / PASS | Реальное исследование с источниками; технический PASS. Редакционная оценка оставалась PARTIAL |
| 6 | Bug Fix v2 | FAIL / BLOCKED | Explanation-only запрос попал под требования полного fix Gate. Сохранённое объяснение проверено отдельно. V3 разделила Bug Fix и Discussion, сохранив stop-on-error |
| 7 | Bug Fix v3 / Discussion | PASS / PASS | Реальное объяснение существующего fix, чтение исходников; файлы не менялись. Это не новый успешный Bug Fix run |
| 8 | Researcher v3 | PASS / PASS | Реальный исследовательский ответ после switch; пользователь не принял стиль v3 |
| 9 | Researcher v3 | PASS / PASS | Ответ после restart консоли с прежней историей и активным researcher; NOT_ACCEPTED стиля v3 сохранён |
| 10 | Researcher v4 | PASS / PASS | Тот же контрольный вопрос, новый фактический ответ. Технический PASS с ограничением экспорта admission; historical editorial PARTIAL сохранена; позднейшее окончательное решение пользователя — ACCEPTED |

Последовательность версий и инструкции подтверждены точными hashes в
`evidence/ten-turn-ledger.json`. Для каждой попытки опубликован task-only
текст ответа в `evidence/turns/`; удалены machine paths и history markers,
а original raw SHA оставлен в ledger. Нового текста от модели при сборке нет.

V5 уточняет подачу Researcher и section recognizer; сохранённые offline contract
и integration checks PASS. Это **не реальное выполнение v5**: native загрузка,
новый ответ и human signoff отсутствуют. V5 не становится третьей ролью. По решению пользователя от 25.10.2026 — **DEFERRED / NOT_RUN**; Turn 11 **CANCELLED**. Researcher v4 принят, дополнительных испытаний не требуется. Историческая редакционная оценка v4 не переписывается.

Буквальное требование чистого успешного первого Bug Fix запуска остаётся
неподтверждённым. Задание допускает итерации после неуспеха, но достаточность
цепочки original FAIL → independent saved-patch PASS должен решить принимающий
ревьюер. Сборка не заменяет это решение.

Старые recovery здесь только описываются как уже существующие исторические
проверки. Нового восстановления, реконструкции receipts или повторения model
attempts не выполнялось. Старые лимиты 8/8, 9/9 и 10/10 остаются свойствами
соответствующих исторических версий; текущий бюджет Control — 10/11.
