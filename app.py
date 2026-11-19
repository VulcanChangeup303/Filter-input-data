import argparse
import csv
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
import argparse

FIELDS = ("date", "amount", "category", "description", "payment_method", "note")
REQUIRED = ("date", "amount", "category", "description")
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")


# ----------list[dict] ----------

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"CSV không có dòng tiêu đề cột: {path}")
        return [
            {(key or "").strip().lower(): value for key, value in row.items()}
            for row in reader
        ]


def read_xml(path):
    root = ET.parse(path).getroot()
    return [
        {child.tag.strip().lower(): child.text for child in expense}
        for expense in root.findall(".//expense")
    ]


READERS = {".csv": read_csv, ".xml": read_xml}


# ---------- Làm sạch ----------

def clean_text(value):
    return " ".join((value or "").replace("\ufeff", "").replace("\u00a0", " ").split())


def clean_amount(value):
    """'200,000' / '200.000' / '200 000 VND' -> 200000. Không hợp lệ -> None."""
    s = re.sub(r"(?i)vnd|đồng|dong|đ|₫|\s", "", clean_text(value))
    if re.fullmatch(r"\d+", s):
        return int(s)
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):  # dấu ngăn cách hàng nghìn
        return int(re.sub(r"[.,]", "", s))
    return None  # số thập phân, số âm, chữ... bị loại


def clean_date(value):
    value = clean_text(value)
    if re.match(r"\d{4}-\d{2}-\d{2}[T ]", value):
        value = value[:10]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def clean_record(raw):
    raw = {(key or "").strip().lower(): clean_text(value) for key, value in raw.items()}
    return {
        "date": clean_date(raw.get("date", "")),
        "amount": clean_amount(raw.get("amount", "")),
        "category": raw.get("category", ""),
        "description": raw.get("description", ""),
        "payment_method": raw.get("payment_method") or None,
        "note": raw.get("note") or None,
    }

def ensure_database(db_file):
    with sqlite3.connect(db_file) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            payment_method TEXT,
            note TEXT
        )""")
        
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Làm sạch file chi tiêu (.csv/.xml) và nạp vào SQLite."
    )
    parser.add_argument("input", type=Path, help="đường dẫn file .csv hoặc .xml")
    parser.add_argument(
        "--db", type=Path, default=Path("expenses.db"),
        help="file SQLite đầu ra (mặc định: expenses.db trong thư mục đang đứng)",
    )
    return parser.parse_args(argv)

 

def main(argv=None):
    args = parse_args(argv)
    path = args.input.expanduser().resolve()
    db_file = args.db.expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file đầu vào: {path}")

    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise ValueError(
            f"Định dạng '{path.suffix}' chưa được hỗ trợ. Chỉ nhận: {', '.join(READERS)}"
        )

    accepted, rejected = [], Counter()
    for raw in reader(path):
        row = clean_record(raw)
        missing = next((f for f in REQUIRED if row[f] in (None, "")), None)
        if missing:
            rejected[f"missing_or_invalid_{missing}"] += 1
        elif row["amount"] <= 0:
            rejected["amount_not_positive"] += 1
        else:
            accepted.append(tuple(row[f] for f in FIELDS))

    ensure_database(db_file)
    with sqlite3.connect(db_file) as conn:
        conn.executemany(
            f"INSERT INTO expenses ({', '.join(FIELDS)}) "
            f"VALUES ({', '.join('?' * len(FIELDS))})",
            accepted,
        )

    print(f"Đã đọc: {path}")
    print(f"Đã ghi {len(accepted)} dòng sạch vào: {db_file}")
    print(f"Đã bỏ {sum(rejected.values())} dòng không hợp lệ.")
    for reason, count in sorted(rejected.items()):
        print(f"  {reason}: {count}")