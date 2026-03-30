# Spamerno — Project Explanation

## 📌 What Is Spamerno?

Spamerno is an **AI-powered email spam detection web application** built with Python. It takes an email (subject + body) as input and classifies it as **SPAM** or **NOT SPAM**, while providing a detailed, explainable breakdown of *why* it made that decision.

Unlike simple keyword filters, Spamerno uses a **hybrid decision system** that combines:

1. **Machine Learning** (TF-IDF + Naive Bayes with calibration)
2. **URL risk analysis** (shorteners, suspicious domains, phishing keywords)
3. **Structural signal detection** (exclamation marks, uppercase ratio, ALL-CAPS words)
4. **Context-aware bias adjustment** (recognizes formal/professional language)

---

## 🧠 How the AI Model Works

### Training Pipeline

| Step | Description |
|---|---|
| **Dataset** | 90,000+ labeled emails (`spam.csv`) with `label`, `subject`, and `body` columns |
| **Label Mapping** | `spam → 1`, `ham → 0` |
| **Text Preprocessing** | Lowercase, remove punctuation, strip extra whitespace |
| **Subject Weighting** | Subject is repeated (`subject + subject + body`) to increase its importance |
| **Vectorization** | `TfidfVectorizer` with bigrams `(1, 2)` and custom stopwords |
| **Model** | `MultinomialNB` wrapped in `CalibratedClassifierCV` (sigmoid method, 5-fold) |
| **Output** | Saves `model.pkl` and `vectorizer.pkl` for use by the web app |

### Key ML Concepts Used

- **TF-IDF (Term Frequency–Inverse Document Frequency):** Converts text into numerical vectors by measuring how important a word is relative to the entire dataset. Common words get low scores; distinctive words get high scores.

- **N-Grams (Bigrams):** The vectorizer uses `ngram_range=(1, 2)`, which means it considers both single words ("free") and two-word phrases ("click here", "verify account"). This captures spam patterns that single words miss.

- **Custom Stopwords:** Standard English stopwords are used, but negation words like "not", "no", "never" are **kept** because they change meaning (e.g., "not spam" vs "spam").

- **Multinomial Naive Bayes:** A probabilistic classifier well-suited for text data. It calculates the probability that an email belongs to each class based on word frequencies.

- **Calibrated Probabilities:** Raw Naive Bayes probabilities tend to be overconfident (very close to 0% or 100%). `CalibratedClassifierCV` with sigmoid method produces more realistic, well-calibrated probability estimates.

---

## ⚙️ Hybrid Decision System

The final classification is **not** just the ML model's output. It goes through a multi-stage hybrid decision process:

```
ML Probability → Context Bias → URL Boost → Structure Boost → Formal Tone → Final Label
```

### Stage 1: ML Prediction
The calibrated model produces a spam probability (0.0 to 1.0).

### Stage 2: Context-Based Bias Adjustment
If the email contains formal/professional phrases like:
- "I am writing to apply"
- "Please find attached my resume"
- "Best regards"

The spam probability is **reduced** (up to -0.25), because these phrases indicate legitimate communication.

### Stage 3: URL Risk Signal
- **HIGH risk URLs** (suspicious TLDs like `.xyz`, `.tk`, phishing keywords) → spam probability **increased**
- **No URLs + formal tone** → spam probability **decreased**

### Stage 4: Structural Signal
Spammy emails tend to have excessive exclamation marks, high uppercase ratios, and ALL-CAPS words. These structural features **boost** the spam probability.

### Stage 5: Threshold Decision
If final adjusted probability > **0.65** → **SPAM**, otherwise → **NOT SPAM**.
If probability is between **0.45 and 0.65** → marked as **Uncertain**.

---

## 🌐 URL Analysis

Every URL found in the email is analyzed for risk:

