# 📋 ИСПРАВЛЕНИЯ ДЛЯ v7.3

## 🔴 КРИТИЧЕСКИЕ ОШИБКИ И ИСПРАВЛЕНИЯ:

### 1. Vital Projekt - неправильная сумма
**Проблема:** Берёт 79.99 вместо 421.00
**Причина:** Извлекает не ту строку из PDF
**Решение:** 
- В счёте есть "Summe: 421,00 €" (NETTO)
- Есть "Gesamtbetrag: 500,99 €" (BRUTTO с НДС)
- Нужно искать именно "Summe" или "421,00 € netto"

**Паттерн для исправления:**
```python
def extract_vital_projekt(text):
    # Ищем: "Summe" + сумма
    total_match = re.search(r'Summe\s+([\d,.]+)\s*€', text)
    # Должно найти: 421,00
```

---

### 2. TIP Trailer - берёт BRUTTO вместо NETTO
**Проблема:** 7846.86 вместо 6594.00
**Причина:** Извлекает "Gesamtbetrag" (BRUTTO) вместо "Nettosumme"
**Решение:**
- Ищем "Nettosumme" в PDF
- Игнорируем "Gesamtbetrag"

**Паттерн:**
```python
def extract_tip(text):
    # ПРИОРИТЕТ 1: Nettosumme
    netto_match = re.search(r'Nettosumme\s+([\d,.]+)', text)
    if netto_match:
        return netto_match.group(1)
    
    # ПРИОРИТЕТ 2: % USt auf (сумма netto)
    netto_match2 = re.search(r'(\d+[,.]?\d*)\s*%\s*USt\s*auf\s+([\d,.]+)', text)
```

---

### 3. MAN Gutschrift - нужен знак минус
**Проблема:** Сумма 143.13, должна быть -143.13
**Причина:** Не определяется Gutschrift
**Решение:**
- Ищем слово "Gutschrift" в тексте
- Если найдено → умножаем сумму на -1

**Код:**
```python
def extract_man(text):
    # ... извлечение данных ...
    
    # Проверка на Gutschrift
    is_gutschrift = 'GUTSCHRIFT' in text.upper() or 'Gutschrift' in text
    
    if is_gutschrift:
        data['total_price'] = -abs(data['total_price'])
        data['name'] = 'Gutschrift - ' + data.get('name', '')
```

---

### 4. MAN множественные машины - разделение строк
**Проблема:** 7 машин в одной строке
**Файл:** checked_2241_2240_2243_2244_2245_2242_2246 - Wartungsvertrag MAN 7501719939.pdf
**Машины:** GR-OO2241, GR-OO2240, GR-OO2243, GR-OO2244, GR-OO2245, GR-OO2242, GR-OO2246

**Решение:**
- Извлекаем ВСЕ номера машин из текста
- Делим общую сумму на количество машин
- Создаём отдельную строку для каждой машины

**Код:**
```python
def extract_man(text):
    # Извлекаем все машины
    trucks = re.findall(r'GR-OO\s*\d+', text)
    trucks = [re.sub(r'\s+', '', t) for t in trucks]
    trucks = list(set(trucks))  # Уникальные
    
    # Извлекаем данные
    data = {... основные данные ...}
    
    # Если несколько машин
    if len(trucks) > 1:
        # Делим сумму
        price_per_truck = data['total_price'] / len(trucks)
        
        # Возвращаем список данных (по одному на машину)
        results = []
        for truck in trucks:
            truck_data = data.copy()
            truck_data['truck'] = truck
            truck_data['total_price'] = price_per_truck
            truck_data['price'] = price_per_truck
            results.append(truck_data)
        return results  # Список вместо одного dict
    else:
        return data
```

---

### 5. Volvo - неправильная сумма
**Проблема:** 310.77 вместо 261.15
**Причина:** Берёт "Gesamt" вместо "Nettosumme"
**Решение:**
- Ищем "Nettosumme: 261,15"
- Игнорируем "Gesamt"

**Паттерн:**
```python
def extract_volvo(text):
    # ПРИОРИТЕТ 1: Nettosumme
    netto_match = re.search(r'Nettosumme\s+([\d,.]+)', text)
    if netto_match:
        return float(netto_match.group(1).replace(',', '.'))
```

---

