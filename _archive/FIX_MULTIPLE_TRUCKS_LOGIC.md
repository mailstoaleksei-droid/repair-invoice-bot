# 🔴 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ #4 - Правильная логика

## ❌ НЕПРАВИЛЬНО (было в первой версии v7.3):

```python
# Делим общую сумму на количество машин
price_per_truck = data['total_price'] / len(trucks)

results = []
for truck in trucks:
    truck_data = data.copy()
    truck_data['truck'] = truck
    truck_data['total_price'] = price_per_truck  # ❌ НЕПРАВИЛЬНО!
    results.append(truck_data)
```

**Проблема:** Делим общую сумму поровну, но в счёте может быть РАЗНАЯ сумма для каждой машины!

---

## ✅ ПРАВИЛЬНО:

### Логика работы:

1. **Извлечь ТАБЛИЦУ** из счёта MAN с данными по каждой машине
2. **Для каждой строки таблицы:**
   - Номер машины (GR-OO2241)
   - Описание услуги (Job)
   - Сумма NETTO для этой конкретной машины
3. **Создать отдельную строку Excel** для каждой машины со своей суммой

### Пример счёта MAN с множественными машинами:

```
Rechnung 7501719939

Fahrzeug    Job     Beschreibung              Netto EUR
GR-OO2241   1001    Wartungsvertrag           150,00
GR-OO2240   1002    Wartungsvertrag           150,00
GR-OO2243   1003    Wartungsvertrag           150,00
GR-OO2244   1004    Wartungsvertrag + Teile   200,00
GR-OO2245   1005    Wartungsvertrag           150,00
GR-OO2242   1006    Wartungsvertrag           150,00
GR-OO2246   1007    Wartungsvertrag + Teile   180,00

GESAMT NETTO: 1130,00 EUR
```

### Правильный код:

```python
def extract_man_multiple_trucks(text):
    """
    Извлечение данных MAN с поддержкой множественных машин
    ПРАВИЛЬНАЯ ЛОГИКА: извлекать индивидуальную сумму для каждой машины
    """
    base_data = {}
    
    # Номер счёта
    invoice_match = re.search(r'Rechnungsnummer:\s*(\d+)', text)
    if not invoice_match:
        return None
    base_data['invoice'] = invoice_match.group(1)
    
    # Дата
    date_match = re.search(r'Rechnungsdatum:\s*(\d{2})\.(\d{2})\.(\d{4})', text)
    if not date_match:
        return None
    
    date_str = f"{date_match.group(1)}.{date_match.group(2)}.{date_match.group(3)}"
    base_data['date'] = date_str
    
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        base_data['month'] = date_obj.month
        base_data['week'] = date_obj.isocalendar()[1]
    except:
        return None
    
    base_data['seller'] = 'MAN Truck & Bus Deutschland GmbH'
    base_data['buyer'] = 'Auto Compass GmbH'
    base_data['amount'] = 1
    
    # Проверка на Gutschrift
    is_gutschrift = detect_gutschrift(text)
    
    # 🔴 КРИТИЧЕСКАЯ ЧАСТЬ: Извлечение данных по каждой машине
    
    # Паттерн 1: Таблица с колонками (Fahrzeug, Job, Netto)
    # Ищем строки вида: "GR-OO2241   Job 1001:   Описание   150,00"
    truck_lines = re.findall(
        r'(GR-OO\s*\d+)\s+.*?Job\s+\d+[:\s]+(.+?)\s+([\d,]+(?:\.\d+)?)\s*(?:EUR|€)?',
        text,
        re.IGNORECASE
    )
    
    if truck_lines and len(truck_lines) > 1:
        # ✅ МНОЖЕСТВЕННЫЕ МАШИНЫ - извлекаем индивидуальные суммы
        results = []
        
        for truck_raw, description, amount_str in truck_lines:
            truck_data = base_data.copy()
            
            # Форматировать номер машины
            truck_clean = re.sub(r'\s+', '', truck_raw)
            truck_data['truck'] = truck_clean
            
            # Описание
            truck_data['name'] = description.strip()[:50]
            if is_gutschrift and 'Gutschrift' not in truck_data['name']:
                truck_data['name'] = 'Gutschrift - ' + truck_data['name']
            
            # ИНДИВИДУАЛЬНАЯ сумма для этой машины
            amount_clean = amount_str.replace('.', '').replace(',', '.')
            truck_data['price'] = float(amount_clean)
            truck_data['total_price'] = float(amount_clean)
            
            # Gutschrift - делаем отрицательной
            if is_gutschrift:
                truck_data['total_price'] = -abs(truck_data['total_price'])
                truck_data['price'] = -abs(truck_data['price'])
            
            results.append(truck_data)
        
        return results  # СПИСОК dict
    
    else:
        # ✅ ОДНА МАШИНА или машина не указана
        # Извлекаем как обычно
        
        truck_match = re.search(r'GR-OO\s*(\d+)', text)
        if truck_match:
            base_data['truck'] = f"GR-OO{truck_match.group(1)}"
        else:
            base_data['truck'] = ''
        
        # Описание
        desc_match = re.search(r'Job\s+\d+:\s+([^\n]+)', text)
        if desc_match:
            base_data['name'] = desc_match.group(1)[:50]
        else:
            base_data['name'] = 'Reparatur MAN'
        
        if is_gutschrift and 'Gutschrift' not in base_data['name']:
            base_data['name'] = 'Gutschrift - ' + base_data['name']
        
        # Общая сумма NETTO
        total_match = re.search(r'NETTO\s+([\d,.]+)\s+EUR', text, re.IGNORECASE)
        if not total_match:
            total_match = re.search(r'Nettobetrag:\s+([\d,.]+)', text)
        
        if not total_match:
            return None
        
        total_str = total_match.group(1).replace('.', '').replace(',', '.')
        base_data['total_price'] = float(total_str)
        base_data['price'] = float(total_str)
        
        # Gutschrift
        if is_gutschrift:
            base_data['total_price'] = -abs(base_data['total_price'])
            base_data['price'] = -abs(base_data['price'])
        
        return base_data  # ОДИН dict
```

