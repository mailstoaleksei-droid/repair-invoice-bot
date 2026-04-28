import os
import pdfplumber
from collections import Counter

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def identify_supplier(text):
    """
    Определить поставщика по содержимому PDF
    Приоритет: точные совпадения в начале документа
    """
    # Берём первые 1000 символов (шапка документа)
    text_start = text[:1000].upper()
    text_upper = text.upper()
    
    # ПРИОРИТЕТ 1: Точные совпадения в начале
    if 'VITAL PROJEKT' in text_start:
        return 'Vital Projekt'
    elif 'K&L KFZ MEISTERBETRIEB' in text_start or 'K&L-KFZ' in text_start:
        return 'K&L'
    elif 'AUTO COMPASS' in text_start and ('KOPIE' in text or 'RANDERSWEIDE' in text):
        return 'Auto Compass (Internal)'
    elif 'DEKRA AUTOMOBIL' in text_start:
        return 'DEKRA'
    elif 'SCANIA HAMBURG' in text_start or 'SCANIA VERTRIEB' in text_start:
        return 'Scania'
    elif 'SCHÜTT GMBH' in text_start or 'W. SCHÜTT' in text_start:
        return 'Schütt'
    elif 'VOLVO GROUP' in text_start:
        return 'Volvo'
    elif 'FERRONORDIC' in text_start:
        return 'Ferronordic'
    elif 'QUICK REIFEN' in text_start:
        return 'Quick Reifendicount'
    elif 'SOTECS' in text_start:
        return 'Sotecs'
    elif 'EXPRESS' in text_start:
        return 'Express'
    
    # ПРИОРИТЕТ 2: Поиск во всём документе (только если не найдено в начале)
    elif 'SCANIA' in text_upper:
        return 'Scania'
    elif 'DEKRA' in text_upper:
        return 'DEKRA'
    elif 'FERRONORDIC' in text_upper:
        return 'Ferronordic'
    
    # MAN - ТОЛЬКО если действительно от MAN
    elif 'MAN TRUCK' in text_upper or 'MAN SE' in text_upper:
        return 'MAN'
    
    return 'Unknown'

# Подсчёт поставщиков
suppliers = Counter()
pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]

print(f"Анализ {len(pdf_files)} файлов...\n")

for i, pdf_file in enumerate(pdf_files, 1):
    if i % 50 == 0:
        print(f"Обработано: {i}/{len(pdf_files)}")
    
    try:
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text()
            supplier = identify_supplier(text)
            suppliers[supplier] += 1
    except:
        suppliers['Error'] += 1

print("\n" + "="*60)
print("РЕЗУЛЬТАТЫ КЛАССИФИКАЦИИ")
print("="*60)

for supplier, count in suppliers.most_common():
    percentage = (count / len(pdf_files)) * 100
    print(f"{supplier:30} : {count:3} файлов ({percentage:5.1f}%)")

print("="*60)
print(f"ВСЕГО: {len(pdf_files)} файлов")