Bug Fix Engineer: Нашёл: Task.__post_init__ проверяет только title; runtime-проверка status отсутствует. Аннотация TaskStatus не обеспечивает инвариант.
Исправил: добавил tests/test_task_status_invariant.py — 13 случаев для недопустимых значений, replace, TODO/DONE и значения по умолчанию. Исходник пока не изменён.
Проверил командой:
PYTHONDONTWRITEBYTECODE=1 <PRIVATE_HOME_PATH> -m pytest -p no:cacheprovider tests/test_task_status_invariant.py > <PRIVATE_RUNTIME_PATH> 2>&1
Результат: exit 4, ModuleNotFoundError: No module named 'bublik' при загрузке conftest. Я не настроил путь импорта src. Это ошибка запуска, а не RED регрессии.
Статус: BLOCKED. Остановился согласно требованию профиля «Stop after failed verification; no automatic retry». Лог неудачного запуска сохранён.
