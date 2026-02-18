"""One-time import: Repair_2025.xlsx → repair.invoices."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import openpyxl
import psycopg2
from datetime import datetime

EXCEL_PATH = (
    r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente"
    r"\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen"
    r"\RG 2025 Ersatyteile RepRG\Repair_2025.xlsx"
)
DB_URL = (
    "postgresql://neondb_owner:npg_6CJLdnOh2URz"
    "@ep-falling-bird-ag40j8ls-pooler.c-2.eu-central-1.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)

INSERT_SQL = """
INSERT INTO repair.invoices
    (invoice_year, invoice_month, invoice_week, invoice_date,
     truck, total_price, invoice_nr, seller, buyer, kategorie,
     pdf_filename, ai_confidence, ai_model, prompt_version)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (invoice_nr, seller, invoice_date) DO NOTHING
"""


def parse_date(val):
    """Parse date from Excel — can be datetime or string."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


def main():
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb["Sheet1"]

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    errors = 0

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # Columns: Month, Week, Truck, Date, Name, Amount, Price, TotalPrice,
        #          Invoice, Seller, Buyer, InterneRechnung, дата загрузки
        month_val, week_val, truck, date_val, name, amount, price, total_price, \
            invoice_nr, seller, buyer, *rest = row

        # Skip empty rows
        if not invoice_nr or not date_val:
            skipped += 1
            continue

        dt = parse_date(date_val)
        if dt is None:
            print(f"  Row {i}: cannot parse date '{date_val}', skipping")
            errors += 1
            continue

        year = dt.year
        month = dt.month
        week = dt.isocalendar()[1]

        # Parse total_price
        tp = total_price
        if isinstance(tp, str):
            tp = tp.replace(",", ".").replace(" ", "")
        try:
            tp = float(tp)
        except (TypeError, ValueError):
            print(f"  Row {i}: cannot parse total_price '{total_price}', skipping")
            errors += 1
            continue

        truck_str = str(truck or "").strip()
        invoice_str = str(invoice_nr).strip()
        seller_str = str(seller or "").strip()
        buyer_str = str(buyer or "").strip()

        try:
            cur.execute(INSERT_SQL, (
                year, month, week, dt,
                truck_str, tp, invoice_str, seller_str, buyer_str,
                None,           # kategorie (not in historical data)
                "Repair_2025.xlsx",  # pdf_filename (source)
                1.0,            # ai_confidence (manual import = 100%)
                "manual_import",
                "v0",
            ))
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  Row {i}: DB error: {e}")
            conn.rollback()
            errors += 1
            continue

    conn.commit()
    cur.close()
    conn.close()
    wb.close()

    print(f"\nDone: inserted={inserted}, skipped={skipped}, errors={errors}")


if __name__ == "__main__":
    main()
