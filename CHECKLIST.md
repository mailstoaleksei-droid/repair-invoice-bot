# Repair Invoice Processor — Checklist

> Last updated: 2026-04-30
> Status legend: [ ] pending | [~] in progress | [x] done | [-] skipped

---

## Как работает процесс

```
ПОЛЬЗОВАТЕЛЬ                         СИСТЕМА
─────────────                        ───────
1. Кладёт PDF-счета                  Папка EingangsRG/
   в папку                           (SharePoint / локальная)
       │
2. Открывает Telegram                Bot "Repair"
   бот "Repair"                      ┌──────────────────┐
       │                             │ 🔧 Repair Bot    │
3. Нажимает кнопку ─────────────────▶│                  │
   "Обработать счета"                │ Найдено 12 PDF.  │
       │                             │ [Обработать?]    │
4. Подтверждает ────────────────────▶│                  │
                                     └──────┬───────────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │  PIPELINE (параллельно ×5)  │
                              │                            │
                              │  PDF ──▶ pdfplumber        │
                              │         (извлечь текст)    │
                              │              │             │
                              │         текст < 50 сим?    │
                              │         ├─ Да: СКАН        │
                              │         │   pdf2image      │
                              │         │   → GPT-4o Vision│
                              │         └─ Нет: ТЕКСТ      │
                              │             → GPT-4o-mini   │
                              │              │             │
                              │         JSON response      │
                              │         {date, truck,      │
                              │          price, seller,    │
                              │          invoice_nr,       │
                              │          kategorie,        │
                              │          confidence}       │
                              │              │             │
                              │         Валидация (4 ур.)  │
                              │              │             │
                              │         confidence ≥ 0.8?  │
                              │         ├─ Да: ✓ принять   │
                              │         ├─ 0.5-0.8: ⚠ review│
                              │         └─ < 0.5: ✗ manual │
                              │              │             │
                              │         INSERT PostgreSQL  │
                              │         (транзакция)       │
                              └──────────────┬─────────────┘
                                             │
                              ┌──────────────▼─────────────┐
                              │  РЕЗУЛЬТАТ                  │
                              │                            │
                              │  ✓ Успешные PDF:           │
                              │    → checked_* в папку года│
                              │    → строки в PostgreSQL   │
                              │                            │
                              │  ✗ Неуспешные PDF:         │
                              │    → manual/ папка         │
                              │                            │
                              │  Excel: новый .xlsx файл   │
                              │    → сохранён в папку      │
                              │    → отправлен в Telegram  │
                              │                            │
                              │  Сводка в Telegram:        │
                              │  "✓ 10 OK | ⚠ 1 review    │
                              │   | ✗ 1 manual | $0.08"   │
                              └────────────────────────────┘
```

**Тезисно:**
- Пользователь кладёт PDF в папку и нажимает кнопку в Telegram
- AI (GPT-4o-mini) извлекает данные из ЛЮБОГО поставщика без regex
- Сканы обрабатываются через Vision API (изображение → данные)
- Один счёт = один PDF (1-10 страниц), но может содержать несколько машин
- Общий Excel-отчет содержит лист `Problem Invoices` для ручной проверки частичных, ошибочных и необработанных счетов.
- Scania parser должен брать invoice из `RE-NR.` / `SCH...`, truck из `AMTL.KENNZ` / `Kennzeichen`, а не использовать `AUFTRAGS-NR.` как номер счета.

## 2026-04-30 Updates

