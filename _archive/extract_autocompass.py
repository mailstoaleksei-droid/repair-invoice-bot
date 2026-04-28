import re
from datetime import datetime

def extract_autocompass_internal(text):
    """
    Извлечь данные из внутреннего счёта Auto Compass
    """
    
    data = {}
    
    # 1. Номер счёта
    invoice_match = re.search(r'Rechnung\s+(\d+)', text)
    if not invoice_match:
        return None
    data['invoice'] = invoice_match.group(1)
    
    # 2. Дата (два варианта)
    date_match = re.search(r'Datum\s+(\d{2}\.\d{2}\.\d{4})', text)
    if date_match:
        date_str = date_match.group(1)
    else:
        date_match2 = re.search(r'Leistungsdatum:\s*(\d{2}\.\d{2}\.\d{4})', text)
        if date_match2:
            date_str = date_match2.group(1)
        else:
            return None
    
    data['date'] = date_str
    
    # Вычислить Month и Week
    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
    data['month'] = date_obj.month
    data['week'] = date_obj.isocalendar()[1]
    
    # 3. Номер машины
    truck_match = re.search(r'Kennzeichen\s+([A-Z]{2}-[A-Z]{2}\s*\d+)', text)
    if not truck_match:
        truck_match = re.search(r'([A-Z]{2}-[A-Z]{2}\s+\d+)', text)
    
    if truck_match:
        truck_raw = truck_match.group(1)
        data['truck'] = re.sub(r'\s+', '', truck_raw)
    else:
        data['truck'] = ''
    
    # 4. Извлечь описание
    description_match = re.search(r'Bezeichnung\s+Menge\s+E-Preis\s+Gesamt\s+(.+?)(?:\n\s*[A-Z0-9-]+\s+|\n\s*$)', text, re.DOTALL)
    if description_match:
        desc_text = description_match.group(1).strip()
        desc_lines = [line.strip() for line in desc_text.split('\n') if line.strip()]
        description = desc_lines[0] if desc_lines else desc_text
        data['name'] = description[:50] if len(description) > 50 else description
    else:
        data['name'] = 'Ремонтные работы'
    
    # 5. ИСПРАВЛЕНО: Извлечь количество и цену из ПЕРВОЙ строки таблицы
    # Паттерн: Артикул  Описание  Количество  Цена  Сумма
    # Ищем первую строку после описания
    table_lines = text.split('\n')
    found_table = False
    for i, line in enumerate(table_lines):
        if 'E-Preis' in line and 'Gesamt' in line:
            found_table = True
            continue
        
        if found_table and line.strip():
            # Пропустить строки с описанием (без чисел)
            if not any(char.isdigit() for char in line):
                continue
            
            # Найти первую строку с артикулом и числами
            # Формат: АРТИКУЛ ОПИСАНИЕ КОЛИЧЕСТВО ЦЕНА СУММА
            parts = line.split()
            # Найти числа (с запятыми)
            numbers = []
            for part in parts:
                if re.match(r'^\d+[,.]?\d*$', part.replace(',', '.')):
                    numbers.append(part.replace(',', '.'))
            
            # Должно быть минимум 3 числа: количество, цена, сумма
            if len(numbers) >= 3:
                data['amount'] = float(numbers[-3])
                data['price'] = float(numbers[-2])
                break
    
    if 'amount' not in data:
        data['amount'] = 1
        data['price'] = 0.0
    
    # 6. ИСПРАВЛЕНО: Итоговая сумма НЕТТО
    # Ищем строку вида: "18,75 € 76,00 € 0.00 € 94,75 €"
    # где последнее число - это Netto
    # Затем идёт строка с "Gesamt"
    
    # Вариант 1: Ищем "Netto" и берём число после него
    netto_pattern1 = re.search(r'Netto\s+([\d,.]+)\s*€', text)
    
    # Вариант 2: Ищем строку с 4 суммами и берём последнюю
    netto_pattern2 = re.search(r'([\d,.]+)\s*€\s+([\d,.]+)\s*€\s+([\d,.]+)\s*€\s+([\d,.]+)\s*€\s+Gesamt', text)
    
    # Вариант 3: Ищем строку "Lohn Material Fremdleistung Netto"
    netto_pattern3 = re.search(r'Lohn\s+Material\s+Fremdleistung\s+Netto\s+[\d,.]+\s*€\s+[\d,.]+\s*€\s+[\d,.]+\s*€\s+([\d,.]+)\s*€', text)
    
    if netto_pattern3:
        total_str = netto_pattern3.group(1).replace('.', '').replace(',', '.')
        data['total_price'] = float(total_str)
    elif netto_pattern2:
        total_str = netto_pattern2.group(4).replace('.', '').replace(',', '.')
        data['total_price'] = float(total_str)
    elif netto_pattern1:
        total_str = netto_pattern1.group(1).replace('.', '').replace(',', '.')
        data['total_price'] = float(total_str)
    else:
        return None
    
    # 7. Продавец
    data['seller'] = 'Auto Compass GmbH'
    
    # 8. Покупатель
    buyer_match = re.search(r'Firma\s+(.+?)(?:\n|Randersweide)', text)
    if buyer_match:
        buyer = buyer_match.group(1).strip()
        data['buyer'] = buyer
    else:
        data['buyer'] = 'Unknown'
    
    # 9. Interne Rechnung
    if data['seller'] == data['buyer']:
        data['interne_rechnung'] = 'Interne Rechnung'
    else:
        data['interne_rechnung'] = ''
    
    return data
    

# Тестирование
if __name__ == "__main__":
    import pdfplumber
    import os
    
    PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
    
    print("Тестирование функции извлечения данных Auto Compass (Internal)\n")
    print("="*80)
    
    ac_count = 0
    success_count = 0
    
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Читать все страницы
                full_text = ''
                for page in pdf.pages:
                    full_text += page.extract_text() + '\n'
                
                # Проверить признаки Auto Compass Internal
                if not ('AUTO COMPASS' in full_text.upper() and 'KOPIE' in full_text):
                    continue
                
                ac_count += 1
                
                # Извлечь данные
                data = extract_autocompass_internal(full_text)
                
                if data:
                    success_count += 1
                    print(f"\n✓ {filename}")
                    print(f"  Invoice: {data['invoice']}")
                    print(f"  Date: {data['date']} (Month: {data['month']}, Week: {data['week']})")
                    print(f"  Truck: {data['truck']}")
                    print(f"  Name: {data['name']}")
                    print(f"  Amount: {data['amount']}")
                    print(f"  Price: {data['price']:.2f} €")
                    print(f"  Total: {data['total_price']:.2f} €")
                    print(f"  Seller: {data['seller']}")
                    print(f"  Buyer: {data['buyer']}")
                    print(f"  Interne Rechnung: {data['interne_rechnung']}")
                else:
                    print(f"\n✗ {filename} - не удалось извлечь данные")
        
        except Exception as e:
            print(f"\n✗ Ошибка при обработке {filename}: {e}")
    
    print("\n" + "="*80)
    print(f"Итого: {success_count}/{ac_count} файлов успешно обработано")