| Check | What It Detects |
|---|---|
| URL Shorteners | `bit.ly`, `tinyurl.com`, etc. |
| Suspicious TLDs | `.xyz`, `.tk`, `.ml`, `.ru`, `.cn`, etc. |
| Phishing Keywords | `login`, `verify`, `password`, `banking` in the URL |
| Domain Digits | Excessive numbers in the domain name |
| IP Addresses | Using `192.168.x.x` instead of a domain name |
| Long Domains | Unusually long domain names (spoofing) |
| Multiple Subdomains | Potential domain spoofing |

Each URL gets a **numeric risk score (0–100)** and a label: LOW, MEDIUM, or HIGH.

Optional: Users can enter a **VirusTotal API key** to check live domain reputation (the key is never stored).

---

## 🖥️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| ML Model | scikit-learn (TF-IDF + MultinomialNB + CalibratedClassifierCV) |
| Model Persistence | joblib |
| Input Sanitization | bleach (prevents XSS attacks) |
| Frontend | HTML, CSS (monochrome design), JavaScript |
| Dataset | CSV (90,000+ entries) |

---

## 📁 Project Structure

```
AIProject/
├── app.py                  # Flask web server + hybrid decision system
├── requirements.txt        # Python dependencies
├── README.md               # Setup and deployment guide
│
├── model/
│   ├── train.py            # ML training script
│   ├── model.pkl           # Trained model (generated)
│   └── vectorizer.pkl      # TF-IDF vectorizer (generated)
│
├── utils/
│   ├── text_cleaning.py    # Text preprocessing + keyword extraction
│   ├── url_analysis.py     # URL risk assessment
│   └── explain.py          # Explainability (highlighting, risk indicators)
│
├── templates/
│   ├── index.html          # Input page
│   └── result.html         # Results page with full analysis
│
├── static/
│   └── style.css           # Monochrome design system
│
└── dataset/
    └── spam.csv            # Training dataset (90,000+ rows)
```

---

## 🔒 Security Features

- **Input Sanitization:** All user inputs are cleaned with `bleach` to prevent XSS (Cross-Site Scripting) attacks.
- **No Data Persistence:** No emails or API keys are stored. All processing is in-memory and temporary.
- **Input Length Limit:** Maximum 10,000 characters to prevent abuse. Inputs exceeding this are truncated with a warning.

---

## 📊 What the User Sees

When an email is analyzed, the results page shows:

1. **Classification Badge** — SPAM or NOT SPAM with confidence percentage
2. **Uncertainty Warning** — If the model is unsure (45–65% range)
3. **Highlighted Text** — Spam-contributing words highlighted in red
4. **Top Keywords** — Words with highest spam contribution scores
5. **URL Analysis** — Each URL analyzed with risk level and reasons
6. **Risk Indicators** — Word Risk and URL Risk badges
7. **Structure Signals** — Exclamation count, uppercase ratio, ALL-CAPS words, email length
8. **Hybrid Decision Adjustments** — Shows exactly what factors modified the prediction
9. **Analytics** — Total words, spam words found, URLs found, contribution breakdown

---

## 🧪 Example Results

### Spam Email
- **Input:** "URGENT! You've been selected for $5000/week remote job!!!"
- **Result:** ⛔ SPAM at **99.0%** confidence
- **Adjustments:** URL risk boost (+0.04), Structure boost (+0.03)

### Legitimate Job Application
- **Input:** "I am writing to apply for the Software Developer position. Please find attached my resume."
- **Result:** ✅ NOT SPAM at **50.3%** confidence (uncertain)
- **Adjustments:** HAM bias (-0.15), Formal tone (-0.10), Context override (-0.25)

This shows the hybrid system correctly distinguishing between job scams and real job applications — a problem that pure keyword-based systems fail at.

---

## 🚀 How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model
python model/train.py

# 3. Start the web app
python app.py

# 4. Open in browser
# http://localhost:5000
```

---

## 📝 Summary

Spamerno demonstrates how combining **machine learning with rule-based heuristics** creates a more robust and reliable spam detection system. The hybrid approach addresses real-world challenges like false positives on legitimate professional emails, while the explainability features make every prediction transparent and understandable.
