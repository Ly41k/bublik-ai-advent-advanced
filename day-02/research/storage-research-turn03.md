# Где Бублик хранит задачи и что потребуется для SQLite

Researcher: исследование текущих исходников, без изменения приложения.

Код экспедиции из запроса: `<HISTORY_MARKER_WITHHELD>`.

## Файлы

Все пути ниже относительны runtime app; канонический префикс — `day-02/app/`. Номера источников соответствуют разделу «Источники».

| Файл | Символ | Назначение |
|---|---|---|
| `src/bublik/domain/task.py` | `Task`, `TaskStatus` | Неизменяемая задача, проверка заголовка и статуса |
| `src/bublik/application/repository.py` | `TaskRepository` | Порт хранения: `save` и `get` |
| `src/bublik/application/service.py` | `TaskService` | Создание, получение и изменение статуса |
| `src/bublik/infrastructure/memory_repository.py` | `InMemoryTaskRepository` | Хранение задач в словаре под блокировкой |
| `src/bublik/main.py` | `create_app` | Создание конкретного репозитория и сервиса |
| `src/bublik/api/dependencies.py` | `get_task_service` | Получение сервиса текущего приложения |
| `src/bublik/api/routes.py` | `get_task` | Вызов сервиса и преобразование отсутствия задачи в HTTP 404 |
| `tests/test_api.py` | `test_application_instances_do_not_share_tasks` | Описание ожидаемой изоляции экземпляров приложения |
| `docs/BASELINE_CODE_EXAMPLES.md` | Раздел Repository port | Документация границы между сервисом и хранилищем |

Также прочитаны README, проектные правила, pyproject.toml, модели API, доменные ошибки, тесты репозитория, сервиса, архитектуры и фикстура API. Ссылки README на документы вне runtime app не открывались.

## Связи

Фактический путь запроса:

`HTTP → API handler → get_task_service → app.state.task_service → TaskService → TaskRepository → InMemoryTaskRepository → dict[UUID, Task]`.

`create_app()` — точка сборки: она создаёт FastAPI, затем `TaskService(InMemoryTaskRepository())` и сохраняет сервис в `app.state` [4]. API получает именно этот сервис через `request.app.state.task_service` [5]. Это не создание отдельного репозитория на каждый запрос.

`TaskService` принимает `TaskRepository` через конструктор. Он импортирует порт и доменные типы, а не конкретный адаптер. Создание задачи вызывает `save`; обновление статуса создаёт новое значение через `dataclasses.replace` и снова вызывает `save`; чтение вызывает `get` [2]. Порт требует возвращать `None`, если задача отсутствует, и заменять полное значение при сохранении существующего идентификатора [3].

Доменная `Task` — frozen dataclass. Проверка и нормализация её значений находятся в домене [8]. Хранение не должно обходить эти инварианты.

## Результаты исследования

### Факты из текущего кода

1. Фактическое хранилище — `self._tasks: dict[UUID, Task] = {}` в экземпляре `InMemoryTaskRepository` [1]. `save` присваивает значение по UUID, `get` читает его. Оба действия защищены `threading.Lock`.
2. В прочитанном коде этого адаптера нет записи в файл, SQL или восстановления данных. Название `save` описывает операцию порта и само по себе не гарантирует долговечность.
3. Каждый вызов `create_app()` создаёт новый экземпляр репозитория [4]. В исходниках теста `test_application_instances_do_not_share_tasks` второй экземпляр приложения ожидаемо отвечает 404 для задачи первого [6]. Тест прочитан, но в этом исследовании не запускался.
4. Если репозиторий вернул `None`, `TaskService.get_task` поднимает `TaskNotFoundError` [2]. Обработчик GET преобразует её в HTTP 404 [7].
5. Документация явно описывает независимость сервиса от реализации хранилища [9]. Это согласуется с текущими импортами и constructor injection.

### Выводы из фактов

**Причина исчезновения задач — время жизни памяти.** Пока экземпляр приложения и его репозиторий доступны, запросы используют один словарь. При завершении процесса память исчезает. Следующий запуск вызывает фабрику и начинает с пустого словаря; загрузки предыдущего состояния нет.

Даже без завершения процесса новый вызов `create_app()` создаёт отдельное хранилище. Поэтому точная граница состояния — экземпляр репозитория, принадлежащий экземпляру приложения, внутри процесса.

Если запускать несколько worker-процессов с такой фабрикой, каждый получит собственное хранилище. Следовательно, задача, созданная через один worker, может отсутствовать у другого. Это вывод из устройства кода; фактическая конфигурация deployment не исследовалась.

`Lock` защищает отдельные операции со словарём внутри процесса. Она не сохраняет данные на диск, не объединяет worker-процессы и не делает всю последовательность чтение → изменение → сохранение атомарной.