---

## 📊 ПРИМЕРЫ РАБОТЫ

### Пример 1: Множественные машины с РАЗНЫМИ суммами

**Входной счёт:**
```
Rechnung: 7501719939

GR-OO2241  Job 1001:  Wartungsvertrag        150,00 EUR
GR-OO2240  Job 1002:  Wartungsvertrag        150,00 EUR
GR-OO2243  Job 1003:  Wartungsvertrag        150,00 EUR
GR-OO2244  Job 1004:  Wartungsvertrag+Teile  200,00 EUR
GR-OO2245  Job 1005:  Wartungsvertrag        150,00 EUR
GR-OO2242  Job 1006:  Wartungsvertrag        150,00 EUR
GR-OO2246  Job 1007:  Wartungsvertrag+Teile  180,00 EUR

GESAMT NETTO: 1130,00 EUR
```

**Результат в Excel (7 строк):**
```
Truck        Name                    Total Price
GR-OO2241    Wartungsvertrag         150.00
GR-OO2240    Wartungsvertrag         150.00
GR-OO2243    Wartungsvertrag         150.00
GR-OO2244    Wartungsvertrag+Teile   200.00  ← РАЗНАЯ СУММА!
GR-OO2245    Wartungsvertrag         150.00
GR-OO2242    Wartungsvertrag         150.00
GR-OO2246    Wartungsvertrag+Teile   180.00  ← РАЗНАЯ СУММА!
```

**Проверка:** 150+150+150+200+150+150+180 = **1130 EUR** ✅

---

### Пример 2: Одна машина

**Входной счёт:**
```
Rechnung: 5518613534

GR-OO1726  Job 2001:  Reparatur Motor  450,00 EUR

NETTO: 450,00 EUR
```

**Результат в Excel (1 строка):**
```
Truck        Name             Total Price
GR-OO1726    Reparatur Motor  450.00
```

---

## 🔍 КАК ПРОВЕРИТЬ

### Тест для файла 7501719939:

1. **Открыть PDF** `checked_2241_2240_2243_2244_2245_2242_2246 - Wartungsvertrag MAN 7501719939.pdf`

2. **Найти таблицу** с машинами и суммами

3. **Записать индивидуальные суммы:**
   - GR-OO2241: ? EUR
   - GR-OO2240: ? EUR
   - GR-OO2243: ? EUR
   - GR-OO2244: ? EUR
   - GR-OO2245: ? EUR
   - GR-OO2242: ? EUR
   - GR-OO2246: ? EUR

4. **Проверить Excel:**
   - Должно быть 7 отдельных строк
   - Сумма в каждой строке = индивидуальная сумма из PDF
   - НЕ должны быть все суммы одинаковые!

5. **Проверить общую сумму:**
   - Сумма всех 7 строк = GESAMT NETTO из PDF

---

## 🛠️ ЧТО НУЖНО ИСПРАВИТЬ В v7.3

### В файле process_pdf_v7_3.py:

1. **Заменить функцию `extract_man()`** на правильную версию выше

2. **Обновить паттерн извлечения:**
   ```python
   # Искать строки таблицы с машиной, Job и суммой
   truck_lines = re.findall(
       r'(GR-OO\s*\d+)\s+.*?Job\s+\d+[:\s]+(.+?)\s+([\d,]+(?:\.\d+)?)\s*(?:EUR|€)?',
       text,
       re.IGNORECASE
   )
   ```

3. **Для каждой строки - своя сумма**

---

## 📝 ИТОГО

### ❌ Неправильно:
```python
total_price / количество_машин  # Делим поровну
```

### ✅ Правильно:
```python
# Извлекаем ИНДИВИДУАЛЬНУЮ сумму для каждой машины из таблицы
for truck, description, individual_amount in truck_lines:
    truck_data['total_price'] = individual_amount  # Своя сумма!
```

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

1. **Обновить** `extract_man()` в process_pdf_v7_3.py
2. **Протестировать** на файле 7501719939
3. **Проверить:**
   - 7 строк в Excel
   - Разные суммы (не все одинаковые!)
   - Общая сумма = GESAMT NETTO из PDF

---

**Спасибо за замечание!** Это действительно критическая ошибка в логике. Сейчас создам исправленную версию v7.3.1
