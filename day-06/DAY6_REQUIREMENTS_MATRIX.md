# Day 6 — матрица буквальных критериев

Course Minimum принят Control после проверки R5 и R6. PASS ниже относится к учебным
критериям и проверенным private evidence, а не к разрешению публикации.

| Пункт преподавателя | Статус | Проверяемое агрегатное evidence |
|---|---|---|
| «Возьмите готовый датасет» из Hugging Face | PASS | Emotion split, закреплённый revision; исходные 16000/2000/2000, обучение 3996 + validation 498; параметры JSON |
| Выразительное изменение поведения / жёсткий формат | PASS | Primary20 exact format 5/20 → 20/20; strict correct 1/20 → 12/20 |
| Посмотрите примеры и приведите к шаблону модели | PASS | Настоящий model chat template, system/user/assistant roles; prefix/completion/masking/no-truncation QA; описание в отчёте |
| Небольшая открытая модель и доступное железо | PASS | SmolLM2-360M bf16; Mac M1 Pro, 32 GiB, MLX/Metal; параметры JSON |
| Зафиксируйте, на чём обучали и сколько заняло | PASS | macOS/Python/core stack; 90.590454 s worker lifecycle, включая load/final checks |
| Запустите LoRA/QLoRA, следите за loss | PASS | Один LoRA, 400/400; 40 train + 9 validation points; loss summary JSON и график |
| Сохраните адаптер | PASS | Адаптер сохранён, загружен и реально использован в tuned inference; факт в отчёте, веса приватны |
| Возьмите 20 запросов, сравните Base/Fine-tuned | PASS | Primary20 заморожены до Base; 20 пар на одинаковых inputs/settings; метрики JSON |
| Что изменилось и что осталось прежним | PASS | Primary20: 18 changed, 2 unchanged, 11 improved, 7 both-wrong changed; отчёт/метрики |
| «Найдите запросы, на которых дообученная модель стала хуже» | PASS | Primary20: 0; отдельный заранее frozen supplemental120: 1 strict regression. Проверен конкретный private случай; публично только агрегат |
| Результат: дообученная модель, сравнение и параметры | PASS | Реальный adapter load/use, primary20 и отдельный probe120, run parameters и loss; веса остаются локальными |

Все числа отдельно в [DAY6_METRICS.json](DAY6_METRICS.json); метод и ограничения —
[DAY6_FINAL_REPORT_RU.md](DAY6_FINAL_REPORT_RU.md). R6 не выполнял дополнительного train.
Общий показатель для двух выборок не рассчитывается. Отдельный пример, raw records и
private audit не публикуются. Правила и attribution — [DAY6_PRIVACY_LICENSE_RU.md](DAY6_PRIVACY_LICENSE_RU.md).
