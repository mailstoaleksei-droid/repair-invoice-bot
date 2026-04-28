# Project Checklist — 2026-03-27

> Рабочий чек-лист по текущему состоянию проекта, а не по целевой AI-архитектуре.

## A. В работе

- [ ] Разбор ошибок текущего батча по поставщикам и полям извлечения
- [ ] Переход от общего аудита к итеративной доработке на реальных текущих счетах
- [ ] Проверка первого полного AI-отчета пользователем и фиксация ошибок по строкам/поставщикам
- [x] Исправление счетчика `AI Assisted`, который теперь считает уникальные счета, а не повторные AI-вызовы
- [x] Добавлен недельный автозапуск проверки `EingangsRG` по понедельникам в 09:00 через Windows Scheduled Task
- [x] Зафиксирована цель 95%+ и правила работы с `Review Queue` для ручных ошибок

## B. Следующий шаг

- [ ] Проверить отчет `processing_report_20260327_210432.xlsx`
- [ ] Отметить строки, где неверны `Seller`, `Buyer`, `Truck`, `Name`, `Total Price`, `Kategorie`
- [ ] Отдельно проверить multi-truck счета, где должна быть одна строка на одну машину
- [ ] Разобрать 3 необработанных файла и понять, нужен ли OCR или отдельный parser
- [ ] После замечаний пользователя править алгоритм по одному поставщику за итерацию и повторять прогон
- [ ] Добавлять каждую подтвержденную ручную ошибку в checklist/GitHub issue, чтобы она стала regression case
- [ ] Проверить, что `.env` содержит Telegram credentials для автоматической отправки еженедельного отчета в `PDF Processor Bot`

## C. Последний результат прогона

- Дата прогона: `2026-03-27 21:04:32`
- Режим: `report_only`
- Всего PDF в батче: `542`
- Строк в листе `Invoice Report`: `940`
- Извлечено: `539`
- Дубликаты: `0`
- Не обработано: `3`
- AI участвовал в извлечении: `519` счетов
- Только Python без AI: `20` счетов
- Статусы по отчету:
- `extracted`: `539`
- `empty_pdf`: `1`
- `processing_error`: `2`
- Наиболее частые missing fields в извлеченных счетах:
- `name`: `29`
- `truck`: `16`
- `total_price`: `7`
- `buyer`: `1`
- Необработанные файлы:
- `2352 - VHV 238,18.pdf`
- `error_1927 - Vovo Pinneberg 0057804665.pdf`
- `error_1928 - Volvo Pinneberg 0057804649.pdf`
- Отчет: `processing_report_20260327_210432.xlsx`

## D. Текущие блокеры

- [ ] Нет OCR fallback для scan-based PDF
- [x] Убрана критическая зависимость от hardcoded путей проекта; подготовлен перенос в `AI\Repair Eingang Bot`
- [ ] В коде остаются поврежденные строки кодировки
- [ ] Полное разбиение счетов с несколькими машинами на отдельные строки еще не реализовано в supplier-specific extractors
- [ ] Локальная папка `PDF_Processor` еще не подключена к git-репозиторию
- [x] Telegram token и chat id вынесены в `.env`
- [ ] `file_monitor.py` отсутствует в рабочей папке
- [ ] Нет автотестов на поставщиков и регрессии
- [ ] Счетчик `AI Assisted` в консольной/Telegram-сводке завышен, потому что считает повторные AI-вызовы на один счет
- [ ] Нужно вручную подтвердить качество AI-извлечения в первом полном отчете, прежде чем включать рабочий режим с раскладкой файлов

## 0. Уже выполнено

