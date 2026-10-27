# Day 4 R2 — матрица требований и источников

Итог по актуальному Control: PARTIAL_DELIVERY / NOT_COMPLETE; Gate6 PARTIAL_ACCEPTED final.
PASS в отдельной строке означает только ограниченный критерий и не повышает общий статус.
FUNCTIONAL_HUMAN_ASSISTED сохраняет участие оператора. Expected RED считается ожидаемым
падением регрессии; это не PASS неисправленного кода. Новых запусков здесь нет.

| ID | Критерий | Статус критерия | Принятое/наблюдённое значение | Источники | Ограничение |
| --- | --- | --- | --- | --- | --- |
| R01 | Gate0: Mac/Ollama/Continue setup | PASS | ACCEPTED | C; S5 / GATE6_OFFLINE_REVIEW_RU.md | Локальная среда принята; Work не повторял Mac preflight. |
| R02 | Gate1: реальный Continue Chat | PASS | ACCEPTED | C; S2 review; S5 review | Наблюдён ранее, не новый запрос этой поставки. |
| R03 | Gate1: настоящий inline Autocomplete | PASS | ACCEPTED | C; S5 review; S6 evidence/OBSERVATIONS.json | Факты UI/FIM из проверенных evidence; обычный Chat не выдан за inline. |
| R04 | Gate2: полный Day1 Rules body в Chat system context | PASS | ACCEPTED | C; S2 evidence/console/console.original.txt | Chat context подтверждён. Не доказательство послушания каждому правилу во всех генерациях. |
| R05 | Gate2: options/config control | PASS | ACCEPTED | C; S2 review; S5 review | 8192/1024/0.1/0.9 — проверенные условия; не byte-exact trace каждого запроса. |
| R06 | Rules в Agent и успешное native tool execution | NOT_MET | NOT_MET | C; S1 report; S2 review | Chat + Apply не переименованы в Agent; Rules не применяются к FIM автоматически. |
| R07 | Gate3: исходный Agent и read_file probe | FAIL | FIRST_AGENT_FAIL / TOOL_PROBE_FAIL | C; S1 GATE3_RECOVERY_REPORT_RU.md; S4 comparison | Текстовый tool JSON не подтверждает исполнение; исходные FAIL сохранены. |
| R08 | Gate3: ранний Chat + Apply fallback | BLOCKED | EARLIER_CHAT_APPLY_BLOCKED | C; S1 report; S4 comparison | Контекстный блокер сохранён; код тогда не применён. |
| R09 | Gate3: PATCH /tasks/{task_id}/status | FUNCTIONAL_HUMAN_ASSISTED | FUNCTIONAL_RECOVERY_ACCEPTED | C; S1 source/src/bublik/application/service.py, api/routes.py, api/schemas.py; logs/acceptance-17.xml | Три Chat-компонента, операторские Apply/import/format corrections; не автономный результат. |
| R10 | Gate3: прежние tests и frozen acceptance | PASS | 38/38 existing; 17/17 frozen Day1 | S1 logs/pytest-38.xml; logs/acceptance-17.xml | Архивные результаты, Ruff lint/format/compile exit0; тесты не пересчитываются суммой. |
| R11 | Gate4: первый ответ Qwen | FAIL | STATIC_FAIL / PARTIAL_CONTENT | C; S2 GATE4_FIRST_MODEL_ATTEMPT_R1_REVIEW_RU.md | В тесте отсутствовал pytest; canonical enum/аннотации требовали вмешательства. |
| R12 | Gate4: recovery R1 collection | BLOCKED | COLLECTION_BLOCKED_NOT_RED | S3 GATE4_BUGFIX_HUMAN_ASSISTED_R3_REVIEW_RU.md | Отсутствовал класс исключения; collection error не считается RED. |
| R13 | Gate4: prepared-baseline RED | PASS | EXPECTED_RED_2_FAILED_1_PASSED_ACCEPTED | S3 nested inputs/accepted-r2-RED_EXPECTED.xml; red-adjudication-r3.json | Оператор добавил error contract; R2 wrapper FAIL сохранён; это не pristine Day2 RED и в R3 не повторён. |
| R14 | Gate4: исправленная доменная валидация | FUNCTIONAL_HUMAN_ASSISTED | FUNCTIONAL_PASS_HUMAN_ASSISTED_ACCEPTED | C; S3 review; nested observed-files/src/bublik/domain/task.py | Операторские regression/error class/canonical fix; GREEN3/3 и frozen13/13. |
| R15 | Gate4: регрессия, frozen/baseline/full/external | PASS | 3/3; 13/13; 38/38; 41/41; 17/17 | S3 nested GREEN.xml, DAY2_13.xml, EXISTING_38.xml, FULL_TESTS.xml, DAY1_17.xml | Полный41 = прежние38 + новые3; наборы не суммируются как независимые tests. |
| R16 | Gate5: Cloud vs Local evidence comparison | PASS | EVIDENCE_COMPARISON_ACCEPTED | C; S4 GATE5_CLOUD_VS_LOCAL_COMPARISON_RU.md | Реальные Cloud feature tools/subagent отмечены; Local native tool loop NOT_MET. |
| R17 | Сопоставимые e2e speed / throughput / cost | NOT_MET | NOT_ESTABLISHED | S4 comparison; C | Разные workflows/tools/baselines; UI FIM и pytest duration не равны LLM e2e latency. |
| R18 | Gate6: offline итог R1/R2 | PARTIAL | PARTIAL_ACCEPTED_FINAL | C; S5 review/checks; S6 result/observations | Chat/FIM наблюдались. R1 raw BLOCKED, R2 EVIDENCE_ADDED, происхождение/сохранение ограничены. |
| R19 | Gate6 R3: сохранённая рабочая реализация | FAIL | R3_FAIL_INDENTATION_ERROR | C; S7 STATUS.json; evidence/SCRATCH_BYTES_ANALYSIS.json | Сохранено98bytes, но 3vs4 spaces; виновник UNDETERMINED. |
| R20 | Gate6 R3: after-boundary network/Ollama probes | NOT_RUN | NOT_RUN_AFTER_STOP | C; S7 STATUS.json; evidence/NETWORK_REVIEW.json | Остановка после syntax error; новый прогон/фиксы запрещены, повторы CANCELLED. |
| R21 | Native local Agent contract | NOT_MET | NOT_MET | C; S1 report; S2 review; S4 comparison | Успешный model-initiated tool loop не подтверждён. |
| R22 | Видео: факт записи со слов пользователя | PARTIAL | VIDEO_RECORDED_USER_CONFIRMED | C; S8 только как сценарий | Файл NOT_RECEIVED; план не доказывает содержимое готовой записи. |
| R23 | Видео: terminal-only / privacy / duration / содержание | NOT_RUN | VIDEO_CONTENT_REVIEW_NOT_RUN | C; DAY4_VIDEO_STATUS_RU.md | Проверять только при предоставлении actual video; SHA/path/URL не придуманы. |
| R24 | Day4 Course Minimum / teacher acceptance | PARTIAL | PARTIAL_DELIVERY / NOT_COMPLETE | C; все предыдущие строки | Full PASS/TEACHER_ACCEPTED не установлены; human-assisted и offline gaps сохранены. |
| R25 | Публичная поставка и Draft PR | BLOCKED | CONTROL_SIGN_OFF_REQUIRED | C; DAY4_PUBLICATION_PLAN_RU.md | Только предложение. Публикация/Git-операции не разрешены и не выполнены. |

