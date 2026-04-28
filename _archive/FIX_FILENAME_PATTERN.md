# 🔧 ИСПРАВЛЕНИЕ: Распознавание файлов без префикса "checked_"

## ❌ ПРОБЛЕМА

Файлы с именами типа:
- `1726 - AC Intern 700293.pdf`
- `771 - TIP Trailer.pdf`

НЕ обрабатывались, так как система ожидала формат:
- `checked_1726 - AC Intern.pdf`

---

## ✅ РЕШЕНИЕ

Обновлена функция `extract_truck_from_filename()` для поддержки обоих форматов.

---

## 📥 УСТАНОВКА ИСПРАВЛЕНИЯ

### Вариант A: Скачать исправленный файл (РЕКОМЕНДУЮ)

1. Скачайте обновленный файл:
   - [process_pdf_v3.py (исправленный)](computer:///mnt/user-data/outputs/process_pdf_v3.py)

2. Замените им старый файл в `PDF_Processor`

3. Готово! ✅

---

### Вариант B: Ручное исправление

Откройте `process_pdf_v3.py` и найдите функцию `extract_truck_from_filename()` (около строки 50).

**ЗАМЕНИТЕ весь блок с:**
```python
def extract_truck_from_filename(filename):
    """Извлечь номер машины из имени файла"""
    patterns = [
        r'checked_(\d+)',
    ]
    ...
```

**НА:**
```python
def extract_truck_from_filename(filename):
    """Извлечь номер машины из имени файла"""
    
    # Паттерн 1: checked_XXX (основной формат)
    patterns = [
        r'checked_(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            number = match.group(1)
            if len(number) <= 2:
                return f"GR-OO{number.zfill(2)}"
            else:
                return f"GR-OO{number}"
    
    # Паттерн 2: XXXX - Поставщик (новый формат)
    # Примеры: "1726 - AC Intern.pdf", "771 - TIP.pdf"
    simple_number_pattern = r'^(\d{2,4})\s*[-–]\s*'
    match = re.match(simple_number_pattern, filename)
    if match:
        number = match.group(1)
        if len(number) <= 2:
            return f"GR-OO{number.zfill(2)}"
        elif len(number) == 3:
            return f"GR-OO{number}"
        else:  # 4 digits
            return f"GR-OO{number}"
    
    # Паттерн 3: Прямые указания (GR-OO, HH-AG, etc.)
    direct_patterns = [
        (r'GR[- ]?OO(\d+)', 'GR-OO'),
        (r'GR[- ]?(\d+)', 'GR-'),
        (r'WJQY4010', 'WJQY4010'),
        (r'OHAMX771', 'OHAMX771'),
        (r'HH[- ]?AG(\d+)', 'HH-AG'),
        (r'DE[- ]?FN(\d+)', 'DE-FN'),
    ]
    
    for pattern, prefix in direct_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            if prefix in ['WJQY4010', 'OHAMX771']:
                return prefix
            number = match.group(1) if match.groups() else ''
            return f"{prefix}{number.zfill(3)}"
    
    return None
```

Сохраните файл.

---

## 🧪 ПОВТОРНОЕ ТЕСТИРОВАНИЕ

### После установки исправления:

1. **Перезапустить бота:**
   ```bash
   Ctrl+C
   python telegram_bot_v3.py
   ```

2. **Проверить что файлы всё еще в папке:**
   ```
   EingangsRG/
   ├── 1726 - AC Intern 700293.pdf
   └── 1726 - Scania SCHWL53718.pdf
   ```

3. **В Telegram нажать:** `🔄 Обработать PDF`

4. **Ожидаемый результат:**
   ```
   ⏳ Обработка начата
   📄 Файл: 1726 - AC Intern 700293.pdf
   
   ✅ Обработан успешно!
   📄 Файл: 1726 - AC Intern 700293.pdf
   🏢 Поставщик: Auto Compass GmbH
   🔢 Счет: 700293
   🚛 Машина: GR-OO1726  ← ✅ НОМЕР ОПРЕДЕЛЕН!
   ...
   
   📊 ОБРАБОТКА ЗАВЕРШЕНА
   ✅ Успешно: 2  ← ✅ ОБА ФАЙЛА!
   ```

---

## 📋 ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ

После исправления система понимает:

### Формат 1: С префиксом (оригинал)
- `checked_1726 - AC Intern.pdf` → `GR-OO1726`
- `checked_15 - K&L.pdf` → `GR-OO15`

### Формат 2: Без префикса (НОВЫЙ)
- `1726 - AC Intern.pdf` → `GR-OO1726`
- `15 - K&L.pdf` → `GR-OO15`
- `771 - TIP Trailer.pdf` → `GR-OO771`

### Формат 3: Прямое указание
- `GR-OO1726 - Invoice.pdf` → `GR-OO1726`
- `HH-AG928 - Document.pdf` → `HH-AG928`

---

## ✅ CHECKLIST

- [ ] Скачал исправленный `process_pdf_v3.py`
- [ ] Заменил файл в `PDF_Processor`
- [ ] Перезапустил бота
- [ ] Проверил что файлы в `EingangsRG`
- [ ] Нажал "🔄 Обработать PDF"
- [ ] Получил успешные уведомления
- [ ] Файлы переместились в `processed/`

---

## 📸 ЧТО ПОКАЗАТЬ

После исправления покажите:
1. PowerShell - успешный запуск
2. Telegram - уведомления с номерами машин
3. Telegram - "✅ Успешно: 2"

---

**Готовы повторить тест?**

Напишите **"ИСПРАВИЛ"** когда замените файл и перезапустите бота! 🚀
