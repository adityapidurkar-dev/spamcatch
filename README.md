# SpamCatch

A web app that detects whether an email is spam using multiple checks, not just one model.

## ✨ Features

- Smart Detection — Uses text analysis, links, and writing style
- Confidence Score — Shows how sure the system is
- Clear Explanation — Highlights why an email is spam or not
- Link Safety Check — Flags risky or suspicious links
- Writing Style Signals — Detects caps, exclamation marks, unusual length
- Better Handling of Professional Emails — Reduces false spam
- Privacy Friendly — No data is stored

## Installation

```bash
pip install -r requirements.txt
python model/train.py
python app.py
```

Open http://localhost:5000