- [x] `telegram_bot_v4_updated.py` переведен на запуск `process_pdf_v7_3.py`
- [x] Добавлен режим проверки `report_only` без перемещения файлов по папкам
- [x] Добавлено сохранение отдельного Excel-отчета по каждому прогону в `PDF_Processor/reports`
- [x] Исправлена ошибка проверки дублей по Excel на коротких строках
- [x] Подтверждено, что AI/OpenAI-обработка используется в текущем рабочем коде через fallback pipeline
- [x] Подтверждено, что `file_monitor.py` в рабочей папке отсутствует и автомониторинг локально не работает
- [x] Возвращены файлы `checked_*.pdf` из `RG 2025 Ersatyteile RepRG` и `RG 2026 Ersatyteile RepRG` обратно в `EingangsRG` без префикса `checked_`
- [x] Отключены Telegram-сообщения по каждому счету
- [x] Добавлена итоговая Telegram-сводка с агрегированными причинами ошибок и частичной обработки
- [x] Добавлены структурированные причины и missing fields в per-run Excel-отчет
- [x] Исправлен парсинг итоговой статистики в Telegram-боте под текущий формат вывода
- [x] Остановлен старый зависший экземпляр Telegram-бота, который отправлял устаревшие сообщения
- [x] Добавлены локальные запускатели `start_bot.cmd` и `start_processing_report.cmd`
- [x] Формат `Invoice Report` приведен к колонкам A-K: `Yaer`, `Month`, `Week`, `Date Invoice`, `Truck`, `Name`, `Total Price`, `Invoice`, `Seller`, `Buyer`, `Kategorie`
- [x] Запись в master Excel приведена к той же схеме A-K
- [x] В workbook отчета сохранен отдельный лист `Validation` для контроля ошибок и missing fields
- [x] Добавлен справочник-ориентир по номерам машин `TRUCK_REFERENCE_2026-03-27.md`
- [x] Добавлен модуль `truck_reference.py` для нормализации и fallback-поиска номеров машин
- [x] Добавлен справочник-ориентир по фирмам `SUPPLIER_REFERENCE_2026-03-27.md`
- [x] Добавлен модуль `supplier_reference.py` для fallback-распознавания фирм по тексту счета
- [x] Добавлен `ai_invoice_extractor.py` для OpenAI-based invoice fallback
- [x] Добавлен `.env.example` с настройками OpenAI
- [x] Создан локальный `.env` шаблон для вставки `OPENAI_API_KEY`
- [x] Установлен Python-клиент `openai`
- [x] AI fallback подключен в pipeline для `pdf_read_error`, `empty_pdf`, `no_data` и partial extraction
- [x] `OPENAI_API_KEY` добавлен в локальный `.env`
- [x] Выполнен первый полный прогон батча `542` PDF с рабочим OpenAI fallback
- [x] Получен новый отчет `processing_report_20260327_210432.xlsx`
- [x] Подтверждено, что AI больше не падает на `Connection error` при запуске вне sandbox
- [x] Подтвержден рабочий AI-прогон `2026-04-28`: `107` обработано, `1` не обработан, AI реально участвовал в pipeline
- [x] Добавлен отдельный лист `Review Queue` в Excel-отчет для ручной проверки проблемных или частично обработанных счетов
- [x] Добавлен helper `sync_project_state.ps1` для сохранения чеклиста и git sync
- [x] Добавлен `weekly_process_invoices.ps1` для автоматической еженедельной AI-обработки PDF из `EingangsRG`
- [x] Добавлен `install_weekly_task.cmd` для установки Windows Scheduled Task на понедельник 09:00
- [x] Добавлен `install_weekly_task.ps1`, чтобы установка Scheduled Task работала с пробелами в OneDrive/SharePoint пути
- [x] Добавлен аудит папки `AI` от `2026-04-28` с перечнем дублей, GitHub/checklist статуса и рекомендациями

## 1. Критическая стабилизация

- [ ] Подключить локальную папку `PDF_Processor` к git-репозиторию `repair-invoice-bot`
- [x] Исправить `telegram_bot_v4_updated.py`, чтобы он запускал `process_pdf_v7_3.py`, а не `process_pdf_v7.py`
- [x] Проверить и обновить пути `EXCEL_FILE` и `PROCESSED_FOLDER` на актуальный 2026 год
- [x] Убрать hardcoded Telegram token и chat id из кода, вынести в `.env`
- [ ] Проверить кодировку файлов Python и сохранить их в UTF-8 без поврежденных строк