Исправление проверки `Task.status`, присутствующее в текущем домене, относится к корректности значения задачи. Оно не меняет срок хранения данных.

### Предложения для будущего SQLite

Ниже описан проект возможных изменений. Это не существующие возможности и не выполненная реализация.

1. **Добавить инфраструктурный адаптер.** Предлагаемый `SQLiteTaskRepository` должен структурно удовлетворять существующему `TaskRepository`: `save(Task) -> None` и `get(UUID) -> Task | None`. Для этих операций менять порт и бизнес-сервис не требуется. SQL и `sqlite3` должны оставаться в infrastructure; домен сохраняет зависимости только от stdlib и не получает знаний о базе.
2. **Изменить сборку в `main`.** Конкретный SQLite-репозиторий должен создаваться только в `main` и передаваться в `TaskService` через существующий конструктор. API продолжит получать сервис через текущую зависимость. Дополнительные providers или слои для этого не нужны.
3. **Определить постоянный файл БД.** Путь и срок жизни файла должны задаваться явно. Для сохранения после перезапуска нужен один и тот же доступный файл; `:memory:` или новый временный файл при запуске цели не достигают. При контейнерном размещении файл должен находиться на сохраняемом томе. Конкретный путь и deployment в запросе не заданы.
4. **Определить схему и преобразования.** Достаточная отправная точка — таблица задач с UUID как текстовым первичным ключом, заголовком и текстовым статусом. Запись должна сохранять полное значение с заменой по идентификатору, например через UPSERT. Чтение должно восстанавливать UUID, TaskStatus и Task через доменный конструктор. Ограничения NOT NULL, первичного ключа и допустимых статусов поддержат целостность; точную схему и версионирование ещё предстоит утвердить.
5. **Обеспечить транзакционную запись.** `save` должен завершаться успешно только после успешного commit; ошибка требует rollback и явного распространения ошибки. Возвращать `None` при ошибке чтения нельзя: по контракту это означает отсутствие задачи. Сбой диска, блокировку БД и повреждённую запись нельзя выдавать за 404 или успешное сохранение.
6. **Определить жизненный цикл соединений.** HTTP-обработчики синхронные, поэтому нельзя без анализа разделить одно соединение SQLite между потоками. Нужна явная стратегия: соединение на операцию либо управляемое соединение с согласованной синхронизацией и закрытием. Для долгоживущих ресурсов подходит lifecycle приложения, подключённый в `main`. Следует отдельно определить timeout и поведение при конкурирующих записях; WAL — возможное решение, а не обязательный архитектурный слой.
7. **Сохранить разделение ошибок.** `TaskNotFoundError` и его HTTP 404 остаются прежними. Если для отказа хранилища нужен стабильный API-ответ, потребуется согласовать отдельный тип ошибки на границе приложения и его HTTP-преобразование. SQL-исключения не должны проникать в бизнес-решения или раскрывать внутренние сведения клиенту.

Текущий порт достаточен для сохранения полных значений, но не обещает атомарности последовательности `get` → `replace` → `save`. Если будущие требования включат защиту от потерянных конкурентных обновлений, понадобятся отдельные решения о версиях или транзакционной операции; включать их в минимальный переход без требования не следует.

Предлагаемая последующая проверка: контракт `save/get`, замена полного значения, отсутствие UUID, сохранение статуса, повторное открытие одного файла после закрытия первого репозитория, доступ из нового приложения, независимость разных файлов, rollback и ошибки хранения. Для файлового адаптера совместное использование одного файла должно проверяться отдельно от существующей изоляции memory-приложений. Текущие тесты не изменялись.

## Выводы

Бублик сейчас хранит задачи в RAM, а не в постоянной базе. Перезапуск создаёт новый пустой репозиторий. Архитектурная точка расширения уже есть: `TaskRepository`. Минимальный переход к SQLite затрагивал бы инфраструктурный адаптер и сборку в `main`, а также требовал бы решений о файле, схеме, транзакциях, соединениях и обработке отказов. Переписывать домен, сервис и HTTP-контракт ради самого хранения не требуется.

## Источники

Цитаты ниже дословно взяты из прочитанных файлов; SHA-256 вычислены по полным байтам файлов через `hashlib` указанного интерпретатора.

### [1] InMemoryTaskRepository

Путь: `src/bublik/infrastructure/memory_repository.py`  
SHA-256: `7bbd048d3dc66e6ba585c3d8a5f8ff507701699e86fa6a82b2328564b77bfbf2`

```python
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        self._lock = Lock()
```

```python
        with self._lock:
            self._tasks[task.id] = task
```

