"""
Проверка типов PDF: текстовые vs сканы
Определяет, можно ли извлечь текст из PDF
"""

import os
import pdfplumber
from collections import defaultdict

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def check_pdf_readability():
    """Проверить, какие PDF можно прочитать"""
    
    readable_count = 0
    scan_count = 0
    error_count = 0
    
    scan_files = []
    error_files = []
    
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    total = len(pdf_files)
    
    print(f"Проверка {total} PDF файлов...\n")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        if i % 50 == 0:
            print(f"Проверено: {i}/{total}")
        
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                
                # Проверка: есть ли текст
                if text and len(text.strip()) > 50:
                    readable_count += 1
                else:
                    scan_count += 1
                    scan_files.append(pdf_file)
                    
        except Exception as e:
            error_count += 1
            error_files.append((pdf_file, str(e)))
    
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ PDF")
    print("="*80)
    print(f"✅ Текстовые PDF (можно обработать):  {readable_count} ({readable_count/total*100:.1f}%)")
    print(f"📷 Сканы (нужно OCR):                 {scan_count} ({scan_count/total*100:.1f}%)")
    print(f"❌ Ошибки чтения:                     {error_count} ({error_count/total*100:.1f}%)")
    print("="*80)
    
    if scan_files:
        print(f"\n📷 НАЙДЕНО {len(scan_files)} СКАНОВ:")
        for f in scan_files[:20]:
            print(f"  - {f}")
        if len(scan_files) > 20:
            print(f"  ... и ещё {len(scan_files) - 20} файлов")
    
    if error_files:
        print(f"\n❌ ОШИБКИ ({len(error_files)} файлов):")
        for f, e in error_files[:10]:
            print(f"  - {f}: {e}")
    
    return {
        'readable': readable_count,
        'scans': scan_count,
        'errors': error_count,
        'scan_files': scan_files
    }

if __name__ == "__main__":
    results = check_pdf_readability()