Bug Fix Engineer: Нашёл: Task допускал недопустимый status при создании и dataclasses.replace.
Причина: __post_init__ проверял только title; аннотация типа не обеспечивает runtime-проверку.
Исправил: добавил преобразование TaskStatus с InvalidTaskStatusError для недопустимых значений и новый регрессионный модуль. TODO/DONE работают.
Проверил из <PRIVATE_RUNTIME_PATH>
Команда регрессии: PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 <PRIVATE_HOME_PATH> -m pytest -p no:cacheprovider -vv tests/test_task_status_invariant.py
1. С --collect-only: exit 0, собрано 13 тестов.
2. RED_EXPECTED: exit 1, 10 failed с DID NOT RAISE InvalidTaskStatusError, 3 passed.
3. После исправления GREEN: exit 0, 13 passed.
Quality Gate: PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1 <PRIVATE_HOME_PATH> <PRIVATE_TEMP_PATH> --app <PRIVATE_RUNTIME_PATH> --output <PRIVATE_RUNTIME_PATH>
Результат: EXECUTION_ERROR, exit 1, ModuleNotFoundError: No module named 'quality'. Остановился без повторного запуска.
Статус: BLOCKED. Точные команды, stdout, stderr и exit codes сохранены в <PRIVATE_RUNTIME_PATH> под именами status-collect.*, status-red.*, status-green.*, quality-gate.*.