## C — актуальный Control

Файл: `BUBLIK-D4-FINAL-DELIVERY-R2-VIDEO-RECORDED-CONTROL(1).md`. SHA256: `6c6ce25158d39bc872e9b7cd14edbae1842211bb79e9da2620683d966cd2c253`. Полностью прочитан; ledger обязателен. Подтверждение записи видео взято из этого решения, не из файла записи.

## Точные архивы и прочитанные члены

### S1 — Gate 3 recovery

`bublik-day4-gate3-recovery-evidence-r1.zip`

SHA256: `e74ac7732d69e0abe418ad623b93fac8e596217bb7abcb2fdd96ff426eb79286`; 17420 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 29/29, CRC PASS. Private исходник не включён в публичный пакет.

- `GATE3_RECOVERY_REPORT_RU.md` — SHA256 `e5ec2eb2d1399e0d2ad845190b274810e434390880f596378815ba18e9eaeda8`.
- `source/src/bublik/application/service.py` — SHA256 `070d4b90f0249d1f285d1698914eda77675fd756104699ee93fb46521e8ce70b`.
- `source/src/bublik/api/routes.py` — SHA256 `2e421cd012340e1e2b6add40aea27c2cd4fb44ec9596bd8b53b85485975e60b0`.
- `source/src/bublik/api/schemas.py` — SHA256 `40811e1f333c4a958bc2ca49366a9eca98c785ec84955207b17f956158692883`.
- `logs/pytest-38.stdout.txt` — SHA256 `5820660ec3010de64a702de867f5df2cf30c67130e042248a991f9440cddf42b`.
- `logs/acceptance-17.stdout.txt` — SHA256 `2c92763ebc85148ceb3debe387f9b6bea1b772e6478ca8a5f6125160e4af8444`.
- `logs/ruff-lint.json` — SHA256 `5d0dbc36432efd0f20ba33b229898847bae916d1c281e33c672fe63ad63ede37`.
- `logs/ruff-format.json` — SHA256 `105b96a297cfec571cae7209f8875ef8eccb83bb6dad51f182f4a8e71d71b0d0`.
- `logs/compile.json` — SHA256 `dfdf8d76cee782df9886bdaf8d4a1088feffdfe79308ab6b95ac5916aee8850a`.
- `logs/pytest-38.xml` — SHA256 `1a8281c92a70505d2682edb45c15121ab88fd44f16a25d86309ff7370b5660a6`.
- `logs/acceptance-17.xml` — SHA256 `45d2160f9a3b956c9ba980733e4885cf02d05680a9656d37b22aa75fd971a21e`.

