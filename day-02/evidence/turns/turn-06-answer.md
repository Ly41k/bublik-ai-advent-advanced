Bug Fix Engineer: Нашёл → самостоятельно прочитал Task и сохранённый regression-тест. Инвариант: после успешного создания `Task.status` содержит `TaskStatus.TODO` или `TaskStatus.DONE`. `TaskStatus(self.status)` также нормализует строки "todo"/"done"; недопустимые значения вызывают `InvalidTaskStatusError`. Frozen dataclass ограничивает последующее присваивание полей; `dataclasses.replace` создаёт новый объект и повторяет проверку.

Причина → согласно истории, раньше проверялся только title: аннотация `status: TaskStatus` сама не проверяет значения во время выполнения. Текущий исходник содержит исправление в `Task.__post_init__`. Это инвариант домена, независимый от хранения: обсуждавшийся переход на SQLite должен сохранять его при восстановлении Task, но проверка статуса не обеспечивает долговечность данных.

Что исправил → в этом обсуждении ничего; файлы оставлены без изменений.

Что проверил → статически установлено покрытие 13 случаев: пять недопустимых значений (`None`, `42`, "invalid-status", `[]`, `{}`) при создании; те же пять через replace с проверкой сохранности исходного TODO; два допустимых enum-статуса при создании и replace с сохранением id/title; один случай значения TODO по умолчанию. Нормализация допустимых строк отдельно этим модулем не проверяется.

Выполненная команда из указанного runtime app, exit 0:
<PRIVATE_HOME_PATH> -B -c 'from pathlib import Path; import hashlib; import sys; print("CWD", Path.cwd()); print("INTERPRETER", sys.executable); print("SRC_EXISTS", Path("src/bublik").is_dir()); paths = ("src/bublik/domain/task.py", "tests/test_task_status_invariant.py"); [(print("FILE", name, "SHA256", hashlib.sha256(data).hexdigest()), print(data.decode(), end="" if data.endswith(b"\n") else "\n")) for name in paths for data in (Path(name).read_bytes(),)]'
Подтверждены cwd, supplied interpreter и наличие src/bublik; выведены FILE, SHA256 и полный текст обоих файлов.

История → контрольный маркер первого продолжения Researcher: <HISTORY_MARKER_WITHHELD>. Исторический Turn 4 FAIL сохранён; Turn 5 technical PASS, editorial PARTIAL и human signoff PENDING остаются отдельными оценками. По сообщению хоста: Attempt 02 исходно FAIL/BLOCKED; независимая проверка сохранённого патча PASS, RED_EXPECTED — 10 failed / 3 passed, GREEN — 13 passed, Quality Gate — 110 pytest + 17 external PASS. Самостоятельно эти проверки я не выполнял.

Статус → статическое обсуждение завершено. BLOCKED относится к подтверждению полного Quality Gate текущего запуска: его результат ещё не получен; запуск оставлен хосту согласно запросу.
