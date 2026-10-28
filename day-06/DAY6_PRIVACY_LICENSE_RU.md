# Day 6 — приватность, лицензии и attribution

## Источники и дата проверки

Проверено **28.10.2026 (Europe/Kyiv)** по текущим HF metadata и закреплённым карточкам;
текущие revisions совпали с использованными, содержимое карточек совпало с evidence.

- Модель [mlx-community/SmolLM2-360M-Instruct](https://huggingface.co/mlx-community/SmolLM2-360M-Instruct),
  revision `5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7`.
  [Закреплённая карточка](https://huggingface.co/mlx-community/SmolLM2-360M-Instruct/blob/5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7/README.md)
  указывает **Apache-2.0**. [Текст Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- Датасет [dair-ai/emotion](https://huggingface.co/datasets/dair-ai/emotion), configuration split,
  revision `cab853a1dbdf4c42c2b3ef2173804746df8825fe`.
  [Закреплённая карточка](https://huggingface.co/datasets/dair-ai/emotion/blob/cab853a1dbdf4c42c2b3ef2173804746df8825fe/README.md)
  и [текущая карточка](https://huggingface.co/datasets/dair-ai/emotion/blob/main/README.md)
  указывают **other** и ограничивают использование образовательными и исследовательскими
  целями. Dataset не обозначается как Apache/MIT/CC; коммерческое распространение и
  право перепубликовывать исходные материалы здесь не утверждаются.

Карточка датасета просит цитировать:

Elvis Saravia, Hsien-Chi Toby Liu, Yen-Hao Huang, Junlin Wu, Yi-Shin Chen. 2018.
[CARER: Contextualized Affect Representations for Emotion Recognition](https://aclanthology.org/D18-1404/).
EMNLP 2018, pp. 3687–3697. DOI: 10.18653/v1/D18-1404. Метаданные сверены с ACL Anthology.

## Состав и ограничения публикации

Эксперимент учебный. Этот каталог содержит собственное описание, параметры и числовые
агрегаты результатов. Он не распространяет dataset или модель. В публичный пакет не
включены исходные тексты и индивидуальные ответы, rendered inputs и token sequences,
индивидуальные ID или digests, screenshots private evidence, пользовательские пути,
machine identifiers, полный environment dump, секреты, веса модели или адаптера.

Проверенный конкретный случай R6 regression остаётся в приватном evidence. Публично
сообщается только количество: 1/120 в supplemental probe; 0/20 в primary. Даже пара
индивидуальных меток этого случая здесь не приводится. Агрегаты не заменяют private
проверку каждого случая и не расширяют права на исходные данные.

Primary20 мала, supplemental120 исследовательская и сбалансирована; оценки не
объединяются. Strict raw-label scoring и неоднозначность эмоций ограничивают выводы.
Содержание и приватность этой документации приняты Control при проверке R7.
Это принятие документации не является публикацией, лицензированием весов или
разрешением дальнейшего распространения чужих материалов.