### S2 — Gate 4 first answer

`bublik-day4-gate4-first-model-attempt-r1.zip`

SHA256: `62cace9c211596694b3eb15e7f60e76846d1f36153222e6224ad22d1c95d1add`; 1682858 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 23/23, CRC PASS. Private исходник не включён в публичный пакет.

- `bublik-day4-gate4-first-model-attempt-r1/GATE4_FIRST_MODEL_ATTEMPT_R1_REVIEW_RU.md` — SHA256 `7a90a311e3b5d39c3bd7cbf882a74011eddaad6f215cf48599ddecc22114d9fd`.
- `bublik-day4-gate4-first-model-attempt-r1/evidence/console/console.original.txt` — SHA256 `6d738d84c50c42347e269bd4b6c1b4fa5f6293f15fab3f7978b6cb908c7841f2`.

### S3 — Gate 4 final review

`bublik-day4-gate4-human-assisted-r3-review.zip`

SHA256: `a2204ebdc362d3bd63528d08e773312b99cf8f3c8c33fc6a17a36bfb51006be0`; 114995 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 5/5, CRC PASS. Private исходник не включён в публичный пакет.

- `GATE4_BUGFIX_HUMAN_ASSISTED_R3_REVIEW_RU.md` — SHA256 `c113793d07ab8d717e9f2bda06eac906821aaf62063df9f86d030e9cf6366b14`.
- `independent-review.json` — SHA256 `07e2abe9d75986d952543f1d7c500ab4dcbb2ced7ecd0e7682946da2a2138597`.
- `evidence/mac-original/bublik-day4-gate4-human-assisted-r3.zip` — SHA256 `7c39f2d33038a2de6c449fd9d944b094674c6ecf906e190fc0a097f36aa3c71d`.

### S4 — Gate 5 comparison

`bublik-day4-gate5-evidence-comparison-r1.zip`

SHA256: `3d1cd3f2b29d335e3f7e27cd25e7e5ec686217be87761e172a62293cfba1d8a1`; 32230 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 4/4, CRC PASS. Private исходник не включён в публичный пакет.

