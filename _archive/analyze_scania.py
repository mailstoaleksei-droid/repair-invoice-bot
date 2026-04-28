import os
import pdfplumber

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def analyze_scania_pdfs():
    """Детальный анализ PDF от Scania"""
    
    print("Поиск PDF от Scania...\n")
    
    scania_files = []
    
    # Найти все PDF от Scania
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if 'SCANIA' in text.upper():
                    scania_files.append((filename, text))
        except:
            continue
    
    print(f"Найдено {len(scania_files)} файлов от Scania\n")
    print("="*80)
    
    # Показать первые 3 файла для анализа
    for i, (filename, text) in enumerate(scania_files[:3], 1):
        print(f"\n{'='*80}")
        print(f"ФАЙЛ {i} из {len(scania_files)}: {filename}")
        print('='*80)
        print("\nПОЛНЫЙ ТЕКСТ:")
        print('-'*80)
        print(text)
        print('-'*80)
        
        # Автоматический поиск ключевых данных
        print("\nАВТОМАТИЧЕСКИЙ ПОИСК ДАННЫХ:")
        print('-'*80)
        
        lines = text.split('\n')
        for line in lines:
            line_upper = line.upper()
            # Искать ключевые слова
            if 'RECHNUNG' in line_upper and 'NR' in line_upper:
                print(f"Номер счёта: {line}")
            elif 'DATUM' in line_upper or 'FERTIG' in line_upper:
                print(f"Дата: {line}")
            elif 'KENNZEICHEN' in line_upper or 'KENNZ' in line_upper:
                print(f"Номер машины: {line}")
            elif 'GESAMTBETRAG' in line_upper or 'SUMME' in line_upper:
                print(f"Сумма: {line}")
            elif 'AUTO COMPASS' in line_upper:
                print(f"Покупатель: {line}")
            elif any(kw in line for kw in ['GR-', 'DE-', 'MNH', 'HH-']):
                if len(line) < 50:
                    print(f"Возможный номер машины: {line}")
        
        print('='*80)
        
        if i < 3:
            input("\nНажмите Enter для просмотра следующего файла...")
    
    print(f"\n\nПоказаны первые 3 из {len(scania_files)} файлов Scania.")
    print("Для просмотра остальных запустите скрипт снова и увеличьте срез [:3] до [:5] или больше")

if __name__ == "__main__":
    analyze_scania_pdfs()