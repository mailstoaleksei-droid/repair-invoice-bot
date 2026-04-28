import os
import pdfplumber

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def analyze_autocompass_pdfs():
    """Детальный анализ внутренних счетов Auto Compass"""
    
    print("Поиск внутренних счетов Auto Compass...\n")
    
    ac_files = []
    
    # Найти все PDF от Auto Compass (внутренние)
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Читать ВСЕ страницы
                full_text = ''
                for page in pdf.pages:
                    full_text += page.extract_text() + '\n'
                
                # Проверить, что это внутренний счёт Auto Compass
                if 'AUTO COMPASS' in full_text.upper() and 'INTERNE RECHNUNG' in full_text.upper():
                    ac_files.append((filename, full_text))
                # Или если в документе есть "KOPIE" и "Auto Compass GmbH" как отправитель
                elif 'KOPIE' in full_text and 'Auto Compass GmbH' in full_text and 'Randersweide' in full_text:
                    ac_files.append((filename, full_text))
        except:
            continue
    
    print(f"Найдено {len(ac_files)} внутренних счетов Auto Compass\n")
    print("="*80)
    
    # Показать первые 3 файла для анализа
    for i, (filename, text) in enumerate(ac_files[:3], 1):
        print(f"\n{'='*80}")
        print(f"ФАЙЛ {i} из {len(ac_files)}: {filename}")
        print('='*80)
        print("\nПОЛНЫЙ ТЕКСТ (ВСЕ СТРАНИЦЫ):")
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
            if 'RECHNUNG' in line_upper and any(char.isdigit() for char in line):
                if 'INTERNE' not in line_upper:
                    print(f"Номер счёта: {line}")
            elif 'DATUM' in line_upper and any(char.isdigit() for char in line):
                print(f"Дата: {line}")
            elif 'KENNZEICHEN' in line_upper:
                print(f"Номер машины: {line}")
            elif 'LEISTUNGSDATUM' in line_upper:
                print(f"Дата работ: {line}")
            elif 'GESAMT' in line_upper and '€' in line:
                print(f"Итоговая сумма: {line}")
            elif 'GROO GMBH' in line_upper:
                print(f"Buyer: {line}")
            elif 'AUTO COMPASS' in line_upper and 'GMBH' in line_upper:
                print(f"Seller/Buyer: {line}")
        
        print('='*80)
        
        if i < 3:
            input("\nНажмите Enter для просмотра следующего файла...")
    
    print(f"\n\nПоказаны первые 3 из {len(ac_files)} внутренних счетов Auto Compass.")

if __name__ == "__main__":
    analyze_autocompass_pdfs()