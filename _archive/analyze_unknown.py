"""
Детальный анализ всех Unknown файлов
Группирует по похожим паттернам для выявления поставщиков
"""

import os
import pdfplumber
from collections import defaultdict
import re

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def identify_supplier(text):
    """Определить поставщика"""
    text_start = text[:1000].upper()
    
    if 'VITAL PROJEKT' in text_start:
        return 'Vital Projekt'
    elif 'K&L KFZ' in text_start:
        return 'K&L'
    elif 'AUTO COMPASS' in text_start and 'KOPIE' in text:
        return 'Auto Compass (Internal)'
    elif 'DEKRA' in text_start:
        return 'DEKRA'
    elif 'SCANIA' in text_start:
        return 'Scania'
    elif 'SCHÜTT' in text_start:
        return 'Schütt'
    elif 'VOLVO' in text_start:
        return 'Volvo'
    elif 'FERRONORDIC' in text_start:
        return 'Ferronordic'
    elif 'QUICK' in text_start:
        return 'Quick'
    elif 'SOTECS' in text_start:
        return 'Sotecs'
    elif 'EXPRESS' in text_start:
        return 'Express'
    elif 'MAN TRUCK' in text or 'MAN SE' in text:
        return 'MAN'
    
    return 'Unknown'

def extract_company_names(text):
    """Извлечь возможные названия компаний"""
    companies = []
    
    # Паттерны для поиска компаний
    patterns = [
        r'([A-ZÄÖÜ][a-zäöü]+(?:\s+[A-ZÄÖÜ][a-zäöü]+)*)\s+GmbH',
        r'([A-ZÄÖÜ][A-Z\s]+)\s+GmbH',
        r'Rechnung\s+von\s+([A-ZÄÖÜ][^\n]+)',
        r'Rechnungssteller[:\s]+([A-ZÄÖÜ][^\n]+)',
        r'Von[:\s]+([A-ZÄÖÜ][^\n]+GmbH)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text[:2000])
        companies.extend(matches)
    
    # Убрать дубликаты
    return list(set([c.strip() for c in companies if len(c) > 3]))

def analyze_unknown_files():
    """Проанализировать все Unknown файлы"""
    
    unknown_files = []
    
    print("Сканирование PDF файлов...\n")
    
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
                
                if supplier == 'Unknown':
                    companies = extract_company_names(full_text)
                    unknown_files.append({
                        'filename': pdf_file,
                        'text': full_text[:2000],
                        'companies': companies,
                        'text_length': len(full_text)
                    })
        except:
            continue
    
    print(f"\n{'='*80}")
    print(f"НАЙДЕНО {len(unknown_files)} UNKNOWN ФАЙЛОВ")
    print('='*80)
    
    # Группировка по компаниям
    by_company = defaultdict(list)
    
    for item in unknown_files:
        if item['companies']:
            main_company = item['companies'][0]
            by_company[main_company].append(item['filename'])
        else:
            by_company['БЕЗ КОМПАНИИ'].append(item['filename'])
    
    # Топ-10 поставщиков в Unknown
    print("\nТОП ПОСТАВЩИКОВ В UNKNOWN:")
    print("-"*80)
    
    sorted_companies = sorted(by_company.items(), key=lambda x: len(x[1]), reverse=True)
    
    for company, files in sorted_companies[:15]:
        print(f"{company:40} : {len(files):3} файлов")
    
    print("\n" + "="*80)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ (первые 10 Unknown файлов)")
    print("="*80)
    
    # Показать первые 10 файлов
    for i, item in enumerate(unknown_files[:10], 1):
        print(f"\n--- ФАЙЛ {i}: {item['filename']} ---")
        print(f"Длина текста: {item['text_length']} символов")
        print(f"Возможные компании: {', '.join(item['companies'][:3])}")
        print("\nНачало текста:")
        print(item['text'][:800])
        print("-"*80)
        
        response = input("\nНажмите Enter для следующего файла (или 'q' для выхода)...")
        if response.lower() == 'q':
            break
    
    # Сохранить полный отчёт
    report_path = os.path.join(os.path.dirname(PDF_FOLDER), 'PDF_Processor', 'unknown_analysis.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ПОЛНЫЙ СПИСОК UNKNOWN ФАЙЛОВ\n")
        f.write("="*80 + "\n\n")
        
        for company, files in sorted_companies:
            f.write(f"\n{company} ({len(files)} файлов):\n")
            for filename in files:
                f.write(f"  - {filename}\n")
    
    print(f"\n✓ Отчёт сохранён: {report_path}")
    
    return unknown_files, by_company

if __name__ == "__main__":
    unknown_files, by_company = analyze_unknown_files()