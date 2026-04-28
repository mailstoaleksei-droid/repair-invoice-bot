import os
import pdfplumber

PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def analyze_man_pdfs():
    """Детальный анализ PDF от MAN"""
    
    print("Поиск PDF от MAN...\n")
    
    man_files = []
    
    # Найти все PDF от MAN
    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith('.pdf'):
            continue
        
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Читать все страницы
                full_text = ''
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + '\n'
                
                if 'MAN' in full_text.upper():
                    man_files.append((filename, full_text))
        except:
            continue
    
    print(f"Найдено {len(man_files)} файлов от MAN\n")
    print("="*80)
    
    # Показать первые 3 файла
    for i, (filename, text) in enumerate(man_files[:3], 1):
        print(f"\n{'='*80}")
        print(f"ФАЙЛ {i} из {len(man_files)}: {filename}")
        print('='*80)
        print("\nПОЛНЫЙ ТЕКСТ:")
        print('-'*80)
        print(text[:2000])  # Первые 2000 символов
        print('-'*80)
        
        # Автоматический поиск
        print("\nКЛЮЧЕВЫЕ ДАННЫЕ:")
        print('-'*80)
        
        lines = text.split('\n')
        for line in lines[:50]:  # Первые 50 строк
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ['RECHNUNG', 'INVOICE', 'NUMMER', 'NR']):
                print(f"Номер счёта: {line}")
            elif any(keyword in line_upper for keyword in ['DATUM', 'DATE']):
                print(f"Дата: {line}")
            elif 'KENNZEICHEN' in line_upper or 'GR-' in line or 'DE-' in line:
                print(f"Машина: {line}")
            elif any(keyword in line_upper for keyword in ['SUMME', 'GESAMT', 'TOTAL', 'NETTO']):
                if '€' in line or 'EUR' in line:
                    print(f"Сумма: {line}")
        
        print('='*80)
        input("\nНажмите Enter для следующего файла...")

if __name__ == "__main__":
    analyze_man_pdfs()