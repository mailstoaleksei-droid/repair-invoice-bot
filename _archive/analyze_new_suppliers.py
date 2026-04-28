"""
Детальный анализ новых поставщиков для создания функций извлечения
Фокус на: Ferronordic, HNS, TIP, Euromaster, Tankpool24, Scania External
"""

import os
import pdfplumber
from collections import defaultdict

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

# Список файлов для анализа (из unknown_analysis.txt)
TARGET_SUPPLIERS = {
    'Ferronordic': [
        '179 - Ferronordic RE100495-14.pdf',
        '400 - Ferronordic RE100477-12.pdf',
    ],
    'HNS': [
        '4033 - HNS 932150.pdf',
        '4006 - HNS 931758.pdf',
    ],
    'TIP': [
        '771 - TIP U71_90919908.pdf',
        'Miete - TIP U71_90917572.pdf',
    ],
    'Euromaster': [
        '1708 - Euromaster 2500400607.pdf',
        '2243 - Euromaster 2500584053.pdf',
    ],
    'Tankpool24': [
        'Tankpool24 international - 2500351.pdf',
        'Tankpoo24 - Gutschrift DE2508405.pdf',
    ],
    'Scania_External': [
        '1515 - SCHWL51496.pdf',
        '1517 - Scania SCHWL51609.pdf',
    ],
    'PNO': [
        '1708 - PNO 135842.pdf',
        '1710 - PNO 135841.pdf',
    ],
    'Hermanns_Kreutz': [
        '1710 - Hermanns & Kreutz 385168.pdf',
        '502 - Hermanns & Kreutz 383537.pdf',
    ],
    'Yellow_Fox': [
        'Yellow Fox - RP2547836.pdf',
    ],
    'ACW_Logistik': [
        '5000 - ACW RE2025070180.pdf',
    ],
}

def analyze_supplier_files(supplier_name, files):
    """Детально проанализировать файлы одного поставщика"""
    
    print("\n" + "="*80)
    print(f"АНАЛИЗ ПОСТАВЩИКА: {supplier_name}")
    print("="*80)
    
    for i, filename in enumerate(files, 1):
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        if not os.path.exists(pdf_path):
            print(f"\n⚠ Файл не найден: {filename}")
            continue
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ''
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + '\n'
                
                print(f"\n{'─'*80}")
                print(f"ФАЙЛ {i}: {filename}")
                print('─'*80)
                print(f"Страниц: {len(pdf.pages)}")
                print(f"Длина текста: {len(full_text)} символов")
                
                # Показать первые 2000 символов
                print("\nТЕКСТ (начало):")
                print(full_text[:2000])
                
                # Поиск ключевых данных
                print("\n" + "─"*80)
                print("КЛЮЧЕВЫЕ ДАННЫЕ:")
                print("─"*80)
                
                lines = text.split('\n') if text else []
                for line in lines[:80]:
                    line_clean = line.strip()
                    if not line_clean:
                        continue
                    
                    line_upper = line_clean.upper()
                    
                    # Номер счёта
                    if any(kw in line_upper for kw in ['RECHNUNG', 'INVOICE', 'RE-NR', 'RECHNUNGS-NR']):
                        if any(c.isdigit() for c in line_clean):
                            print(f"📄 Номер: {line_clean}")
                    
                    # Дата
                    elif any(kw in line_upper for kw in ['DATUM', 'DATE', 'VOM']):
                        if any(c.isdigit() for c in line_clean):
                            print(f"📅 Дата: {line_clean}")
                    
                    # Машина
                    elif any(kw in line_upper for kw in ['KENNZEICHEN', 'KFZ', 'FAHRZEUG']):
                        print(f"🚗 Машина: {line_clean}")
                    
                    # Сумма
                    elif any(kw in line_upper for kw in ['SUMME', 'GESAMT', 'TOTAL', 'NETTO', 'BRUTTO']):
                        if '€' in line_clean or 'EUR' in line_clean:
                            print(f"💰 Сумма: {line_clean}")
                    
                    # Продавец
                    elif 'GMBH' in line_upper and len(line_clean) < 80:
                        if i == 1:  # Только для первого файла
                            print(f"🏢 Компания: {line_clean}")
                
        except Exception as e:
            print(f"\n❌ Ошибка чтения файла: {e}")
        
        print("\n" + "="*80)
        if i < len(files):
            input("Нажмите Enter для следующего файла...")

def main():
    """Главная функция"""
    
    print("="*80)
    print("АНАЛИЗ НОВЫХ ПОСТАВЩИКОВ ДЛЯ СОЗДАНИЯ ФУНКЦИЙ ИЗВЛЕЧЕНИЯ")
    print("="*80)
    
    suppliers_to_analyze = [
        'Ferronordic',
        'HNS', 
        'TIP',
        'Euromaster',
        'Tankpool24',
        'Scania_External',
        'PNO',
        'Hermanns_Kreutz',
    ]
    
    for supplier in suppliers_to_analyze:
        if supplier in TARGET_SUPPLIERS:
            files = TARGET_SUPPLIERS[supplier]
            analyze_supplier_files(supplier, files)
            
            response = input(f"\nПродолжить анализ следующего поставщика? (Enter = да, 'q' = выход): ")
            if response.lower() == 'q':
                break
    
    print("\n" + "="*80)
    print("АНАЛИЗ ЗАВЕРШЁН")
    print("="*80)
    print("\nСледующий шаг: Создание функций извлечения для каждого поставщика")

if __name__ == "__main__":
    main()