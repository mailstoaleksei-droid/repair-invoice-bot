import pdfplumber
import sys

pdf_path = sys.argv[1]
print(f"\n{'='*60}")
print(f"ФАЙЛ: {pdf_path.split('\\')[-1]}")
print('='*60)

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages[:2], 1):
        print(f"\n--- СТРАНИЦА {i} ---\n")
        text = page.extract_text()
        if text:
            print(text)
        else:
            print("[Текст не извлечен]")
        print()