```python
        with self._lock:
            return self._tasks.get(task_id)
```

### [2] TaskService

Путь: `src/bublik/application/service.py`  
SHA-256: `3e2a2ef8b29464bbb3fe6bdf86e5ada64cf315d05f781849cb435a15979e7d1c`

```python
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository
```

```python
        task = Task(id=uuid4(), title=title)
        self._repository.save(task)
        return task
```

```python
        task = self.get_task(task_id)
        updated = replace(task, status=validated_status)
        self._repository.save(updated)
        return updated
```

```python
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
```

### [3] TaskRepository

Путь: `src/bublik/application/repository.py`  
SHA-256: `2c189cbe4ba09c43606f049fac69155cd4ee45d75a71670b0a6771bef766430f`

```python
class TaskRepository(Protocol):
    """Store tasks by identifier; save replaces an existing value."""

    def save(self, task: Task) -> None:
        """Persist the complete task value."""
        ...

    def get(self, task_id: UUID) -> Task | None:
        """Return a task, or None when it is absent."""
        ...
```

### [4] create_app

Путь: `src/bublik/main.py`  
SHA-256: `a2f9609fba57ba1a4292930a827a3233b3f4ab829cc6dcbebaa9c0d2ecf5406f`

```python
def create_app() -> FastAPI:
    """Create an application with its own repository and service."""
    app = FastAPI(title="Bublik Task Service", version="0.1.0")
    app.state.task_service = TaskService(InMemoryTaskRepository())
    app.include_router(router)
    return app
```

### [5] get_task_service

Путь: `src/bublik/api/dependencies.py`  
SHA-256: `08f9dc2baad342663d9f080ca15dd193c832f4b423d5a715a89b9c99ab8cc120`

```python
    service = request.app.state.task_service
    if not isinstance(service, TaskService):
        raise TypeError("Application task service is not configured")
    return service
```

### [6] test_application_instances_do_not_share_tasks

Путь: `tests/test_api.py`  
SHA-256: `87e0ddc62e105cc20f280ba3c430c804810a6d18ffe5433d84dd1cd5a7fad304`

```python
def test_application_instances_do_not_share_tasks(client: TestClient) -> None:
    task_id = client.post("/tasks", json={"title": "Only in first app"}).json()["id"]
    with TestClient(create_app()) as second_client:
        assert second_client.get(f"/tasks/{task_id}").status_code == 404
```

### [7] get_task

Путь: `src/bublik/api/routes.py`  
SHA-256: `5ed91abac2b725a6b3a984274a25f415df28094f8ba4895cf269b702ae02e657`

```python
    try:
        task = service.get_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return TaskResponse.model_validate(task)
```

### [8] Task и Task.__post_init__

Путь: `src/bublik/domain/task.py`  
SHA-256: `14277bd2a7d9fb2986493df226d3ac7482bdeb39bfff7e5c6fefa4ec5d4b7695`

```python
@dataclass(frozen=True, slots=True)
class Task:
```

```python
        try:
            status = TaskStatus(self.status)
        except (TypeError, ValueError) as error:
            raise InvalidTaskStatusError("Invalid task status") from error
```

### [9] Документация TaskRepository, раздел Repository port

Путь: `docs/BASELINE_CODE_EXAMPLES.md`  
SHA-256: `8829da569328a8b9a3f1b61425c6129f840d8fdd49b755138298f44a921854b2`

```text
The application consumes typed `save(Task)` and `get(UUID)` operations. Its
service does not construct or import the in-memory implementation.
```

## Ограничения

- Выполнено статическое чтение и поиск исходников и документации, вычислены SHA-256. Перезапуск приложения и тесты самостоятельно не выполнялись; PASS означает завершение исследования.
- По сообщению хоста, принятому пользователем: первоначальное выполнение Attempt 02 — FAIL/BLOCKED; независимая Mac-проверка точного сохранённого патча — PASS; RED — 10 failed, 3 passed; GREEN — 13 passed; host Quality Gate — 110 pytest + 17 external PASS. Это результаты хоста, не мои проверки. Финальный независимый Quality Gate после диалога ещё не наблюдался.
- Первая команда чтения с shell here-document завершилась до запуска Python: `zsh:1: can't create temp file for here document: operation not permitted`, exit 1. Затем чтение и хеширование успешно выполнены через `python -B -c` без here-document. Неудачная попытка остаётся в архиве событий.
- Исходники, тесты, конфигурация и документация не изменялись; SQLite не реализован. Markdown передан хосту через поле `document`; самостоятельное сохранение файла не выполнялось.
- Путь будущей БД, deployment, требования к долговечности и конкуренции не заданы. Предложения не подменяют эти решения вымышленными настройками.
