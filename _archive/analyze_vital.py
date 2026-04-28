import os
import pdfplumber

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def analyze_vital_pdfs():
    """Детальный анализ PDF от Vital Projekt"""
    
    print("Поиск PDF от Vital Projekt...\n")
    
    vital_files = []
    
    # Найти все PDF от Vital Projekt
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if 'VITAL PROJEKT' in text.upper():
                    vital_files.append((filename, text))
        except:
            continue
    
    print(f"Найдено {len(vital_files)} файлов от Vital Projekt\n")
    print("="*80)
    
    # Проанализировать каждый файл
    for i, (filename, text) in enumerate(vital_files, 1):
        print(f"\n{'='*80}")
        print(f"ФАЙЛ {i}: {filename}")
        print('='*80)
        print("\nПОЛНЫЙ ТЕКСТ ПЕРВОЙ СТРАНИЦЫ:")
        print('-'*80)
        print(text)
        print('-'*80)
        
        # Попытаться найти ключевые данные
        print("\nАВТОМАТИЧЕСКИЙ ПОИСК ДАННЫХ:")
        print('-'*80)
        
        lines = text.split('\n')
        for line in lines:
            line_upper = line.upper()
            # Искать ключевые слова
            if 'RECHNUNGS-NR' in line_upper or 'RECHNUNG' in line_upper:
                print(f"Номер счёта: {line}")
            elif 'HAMBURG, DEN' in line_upper or 'DATUM' in line_upper:
                print(f"Дата: {line}")
            elif 'AUTO COMPASS' in line_upper and 'GMBH' in line_upper:
                print(f"Покупатель: {line}")
            elif 'GESAMTBETRAG' in line_upper:
                print(f"Итоговая сумма: {line}")
            elif any(kw in line for kw in ['DE-', 'GR-', 'MNH', 'HH-']):
                if len(line) < 50:  # Короткая строка с возможным номером машины
                    print(f"Возможный номер машины: {line}")
        
        print('='*80)
        input("\nНажмите Enter для просмотра следующего файла...")

if __name__ == "__main__":
    analyze_vital_pdfs()