- [x] Add `Problem Invoices` sheet to processing report with invoice numbers for partial, failed, duplicate, and unprocessed PDFs.
- [x] Add problematic invoice list to the Telegram final summary.
- [x] Fix Scania `SCHWM02670`: invoice must be `SCHWM02670`, not `47321-1-1-01`.
- [x] Fix Scania `SCHWM02670`: truck must be extracted from `AMTL.KENNZ: GR-OO 1511` as `GR-OO1511`.
- [x] Fix Scania `SCHPM01041`: extract `Kennzeichen` rows such as `GR-OO2456`, `GR-OO2459`, `GR-OO2458`, `GR-OO2457` and write one report row per truck.
- [x] Fix Scania invoice-date priority so vehicle header dates are not used as invoice dates.
- [x] Verify Scania `SCHWM02656`: invoice date must be `23/03/2026` from `RE-DATUM`, not vehicle header date `18/10/2022`.
- [x] Verify Scania `SCHWM03267`: invoice date must be `10/04/2026` from `RE-DATUM`, not vehicle header date `17/01/2011`.
- [x] Fix Scania Finance `SRD1041342`: invoice must be `SRD1041342`, truck must be `KO-HH322`, total must be read from `Netto gesamt (EUR)`.
- [x] Fix Scania `SCHWM03372`: invoice must be `SCHWM03372`, not `47322-1-1-01`, and truck must be `GR-OO8003`.
- [x] Add shared truck normalization for `KO-HH` numbers.
- [x] Fix Auto Compass `700415`: extract truck `GR-OO4501` from `Kennzeichen GR-OO 4501` style layouts.
- [x] Fix Pentoplus Truck Wash `V-RE002079`: extract truck numbers from `Nummernschild`, including `GR-OO2456`, and map them to wash line items.
- [x] Add Volvo Group Trucks Service Nord `0067816059`: extract invoice `0067816059`, truck `GR-OO1708`, invoice date `27/03/2026`, and net total `1188.18`.
- Gutschrift → отрицательная сумма
- Результат: Excel в Telegram + данные в PostgreSQL + PDF перемещён
- Неразобранные → `manual/` для ручной обработки или обучения промпта
- Параллельно до 5 файлов, ~30 сек на 50 счетов

---

## Принятые решения

| # | Вопрос | Решение |
|---|--------|---------|
| 1 | LLM для извлечения | OpenAI GPT-4o-mini (Structured Output / JSON mode) |
| 2 | OCR для сканов | GPT-4o-mini Vision, fallback → GPT-4o |
| 3 | Telegram бот | Отдельный бот "Repair" через @BotFather |
| 4 | Хранение | Excel (per batch) + PostgreSQL (cumulative) + Telegram |
| 5 | Категории | AI классификация из фиксированного списка |
| 6 | PDF структура | 1 PDF = 1 счёт (многостраничный) |
| 7 | Neon БД | Тот же проект `groo-lkw`, схема `repair` |
| 8 | Фреймворк бота | python-telegram-bot (PTB), как LKW бот |
| 9 | Где запускать | Тот же Windows PC, отдельный процесс |
| 10 | Проект | Новый GitHub repo `repair-invoice-bot` |

---

## Данные на выходе

| Column | Source | Notes |
|--------|--------|-------|
| Year | Из даты счёта | Integer |
| Month | Из даты счёта | Integer (1-12) |
| Week | ISO неделя из даты | Integer (1-53) |
| Date Invoice | AI из PDF | DD/MM/YYYY |
| Truck | AI из PDF | GR-OO формат |
| Total Price | AI из PDF | NETTO (внешний), BRUTTO (внутренний AC). Минус для Gutschrift |
| Invoice | AI из PDF | Номер счёта |
| Seller | AI из PDF | Название поставщика |
| Buyer | AI из PDF | "Groo GmbH" или "Auto Compass GmbH" |
| Kategorie | AI классификация | Rent, Repair, Service, Parts, Tyres, Toll, Fuel, TÜV, Wash, Insurance, Tax, Parking, Fees, Accessories, Other |

**Стоимость:** ~$0.005/текстовый счёт, ~$0.02/скан. Итого ~$1-5/мес при 200-500 счетах.

---

## Phase 0 — Инфраструктура

- [ ] **0.1** Создать Telegram бот "Repair" через @BotFather
  - Создать бота, получить токен
  - Задать имя, описание, команды
  - Result: бот отвечает на /start

- [ ] **0.2** Инициализировать проект
  - Создать GitHub repo `repair-invoice-bot`
  - Структура: `src/`, `prompts/`, `sql/`, `tests/`, `.env.example`
  - `.gitignore`, `requirements.txt`, `README.md`
  - Result: чистый репозиторий на GitHub

- [ ] **0.3** OpenAI API ключ
  - Получить/проверить ключ
  - Добавить в `.env` как `OPENAI_API_KEY`
  - Тест: простой вызов API
  - Result: API работает

- [ ] **0.4** PostgreSQL схема (Neon, схема `repair`)
  - Таблица `repair.invoices` — данные счетов + metadata
  - Таблица `repair.processing_log` — аудит
  - UNIQUE constraint: `(invoice_nr, seller, invoice_date)`
  - Индексы: по дате, по машине, по поставщику
  - Result: база готова

