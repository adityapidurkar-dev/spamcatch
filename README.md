# 🛡️ Spamerno — Explainable AI Email Spam Detection

A production-ready, AI-powered web application that detects email spam using a **hybrid decision system** combining machine learning, URL risk analysis, and structural signal detection — with fully explainable results.

## ✨ Features

- **Hybrid Spam Detection** — Combines ML prediction + URL risk + structural signals + context-aware bias
- **Calibrated Confidence** — Realistic probability scores using `CalibratedClassifierCV`
- **Explainable AI** — Top spam-contributing words with scores, highlighted in the email text
- **URL Risk Analysis** — Detects shorteners, suspicious TLDs, phishing keywords, with numeric risk scoring (0–100)
- **Domain Reputation** — Optional VirusTotal API integration (key never stored)
- **Structure Signals** — Exclamation marks, uppercase ratio, ALL CAPS words, email length
- **False Positive Reduction** — Context-aware HAM bias for professional emails (job applications, formal communication)
- **Uncertainty Detection** — Flags predictions with confidence between 45–65%
- **Input Validation** — 10,000 character limit with live counter and truncation handling
- **Privacy-First** — No data stored, all processing is temporary and in-memory
- **Production Ready** — Gunicorn support, relative paths, deployment guides

## 📁 Project Structure

```
spamerno/
├── app.py                  # Flask app + hybrid decision engine
├── requirements.txt        # Python dependencies (incl. gunicorn)
├── README.md               # This file
├── DEPLOYMENT.md           # Full deployment instructions
├── explain.md              # Detailed project explanation
├── dataset/
│   └── spam.csv            # Training dataset (90,000+ examples)
├── model/
│   ├── train.py            # ML training pipeline
│   ├── model.pkl           # Trained model (generated)
│   └── vectorizer.pkl      # TF-IDF vectorizer (generated)
├── utils/
│   ├── text_cleaning.py    # Text preprocessing & keyword extraction
│   ├── url_analysis.py     # URL risk analysis & domain reputation
│   └── explain.py          # Explainability & highlighting
├── templates/
│   ├── index.html          # Input page
│   └── result.html         # Results page with full analysis
└── static/
    └── style.css           # Monochrome design system
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Train the model
python model/train.py

# Run the app
python app.py
```

Open **http://localhost:5000** in your browser.

## 🧠 How It Works

1. **Text Preprocessing** — Lowercase, punctuation removal, subject weighting
2. **TF-IDF Vectorization** — Bigrams `(1, 2)`, custom stopwords (keeps negation words)
3. **Calibrated Naive Bayes** — `MultinomialNB` wrapped in `CalibratedClassifierCV` (sigmoid, 5-fold)
4. **Hybrid Decision** — ML probability adjusted by URL risk, structural signals, and context bias
5. **Threshold Classification** — Tuned threshold of 0.65 (not default 0.5)
6. **Explainability** — Top keywords, URL analysis, risk indicators, contribution breakdown

## 🌐 Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete instructions including:

- Local setup with virtual environment
- Running with gunicorn (production)
- Deploying to Render / Railway
- Environment variable configuration
- Troubleshooting guide

### Quick Deploy (Render)

| Setting | Value |
|---|---|
| **Build Command** | `pip install -r requirements.txt && python model/train.py` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |

## 🔒 Security

- All inputs sanitized with `bleach` (prevents XSS)
- HTML tags stripped from user input
- API keys never stored or logged
- No user data persisted — fully stateless
- Input length capped at 10,000 characters
