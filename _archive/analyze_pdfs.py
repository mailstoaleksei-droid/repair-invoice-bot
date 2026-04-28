import os
import pdfplumber

# Путь к папке с PDF
PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"

def identify_supplier(text):
    """Определить поставщика по содержимому PDF"""
    text_upper = text.upper()
    
    if 'VITAL PROJEKT' in text_upper:
        return 'Vital Projekt'
    elif 'DEKRA' in text_upper:
        return 'DEKRA'
    elif 'VOLVO GROUP' in text_upper or 'VOLVO TRUCKS' in text_upper:
        return 'Volvo'
    elif 'SCANIA' in text_upper:
        return 'Scania'
    elif 'AUTO COMPASS GMBH' in text_upper and 'INTERNE RECHNUNG' in text_upper:
        return 'Auto Compass (Internal)'
    elif 'FERRONORDIC' in text_upper:
        return 'Ferronordic'
    else:
        return 'Unknown'

def analyze_pdfs():
    """Проанализировать все PDF в папке"""
    suppliers = {}
    total_pdfs = 0
    errors = []
    
    print("Анализ PDF файлов...\n")
    
    # Получить список всех PDF
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    
    for pdf_file in pdf_files:
        total_pdfs += 1
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Прочитать первую страницу
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # Определить поставщика
                supplier = identify_supplier(text)
                
                # Добавить в счётчик
                if supplier not in suppliers:
                    suppliers[supplier] = []
                suppliers[supplier].append(pdf_file)
                
                print(f"✓ {pdf_file[:50]}... → {supplier}")
                
        except Exception as e:
            errors.append((pdf_file, str(e)))
            print(f"✗ Ошибка при чтении {pdf_file}: {e}")
    
    # Вывести статистику
    print("\n" + "="*70)
    print("СТАТИСТИКА")
    print("="*70)
    print(f"Всего PDF файлов: {total_pdfs}\n")
    
    # Отсортировать по количеству
    sorted_suppliers = sorted(suppliers.items(), key=lambda x: len(x[1]), reverse=True)
    
    for supplier, files in sorted_suppliers:
        print(f"{supplier:30} : {len(files):3} файлов")
    
    print("\n" + "="*70)
    
    if errors:
        print(f"\nОшибки при чтении: {len(errors)} файлов")
        for filename, error in errors[:5]:  # Показать первые 5
            print(f"  - {filename}: {error}")
    
    # Рекомендация
    if sorted_suppliers:
        top_supplier = sorted_suppliers[0][0]
        top_count = len(sorted_suppliers[0][1])
        print(f"\nРЕКОМЕНДАЦИЯ: Начните с '{top_supplier}' ({top_count} файлов)")

if __name__ == "__main__":
    analyze_pdfs()