- [ ] **0.5** Импорт исторических данных
  - Одноразовый скрипт: Repair_2025.xlsx → `repair.invoices`
  - ~3800 строк за 2022-2025
  - Result: полная история в PostgreSQL

---

## Phase 1 — Core Pipeline

- [ ] **1.1** Модуль извлечения текста из PDF
  - pdfplumber: текст со всех страниц
  - Детект скана: `len(text.strip()) < 50` → скан
  - Скан: `pdf2image` → PNG для Vision API
  - Обработка ошибок кодировки
  - Result: текст или изображения готовы для AI

- [ ] **1.2** Модуль AI-извлечения (GPT-4o-mini)
  - Structured Output (`response_format: json_schema`)
  - System prompt с few-shot примерами (3 кейса: обычный, Gutschrift, мульти-truck)
  - NETTO/BRUTTO правило в промпте
  - Категоризация из фиксированного списка
  - Confidence score в ответе (0.0-1.0)
  - Для сканов: Vision API (изображение → JSON)
  - Двухступенчатая обработка сканов: mini → GPT-4o fallback при confidence < 0.7
  - Retry с backoff: 3 попытки (1s → 3s → 9s) через `tenacity`
  - Result: JSON с данными счёта

- [ ] **1.3** Модуль валидации (4 уровня)
  - **Schema:** все обязательные поля, правильные типы
  - **Format:** дата DD.MM.YYYY, truck GR-OO/HH-AG, price = float
  - **Logic:** дата не в будущем, price > 0 (кроме Gutschrift), month/week из даты
  - **Cross-check:** truck существует в реестре (`public.trucks`)
  - Confidence routing: ≥0.8 авто, 0.5-0.8 review, <0.5 manual
  - Result: валидные данные или причина отклонения

- [ ] **1.4** Модуль PostgreSQL
  - INSERT в транзакции (invoices + processing_log в одном COMMIT)
  - `ON CONFLICT (invoice_nr, seller, invoice_date) DO NOTHING` + warn
  - Connection pool: `asyncpg`, 3-5 соединений на batch
  - Логирование tokens/cost из каждого AI ответа
  - Result: данные в БД

- [ ] **1.5** Модуль генерации Excel
  - Новый `.xlsx` за каждый batch (openpyxl)
  - Формат столбцов точно как в таблице выше
  - Имя файла: `Rechnungen_YYYYMMDD_HHMMSS.xlsx`
  - Сохранить в папку года (`RG {YEAR} Ersatzteile RepRG/`)
  - Result: Excel-файл готов к отправке

- [ ] **1.6** Модуль файлового менеджмента
  - Успешные PDF → `checked_*` в папку года
  - Неуспешные PDF → `manual/`
  - Блокировка папки на время обработки (no concurrent runs)
  - Result: файлы разложены

- [ ] **1.7** Оркестратор пайплайна
  - Параллельная обработка: `asyncio.gather()`, до 5 PDF одновременно
  - Прогресс callback для Telegram
  - Graceful degradation: API down → файлы не тронуты, сообщение пользователю
  - Cost guard: лимит $1/день, стоп при превышении
  - Result: всё собрано в один `process_batch()` вызов

---

## Phase 2 — Telegram Bot

- [ ] **2.1** Скелет бота (PTB)
  - `/start` → приветствие + inline keyboard
  - Whitelist check (из `.env`)
  - `/health` → uptime, DB connected, OpenAI reachable
  - `/cost` → "Сегодня: $0.34 / 47 счетов"
  - Result: бот отвечает авторизованным пользователям

- [ ] **2.2** Кнопка "Обработать счета"
  - Сканировать `EingangsRG/` → показать: "Найдено 12 PDF. Обработать?"
  - Кнопка подтверждения перед стартом
  - Блокировка: если обработка уже идёт → "Подождите, идёт обработка"
  - Result: пользователь контролирует запуск

- [ ] **2.3** Прогресс обработки
  - Одно сообщение, обновляется через `edit_message_text()`
  - Формат: `"📄 3/15 | ✓ GR-OO501 | MAN | 143.13€ | Reparatur"`
  - Не спамит отдельными сообщениями
  - Result: real-time прогресс

- [ ] **2.4** Отправка результата
  - Excel файл как документ в Telegram
  - Caption: "✓ 10 OK | ⚠ 1 review | ✗ 1 manual | $0.08"
  - Кнопка "Показать детали" → развёрнутая таблица
  - Result: пользователь получает файл в чате

