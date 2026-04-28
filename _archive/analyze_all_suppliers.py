"""
Универсальный анализатор всех типов поставщиков
Показывает первые 2 файла от каждого поставщика
"""

import os
import pdfplumber
from collections import defaultdict

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def identify_supplier(text):
    """Определить поставщика"""
    text_start = text[:1000].upper()
    text_upper = text.upper()
    
    if 'VITAL PROJEKT' in text_start:
        return 'Vital Projekt'
    elif 'K&L KFZ MEISTERBETRIEB' in text_start:
        return 'K&L'
    elif 'AUTO COMPASS' in text_start and 'KOPIE' in text:
        return 'Auto Compass (Internal)'
    elif 'DEKRA AUTOMOBIL' in text_start:
        return 'DEKRA'
    elif 'SCANIA' in text_start:
        return 'Scania'
    elif 'SCHÜTT' in text_start or 'W. SCHÜTT' in text_start:
        return 'Schütt'
    elif 'VOLVO GROUP' in text_start:
        return 'Volvo'
    elif 'FERRONORDIC' in text_start:
        return 'Ferronordic'
    elif 'QUICK' in text_start:
        return 'Quick Reifendicount'
    elif 'SOTECS' in text_start:
        return 'Sotecs'
    elif 'EXPRESS' in text_start:
        return 'Express'
    elif 'MAN TRUCK' in text_upper or 'MAN SE' in text_upper:
        return 'MAN'
    
    return 'Unknown'

def analyze_all():
    """Анализировать все поставщики"""
    
    suppliers_files = defaultdict(list)
    
    print("Сканирование всех PDF...")
    
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        try:
            pdf_path = os.path.join(PDF_FOLDER, pdf_file)
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ''
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + '\n'
                
                supplier = identify_supplier(full_text)
                suppliers_files[supplier].append((pdf_file, full_text))
        except:
            continue
    
    # Исключить уже готовых
    ready_suppliers = ['Vital Projekt', 'Auto Compass (Internal)', 'Unknown']
    
    print("\n" + "="*80)
    print("АНАЛИЗ ПОСТАВЩИКОВ (кроме готовых и Unknown)")
    print("="*80)
    
    for supplier in sorted(suppliers_files.keys()):
        if supplier in ready_suppliers:
            continue
        
        files = suppliers_files[supplier]
        
        print(f"\n{'='*80}")
        print(f"ПОСТАВЩИК: {supplier} ({len(files)} файлов)")
        print('='*80)
        
        # Показать первые 2 файла
        for i, (filename, text) in enumerate(files[:2], 1):
            print(f"\n--- ФАЙЛ {i}: {filename} ---\n")
            
            # Показать первые 1500 символов
            print(text[:1500])
            
            # Автоматический поиск ключевых данных
            print("\n--- КЛЮЧЕВЫЕ ДАННЫЕ ---")
            lines = text.split('\n')
            for line in lines[:60]:
                line_upper = line.upper()
                if any(kw in line_upper for kw in ['RECHNUNG', 'INVOICE']) and any(c.isdigit() for c in line):
                    print(f"📄 Номер: {line.strip()}")
                elif any(kw in line_upper for kw in ['DATUM', 'DATE']) and any(c.isdigit() for c in line):
                    print(f"📅 Дата: {line.strip()}")
                elif 'KENNZEICHEN' in line_upper or any(pattern in line for pattern in ['GR-', 'DE-', 'HH-']):
                    if len(line) < 80:
                        print(f"🚗 Машина: {line.strip()}")
                elif any(kw in line_upper for kw in ['SUMME', 'GESAMT', 'NETTO', 'TOTAL']) and '€' in line:
                    print(f"💰 Сумма: {line.strip()}")
            
            print("\n" + "-"*80)
        
        if len(files) > 2:
            print(f"\n(ещё {len(files) - 2} файлов от {supplier})")
        
        input("\nНажмите Enter для следующего поставщика...")

if __name__ == "__main__":
    analyze_all()