- `GATE5_CLOUD_VS_LOCAL_COMPARISON_RU.md` — SHA256 `4f610945eff275d654270e59bddb1da75e7a61ffbf5c94b36a25d2127c0a40a1`.
- `GATE5_EVIDENCE_MATRIX.json` — SHA256 `648e0ea9aec16b39befd27a9c729d10431f36853e439aad372fc4b10e22e88a3`.

### S5 — Gate 6 R1 review

`bublik-day4-gate6-offline-r1-review-private.zip`

SHA256: `6da1c47e4541e657e1831efb29e29c536c49514353f73efa03016489ead30254`; 3623034 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 21/21, CRC PASS. Private исходник не включён в публичный пакет.

- `GATE6_OFFLINE_REVIEW_RU.md` — SHA256 `1147488ea701d6ae68f36ea34c0887002909c3e2a50feb452460ea40da17e732`.
- `GATE6_OFFLINE_CHECKS.json` — SHA256 `c2421b2ca2f47e5b6ddc26dae2ef97c11ef42117f9702cd8fae4549e0d6587ba`.

### S6 — Gate 6 R2 review

`bublik-day4-gate6-existing-console-r2-review-private.zip`

SHA256: `202ef445344661db4ad64e32f13582146375cf6c7de0179e1875b55374726832`; 999398 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 16/16, CRC PASS. Private исходник не включён в публичный пакет.

- `GATE6_EXISTING_CONSOLE_R2_RESULT.json` — SHA256 `31d0c0384dbbb13265ff7bb5fe05e4a97c2312a7f0a30baabb8959a137bc6a94`.
- `evidence/OBSERVATIONS.json` — SHA256 `0f753f6356157973e031642c6056b5417baa99a21816ea3d88507f0e5e8833f9`.

### S7 — Gate 6 R3 review

`bublik-day4-gate6-functional-r3-review-private.zip`

SHA256: `cb36539ba6ceb358433cab456d1b16b80e0299c33a176ec91635180cc193c536`; 6837821 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 24/24, CRC PASS. Private исходник не включён в публичный пакет.

- `STATUS.json` — SHA256 `852e3600d06a3d956857642ba786e3140281222cd69927229ef327bf0be8a461`.
- `evidence/SCRATCH_BYTES_ANALYSIS.json` — SHA256 `0373d43522120f9d8ed01ef523f00906e441c04420382b70aab4e1910ad7e4f6`.
- `evidence/NETWORK_REVIEW.json` — SHA256 `8b6caefa8c723904049b09470889cca6e46666b3b0dd12e1ec326ad922a031b8`.
- `GATE6_FUNCTIONAL_R3_REVIEW_RU.md` — SHA256 `80604eda3ca80dd6998c296c84345354af232e2343deb16bbecb3ab56fa3d5d9`.

### S8 — Preparatory terminal-only video script, NOT actual video

`bublik-day4-video-terminal-r2.zip`

SHA256: `f29f7dd61391684604486f52c48c550f4271e03810c2e1b960666a5fe3b25bef`; 37652 bytes. Доступность: REVIEWED_IN_THIS_DELIVERY. Manifest 21/21, CRC PASS. Private исходник не включён в публичный пакет.

- `day4-video-terminal-r2/DAY4_VIDEO_DELIVERY_STATUS.json` — SHA256 `942824ca9e9bc1ff669a1f8db81714c5bbfde7b03cb0d74a7002234e528a5fad`.
- `day4-video-terminal-r2/DAY4_VIDEO_SCRIPT_RU.md` — SHA256 `12a3e8ac734c7c5105c1ca98bf77fc91110a70d556c6c0d6c6c2f9c6ad510cb3`.
- `day4-video-terminal-r2/DAY4_VIDEO_EVIDENCE_MAP.md` — SHA256 `942c42b6644bdc3ae276ca077487e20f044c27db327ef108cffbc7ae8dfad065`.

### S3 nested — исходные проверки Gate4

