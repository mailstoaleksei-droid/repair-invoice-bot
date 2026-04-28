# 🔧 PATCH для process_pdf_v7_3.py

## ЗАМЕНИТЬ функцию extract_man() (строки 715-769)

**НА СЛЕДУЮЩИЙ КОД:**

```python
def extract_man(text):
    """
    MAN Truck & Bus Deutschland
    ИСПРАВЛЕНИЕ #3: Gutschrift с минусом
    ИСПРАВЛЕНИЕ #4: Извлечение ИНДИВИДУАЛЬНЫХ сумм для каждой машины
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
    
    # ИСПРАВЛЕНИЕ #3: Проверка на Gutschrift
    is_gutschrift = detect_gutschrift(text)
    
    # 🔴 ИСПРАВЛЕНИЕ #4: Извлечение ИНДИВИДУАЛЬНЫХ сумм для каждой машины
    
    # Паттерн 1: Таблица с данными по машинам
    # Ищем строки вида: "GR-OO2241   Job 1001:   Wartungsvertrag   150,00"
    truck_lines = re.findall(
        r'(GR-OO\s*\d+)\s+.*?Job\s+\d+[:\s]+(.+?)\s+([\d,]+(?:\.[\d,]+)?)\s*(?:EUR|€)?',
        text,
        re.IGNORECASE
    )
    
    # Паттерн 2: Альтернативный формат без "Job"
    if not truck_lines:
        truck_lines = re.findall(
            r'(GR-OO\s*\d+)\s+([^\d]+?)\s+([\d,]+(?:\.[\d,]+)?)\s*(?:EUR|€)',
            text,
            re.IGNORECASE
        )
    
    if truck_lines and len(truck_lines) > 1:
        # ✅ МНОЖЕСТВЕННЫЕ МАШИНЫ - извлекаем ИНДИВИДУАЛЬНЫЕ суммы
        results = []
        
        for truck_raw, description, amount_str in truck_lines:
            truck_data = base_data.copy()
            
            # Форматировать номер машины
            truck_clean = re.sub(r'\s+', '', truck_raw)
            truck_data['truck'] = truck_clean
            
            # Описание (ИСПРАВЛЕНИЕ #6: немецкий текст)
            desc_clean = description.strip()
            if desc_clean:
                truck_data['name'] = desc_clean[:50]
            else:
                truck_data['name'] = 'Wartungsvertrag MAN'
            
            # ✅ ИНДИВИДУАЛЬНАЯ сумма для этой конкретной машины (НЕ делим!)
            amount_clean = amount_str.replace('.', '').replace(',', '.')
            try:
                individual_price = float(amount_clean)
            except:
                continue  # Пропускаем некорректные строки
            
            truck_data['price'] = individual_price
            truck_data['total_price'] = individual_price
            
            # ИСПРАВЛЕНИЕ #3: Gutschrift - делаем отрицательной
            if is_gutschrift:
                truck_data['total_price'] = -abs(truck_data['total_price'])
                truck_data['price'] = -abs(truck_data['price'])
                if 'Gutschrift' not in truck_data['name']:
                    truck_data['name'] = 'Gutschrift - ' + truck_data['name']
            
            results.append(truck_data)
        
        return results  # ВОЗВРАЩАЕМ СПИСОК dict (по одному на машину)
    
    else:
        # ✅ ОДНА МАШИНА или машина не указана
        
        # Машина (ИСПРАВЛЕНИЕ #7: улучшенное извлечение)
        truck_match = re.search(r'GR-OO\s*(\d+)', text)
        if truck_match:
            base_data['truck'] = f"GR-OO{truck_match.group(1)}"
        else:
            base_data['truck'] = ''
        
        # Описание (ИСПРАВЛЕНИЕ #6)
        desc_match = re.search(r'Job\s+\d+:\s+([^\n]+)', text)
        if desc_match:
            base_data['name'] = desc_match.group(1)[:50]
        else:
            base_data['name'] = 'Reparatur MAN'
        
        # Общая сумма NETTO (ИСПРАВЛЕНИЕ #8)
        total_match = re.search(r'NETTO\s+([\d,.]+)\s+EUR', text, re.IGNORECASE)
        if not total_match:
            total_match = re.search(r'Nettobetrag:\s+([\d,.]+)', text)
        
        if not total_match:
            return None
        
        total_str = total_match.group(1).replace('.', '').replace(',', '.')
        base_data['total_price'] = float(total_str)
        base_data['price'] = float(total_str)
        
        # ИСПРАВЛЕНИЕ #3: Gutschrift
        if is_gutschrift:
            base_data['total_price'] = -abs(base_data['total_price'])
            base_data['price'] = -abs(base_data['price'])
            if 'Gutschrift' not in base_data['name']:
                base_data['name'] = 'Gutschrift - ' + base_data['name']
        
        return base_data  # ВОЗВРАЩАЕМ ОДИН dict
```

---

## КАК ПРИМЕНИТЬ ПАТЧ:

### Вариант 1: Вручную в редакторе

1. Открыть `process_pdf_v7_3.py`
2. Найти функцию `extract_man` (строка 715)
3. Удалить строки 715-769
4. Вставить код выше

### Вариант 2: Скачать исправленный файл

Я создам новую версию файла - `process_pdf_v7_3_fixed.py`

---

## ⚠️ ВАЖНО!

Этот патч исправляет **КРИТИЧЕСКУЮ ОШИБКУ #4**:

**Было:** Делим общую сумму поровну на все машины  
**Стало:** Извлекаем ИНДИВИДУАЛЬНУЮ сумму для каждой машины из таблицы

---

## 🧪 КАК ПРОВЕРИТЬ ПОСЛЕ ПАТЧА

Запустить на файле **7501719939**:

1. Должно быть **7 строк** в Excel
2. Каждая строка должна иметь **СВОЮ сумму** (не все одинаковые!)
3. Сумма всех 7 строк = GESAMT NETTO из PDF

**Ожидается:**
- GR-OO2241: 150.00 (или другая индивидуальная сумма)
- GR-OO2240: 150.00
- GR-OO2243: 150.00
- GR-OO2244: 200.00 ← может отличаться!
- GR-OO2245: 150.00
- GR-OO2242: 150.00
- GR-OO2246: 180.00 ← может отличаться!

**НЕ должно быть:**
- Все 7 строк по 161.43 (1130/7) ❌

---

Применив этот патч, v7.3 будет работать правильно!
