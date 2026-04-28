import re
from datetime import datetime

def extract_vital_projekt(text):
    """
    Извлечь данные из PDF счёта Vital Projekt
    
    Возвращает словарь с данными или None если не удалось извлечь
    """
    
    data = {}
    
    # 1. Номер счёта
    invoice_match = re.search(r'Rechnungs-Nr\.:\s*(\d+)', text)
    if not invoice_match:
        return None
    data['invoice'] = invoice_match.group(1)
    
    # 2. Дата (два варианта)
    # Вариант 1: "Hamburg, den 23.07.2025"
    date_match = re.search(r'Hamburg,\s*den\s*(\d{2}\.\d{2}\.\d{4})', text)
    if date_match:
        date_str = date_match.group(1)
    else:
        # Вариант 2: "Leistungsdatum/-Ort:22-07-2025/HH"
        date_match2 = re.search(r'Leistungsdatum/-Ort:(\d{2})-(\d{2})-(\d{4})', text)
        if date_match2:
            # Преобразовать из DD-MM-YYYY в DD.MM.YYYY
            date_str = f"{date_match2.group(1)}.{date_match2.group(2)}.{date_match2.group(3)}"
        else:
            return None
    
    data['date'] = date_str
    
    # Вычислить Month и Week
    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
    data['month'] = date_obj.month
    data['week'] = date_obj.isocalendar()[1]
    
    # 3. Номер машины
    truck_match = re.search(r'Kennzeichen/Fahrer:\s*([A-Z]{2}\s*[A-Z]{2}\s*\d+)', text)
    if not truck_match:
        return None
    
    # Убрать лишние пробелы и добавить дефисы
    truck_raw = truck_match.group(1)
    truck_clean = re.sub(r'\s+', '', truck_raw)  # Убрать все пробелы
    # Добавить дефис после первых двух букв: GROO2459 -> GR-OO2459
    if len(truck_clean) >= 4:
        data['truck'] = f"{truck_clean[:2]}-{truck_clean[2:]}"
    else:
        data['truck'] = truck_clean
    
    # 4. Извлечь данные из таблицы (первая позиция - главный товар)
    # Ищем строку типа: "1  2  Stk.  FAL 70 BI856  315/70 R22,5..."
    table_match = re.search(
        r'^\s*1\s+(\d+)\s+Stk\.\s+[^\s]+\s+(.+?)\s+\d+%\s+([\d,]+)\s*€\s+([\d,.]+)\s*€',
        text,
        re.MULTILINE
    )
    
    if table_match:
        data['amount'] = int(table_match.group(1))  # Количество
        
        # Описание (сократить до 50 символов)
        description = table_match.group(2).strip()
        data['name'] = description[:50] if len(description) > 50 else description
        
        # Цена за единицу
        price_str = table_match.group(3).replace(',', '.')
        data['price'] = float(price_str)
    else:
        # Если не удалось извлечь из таблицы, попробуем другой способ
        data['amount'] = 1
        data['name'] = "Шины и услуги"
        data['price'] = 0.0
    
    # 5. ИСПРАВЛЕНО: Извлекаем "Summe" (нетто), а не "Gesamtbetrag"
    # Ищем строку типа: "Summe    829,40 €" или "Summe 1.658,80 €"
    summe_match = re.search(r'Summe\s+([\d,.]+)\s*€', text)
    if summe_match:
        total_str = summe_match.group(1).replace('.', '').replace(',', '.')
        data['total_price'] = float(total_str)
    else:
        return None
    
    # 6. Продавец и покупатель (фиксированные для Vital Projekt)
    data['seller'] = 'Vital Projekt Inh.Vitalij Barth'
    data['buyer'] = 'Auto Compass GmbH'
    
    # 7. Interne Rechnung (всегда пусто для Vital, т.к. seller != buyer)
    data['interne_rechnung'] = ''
    
    return data

# Тестирование
if __name__ == "__main__":
    import pdfplumber
    import os
    
    PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
    
    print("Тестирование функции извлечения данных Vital Projekt\n")
    print("="*80)
    
    # Найти все PDF от Vital
    vital_count = 0
    success_count = 0
    
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()
                
                if 'VITAL PROJEKT' not in text.upper():
                    continue
                
                vital_count += 1
                
                # Извлечь данные
                data = extract_vital_projekt(text)
                
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
                else:
                    print(f"\n✗ {filename} - не удалось извлечь данные")
        
        except Exception as e:
            print(f"\n✗ Ошибка при обработке {filename}: {e}")
    
    print("\n" + "="*80)
    print(f"Итого: {success_count}/{vital_count} файлов успешно обработано")