Реальный путь: `evidence/mac-original/bublik-day4-gate4-human-assisted-r3.zip` внутри S3. SHA256 nested ZIP: `7c39f2d33038a2de6c449fd9d944b094674c6ecf906e190fc0a097f36aa3c71d`; manifest89/89, CRC PASS.

- `inputs/accepted-r2-RED_EXPECTED.stdout.txt` — SHA256 `63f8b5c6133e0c51619b05c280aac1fff75aa356294ef933a914bb7e4226d9a5`.
- `inputs/accepted-r2-RED_EXPECTED.xml` — SHA256 `5d248a650d73e6b8c6ad9c6d79e5c7ae5d1a0b3a08ae00d605e780770ae17df1`.
- `red-adjudication-r3.json` — SHA256 `1ae5695cc473ecdd6701f81cf9bb81eacdcd94ce211f5d0af4f07fc0db42c1b2`.
- `GREEN.stdout.txt` — SHA256 `e0a6ea218ea5d725ce7272da8d68d45a029e489423e03af6960c7bff0f7fe414`.
- `DAY2_13.stdout.txt` — SHA256 `edf3d333fef3a773826ab22829091a2348d9f8a79032da0074fd997d1b9f76d9`.
- `EXISTING_38.stdout.txt` — SHA256 `5820660ec3010de64a702de867f5df2cf30c67130e042248a991f9440cddf42b`.
- `FULL_TESTS.stdout.txt` — SHA256 `ed1c75fda3b4ed3509c39f7e15c80bec75c42dd122fa03c579be7d496cd8747a`.
- `DAY1_17.stdout.txt` — SHA256 `6e2ff8346f32031453bf74d7b33efb5d6944a328f23006e950459699bead23b7`.
- `observed-files/src/bublik/domain/task.py` — SHA256 `b20675b9984517e034c800acf49edc44e7477455409caadf2863c082ed2d5690`.
- `COMPILE.json` — SHA256 `77d7f4c7efea221b385096a888947b0827cd123ace4dfd86e3ab2c879230e809`.
- `IMPORT.json` — SHA256 `54525ff395728f451143219c4cbe4790c35cdeee93ad97ba31cf9ec64956fbdb`.
- `RUFF_LINT.json` — SHA256 `ce18b5a7e51107ad589bf60b45084e5404ef936b947755a303df000d193052f8`.
- `RUFF_FORMAT.json` — SHA256 `90252037d1dbe4a5a15f017b2d35c7f9e3921737dedd83318f4313f25c872b8b`.
- `GREEN.xml` — SHA256 `0d56d0f15e318df1d2ea6ea2b57d28c6f570a72a8c849295c291779cb6195288`.
- `DAY2_13.xml` — SHA256 `f9ca7872b05ad6ffdeeab306a8db0b18591a1dc36a8c5cf382b192d8010ec6b2`.
- `EXISTING_38.xml` — SHA256 `2e072ccecde2d000e8bd0a2d385ebee36f6843454630942d150442007e35b735`.
- `FULL_TESTS.xml` — SHA256 `3d802f0d33b1867ec222abcee0c279fa68e7d512fd7fd2d609d109e45f5c9b55`.
- `DAY1_17.xml` — SHA256 `23ab65610946ff1972f04520714c87bffcf167f6229b355cd0e2a9f9458aef00`.

## Как читать происхождение

Члены ZIP и их bytes/хеши прочитаны; исторические команды не выполнялись. XML разобраны
как данные. Истории original Agent/tool probe и исходных Cloud runs в этой доставке
подтверждены текущим Control и указанными принятыми review, а не повторным аудитом всех
исходных native runtime journals. Такой повторный аудит NOT_REVIEWED_IN_THIS_DELIVERY.
Это не отсутствие доступных основных S1–S8: все восемь проверены.

S8 хранит историческое video_recorded=false на момент подготовки. Он не исправлялся;
новое VIDEO_RECORDED_USER_CONFIRMED задаёт C. Сценарий не доказывает соответствие готового
видео. Архивные DRAFT/PENDING в S3/S4/S6 также не переписаны; текущую приёмку задаёт C.
Реальный remote/main SHA здесь NOT_CHECKED: Git-команд не было.