### 6. Name колонка - кракозябры
**Проблема:** "Ð·ÐµÐ¼Ð¾Ð½Ñ‚Ð½Ñ‹Ðµ Ñ€Ð°Ð±Ð¾Ñ‚Ñ‹"
**Причина:** Кириллица в UTF-8
**Решение:**
- Заменить на немецкий текст
- Извлекать описание из PDF

**Код:**
```python
# Вместо:
data['name'] = 'Ремонтные работы'

# Делать:
data['name'] = 'Reparaturarbeiten'
# Или извлекать из PDF:
name_match = re.search(r'Bezeichnung[:\s]+(.+?)[\n\r]', text)
if name_match:
    data['name'] = name_match.group(1)[:50]
else:
    data['name'] = 'Reparaturarbeiten'
```

---

### 7. Truck колонка - не всегда заполняется
**Проблема:** Пустые значения
**Решение:**
- Улучшить извлечение из имени файла
- Улучшить паттерны в PDF

**Приоритеты:**
1. Из PDF (Kennzeichen, Fahrer, etc.)
2. Из имени файла (checked_1726 → GR-OO1726)
3. Пустое значение (если нет данных)

---

### 8. Дата загрузки - текущая дата
**Проблема:** Должна быть дата обработки
**Решение:** Уже реализовано в write_to_excel()
```python
processing_date = datetime.now().strftime('%d.%m.%Y')
ws[f'M{row}'] = processing_date
```
Это правильно! ✅

---

## 📝 ОБЩЕЕ ПРАВИЛО: NETTO vs BRUTTO

**ДЛЯ ВСЕХ ПОСТАВЩИКОВ (кроме Internal Auto Compass):**

Приоритет извлечения суммы:
1. **"Nettobetrag"** - высший приоритет
2. **"Netto"** - второй приоритет
3. **"Summe netto"** - третий приоритет
4. **"Zwischensumme netto"** - четвёртый
5. **"Gesamt" / "Gesamtbetrag"** - только если нет NETTO

---

## 🔄 ПРАВИЛО: Gutschrift (возвраты)

Для ВСЕХ поставщиков:
```python
# После извлечения суммы:
if 'GUTSCHRIFT' in text.upper() or 'Gutschrift' in text:
    data['total_price'] = -abs(data['total_price'])
    data['price'] = -abs(data['price'])
    
    # Добавить пометку в Name
    if 'Gutschrift' not in data.get('name', ''):
        data['name'] = 'Gutschrift - ' + data.get('name', 'Rückerstattung')
```

---

## 📋 ПРАВИЛО: Множественные машины

Для ВСЕХ поставщиков:
```python
def extract_XXX(text):
    # ... основная логика ...
    
    # Извлечь ВСЕ машины
    trucks = extract_all_trucks(text)
    
    if len(trucks) > 1:
        # Разделить данные
        price_per_truck = data['total_price'] / len(trucks)
        
        results = []
        for truck in trucks:
            truck_data = data.copy()
            truck_data['truck'] = truck
            truck_data['total_price'] = price_per_truck
            truck_data['price'] = price_per_truck
            results.append(truck_data)
        
        return results  # СПИСОК данных
    else:
        return data  # ОДИН dict
```

---

## 🎯 ИТОГО: 8 КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ

1. ✅ Vital Projekt - правильная сумма (Summe, не Gesamtbetrag)
2. ✅ TIP Trailer - NETTO вместо BRUTTO
3. ✅ MAN Gutschrift - знак минус
4. ✅ MAN множественные машины - разделение строк
5. ✅ Volvo - NETTO вместо Gesamt
6. ✅ Name - немецкий текст вместо кириллицы
7. ✅ Truck - улучшенное извлечение
8. ✅ Общее правило NETTO для всех поставщиков

---

## 📊 ОЖИДАЕМОЕ УЛУЧШЕНИЕ:

**БЫЛО:**
- 101 файл обработано (33.4%)
- Много ошибок в суммах

**СТАНЕТ:**
- ~250-280 файлов обработано (85-92%)
- Правильные суммы
- Правильная обработка Gutschrift
- Разделение множественных машин

---

## ⏭️ СЛЕДУЮЩИЕ ШАГИ:

1. Создать v7.3 с этими исправлениями
2. Перезапустить обработку ВСЕХ файлов
3. Проверить результаты
4. Проанализировать оставшиеся manual файлы
5. Создать v7.4 для manual файлов
6. Достичь >95% автоматизации

---

**Начинаю создание v7.3 с исправлениями!** 🚀