- [ ] **2.5** Управление `manual/` папкой
  - Кнопка "Manual (3)" → список файлов
  - "Повторить" → переобработать файл
  - "Пропустить" → пометить как обработанный вручную
  - Result: удобное управление проблемными файлами

- [ ] **2.6** Автозапуск бота
  - `run_repair_bot.cmd` + `run_silent.vbs`
  - Task Scheduler entry: `Repair Invoice Bot`
  - Запуск при входе в систему
  - Result: бот работает 24/7

---

## Phase 3 — Качество и Production

- [ ] **3.1** Тюнинг промпта на реальных данных
  - Тест на 20+ реальных счетов (разные поставщики)
  - Измерить accuracy по каждому полю
  - Добавить few-shot примеры проблемных кейсов
  - Цель: >90% accuracy
  - Result: надёжное извлечение

- [ ] **3.2** Версионирование промптов
  - Промпты в `prompts/v1.txt`, `prompts/v2.txt`
  - Логировать `prompt_version` с каждым вызовом
  - Сравнивать accuracy между версиями
  - Result: контролируемое улучшение промпта

- [ ] **3.3** Audit trail
  - JSON лог каждого AI вызова: input hash + response + result
  - Хранение 90 дней
  - При ошибке — можно восстановить что AI "увидел"
  - Result: полная прослеживаемость

- [ ] **3.4** Unit тесты
  - Тест извлечения текста (pdfplumber mock)
  - Тест парсинга AI ответа
  - Тест валидации (все 4 уровня)
  - Тест генерации Excel
  - Mock AI вызовов для тестов
  - Result: надёжное тестовое покрытие

- [ ] **3.5** Health monitoring
  - Self-test раз в час: ping DB + ping OpenAI
  - Alert в Telegram при проблеме
  - `/health` команда в боте
  - Result: проблемы видны сразу

---

## Phase 4 — Продвинутые функции (будущее)

- [ ] **4.1** Дубликаты через PostgreSQL
  - Проверка invoice_nr перед INSERT
  - Warning в Telegram если дубликат
  - Опция: пропустить или перезаписать
  - Result: нет случайных дубликатов

- [ ] **4.2** Статистика и отчёты
  - `/stats` → месячная сводка: по поставщику, по категории, по машине
  - Стоимость на машину
  - Export из Telegram
  - Result: управленческая аналитика

- [ ] **4.3** Обучение на исправлениях
  - Когда пользователь исправляет manual/ файл → сохранить коррекцию
  - Использовать как few-shot пример для похожих счетов
  - Result: AI улучшается со временем

- [ ] **4.4** Дописывать в master Excel (опционально)
  - Кнопка "Добавить в Repair_2026.xlsx"
  - Merge с существующими данными
  - Result: единый файл для бухгалтерии

---

## Risk Matrix

| Риск | Вероятность | Влияние | Защита |
|------|------------|---------|--------|
| AI извлёк неправильную цену | Средняя | **Критическое** | 4-уровневая валидация + confidence + human review |
| Скан нечитаемый | Низкая | Среднее | Цепочка: mini → 4o → manual |
| OpenAI API недоступен | Низкая | Среднее | Retry 3x + graceful degradation (файлы не тронуты) |
| Перерасход бюджета | Низкая | Низкое | Cost guard $1/день, логирование токенов |
| Мульти-truck разбит неправильно | Средняя | Среднее | Few-shot примеры, тест на 20+ реальных кейсах |
| Gutschrift не распознан | Низкая | Высокое | Правило в промпте + валидация (отрицательная цена) |
| Дубликат записан | Средняя | Среднее | UNIQUE constraint + warn в Telegram |
| Двойное нажатие кнопки | Низкая | Низкое | File lock блокирует параллельный запуск |
| БД отключилась mid-batch | Низкая | Среднее | Транзакция на счёт, необработанные файлы остаются |

---

## Порядок выполнения

```
Phase 0: Инфраструктура (0.1 → 0.2 → 0.3 → 0.4 → 0.5)
Phase 1: Core Pipeline  (1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7)
Phase 2: Telegram Bot    (2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6)
Phase 3: Качество        (3.1 → 3.2 → 3.3 → 3.4 → 3.5)
Phase 4: Продвинутое     (после стабильной работы Phases 0-3)
```

**MVP (Phases 0-2):** бот работает, AI извлекает, Excel генерируется, файл в Telegram
**Production (+ Phase 3):** confidence scoring, тесты, cost tracking, audit trail
