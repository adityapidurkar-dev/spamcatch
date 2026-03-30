import csv
import re
from pathlib import Path

p = Path(r"c:\Users\graceharper\Desktop\AIProject\dataset\spam.csv")
rx = re.compile(r"(https?://[^\s,]+|(?:bit\.ly|tinyurl\.com|t\.co|rb\.gy|rebrand\.ly)/[^\s,]+|www\.[^\s,]+)", re.IGNORECASE)

with p.open("r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames or []
    label_key = next((k for k in fieldnames if "label" in (k or "").lower()), fieldnames[0] if fieldnames else "label")

    total = spam = ham = urls = 0
    for row in reader:
        total += 1
        label = (row.get(label_key) or "").strip().lower().strip('"')
        if label == "spam":
            spam += 1
        elif label == "ham":
            ham += 1

        text = f"{row.get('subject', '')} {row.get('body', '')}"
        if rx.search(text):
            urls += 1

print(f"label_key={label_key!r}")
print(f"total={total}")
print(f"spam={spam}")
print(f"ham={ham}")
print(f"url_rows={urls}")
print(f"url_pct={((urls / total) * 100 if total else 0):.2f}%")