## 2. Повышение качества извлечения

- [ ] Разобрать ошибки NETTO/BRUTTO по поставщикам
- [ ] Создать таблицу правил: какой supplier должен давать NETTO, какой BRUTTO
- [ ] Добавить тестовые PDF-примеры по каждому проблемному поставщику
- [ ] Починить определение поставщика для новых и нестандартных счетов
- [ ] Проверить несовпадения между `identify_supplier()` и `extract_data_by_supplier()`
- [ ] Отдельно проверить кейсы Gutschrift и отрицательных сумм

## 3. OCR и сканы

- [ ] Добавить OCR fallback для PDF-сканов
- [ ] Определять image-only PDF автоматически
- [x] Сохранять причину перевода в `manual` более структурированно
- [ ] Сделать отдельный список поставщиков и шаблонов, которые чаще всего уходят в manual

## 4. Telegram и операционная работа

- [ ] Проверить, что бот запускается без ручных правок путей
- [ ] Вернуть или заново реализовать `file_monitor.py`
- [x] Проверить команду статуса и корректность счетчиков `processed/manual`
- [ ] Сделать отдельное уведомление о критических ошибках конфигурации

## 5. Тесты и контроль качества

- [ ] Создать папку `tests/`
- [ ] Добавить smoke test на запуск обработчика
- [ ] Добавить unit tests на 5-10 ключевых supplier extractors
- [ ] Добавить regression tests на ошибки с NETTO/BRUTTO
- [ ] Добавить fixture-набор PDF или текстовых дампов счетов

## 6. Архитектура

- [ ] Разделить монолитный `process_pdf_v7_3.py` на модули:
- [ ] `config.py`
- [ ] `suppliers.py`
- [ ] `extractors/`
- [ ] `excel_writer.py`
- [ ] `pipeline.py`
- [ ] `telegram_runner.py`
- [ ] Вынести supplier patterns и regex в конфигурацию
- [ ] Добавить единый формат результата обработки счета

## 7. Метрики и KPI

- [ ] Вести журнал по batch-результатам с датой, total, processed, manual, duplicates
- [ ] Считать KPI автоматизации по месяцам
- [ ] Считать top suppliers по ошибкам
- [ ] Считать top reasons для ручной обработки
- [ ] Установить цель этапа 1: не 90%, а стабильные 60-70% с понятным контролем качества
- [ ] Установить цель этапа 2: 80%+ после OCR и supplier coverage
- [ ] Установить цель этапа 3: 90%+ только после тестов и fallback-логики

## 8. GitHub и документация

- [ ] Добавить актуальный `README.md` с описанием реальной архитектуры
- [ ] Добавить `SETUP.md` для локального запуска
- [ ] Добавить `OPERATIONS.md` для работы с папками, логами и Telegram-ботом
- [ ] Добавить `CHANGELOG.md`
- [ ] Синхронизировать локальную рабочую папку и GitHub-репозиторий

## 9. Weekly automation and 95% target

- [x] Weekly Monday 09:00 automation script exists
- [x] Weekly automation excludes `manual`
- [x] Weekly automation forces OpenAI-enabled processing
- [x] Weekly automation uses current final Telegram summary when Telegram credentials are configured
- [ ] Confirm Windows Scheduled Task is installed on the production PC
- [ ] Add KPI history file or database table for weekly `total`, `processed`, `partial`, `manual`, `errors`, `ai_assisted`
- [ ] Convert every manually corrected invoice from `Review Queue` into a supplier rule, OCR case, truck mapping, or regression test
- [ ] Reach and sustain `>=95%` automatic processing for 4 consecutive weekly batches
