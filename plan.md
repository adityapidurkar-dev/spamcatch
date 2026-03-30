# 🚀 Spamerno – Advanced Project Generation Prompt (Claude / Antigravity)

You are a senior full-stack AI engineer and software architect.

Your task is to build a **production-grade, clean, secure, modular project** named:

# 🧠 Spamerno
An Explainable AI Email Spam Detection Web Application

This must be a COMPLETE, fully working system with NO placeholders.

---

# 🎯 CORE OBJECTIVE

Users can:
- Paste email subject + body
- Click "Check for Spam"
- Get:
  - Spam / Not Spam result
  - Confidence score
  - Highlighted spam words
  - URL risk analysis
  - Optional domain reputation check (API-based)
  - Clear analytics breakdown

---

# ⚙️ ENGINEERING REQUIREMENTS

## Code Quality
- Clean, modular architecture
- Separation of concerns
- Reusable functions
- Proper error handling
- No hardcoding sensitive data
- Secure input handling

## Performance
- Load ML model once at startup
- Fast inference (<1s)

---

# 🧠 MACHINE LEARNING PIPELINE

Use ONLY:
- TF-IDF Vectorizer
- Multinomial Naive Bayes

### Steps:
1. Text preprocessing:
   - Lowercase
   - Remove punctuation
   - Remove extra whitespace
2. Combine subject + body
3. TF-IDF transformation
4. Train model
5. Save:
   - model.pkl
   - vectorizer.pkl

### Dataset:
- Use Enron dataset if possible
- Otherwise create realistic fallback dataset

---

# 🧩 FUNCTIONAL MODULES

## 1. Text Processing Module
- Cleaning
- Tokenization
- Keyword extraction

## 2. Prediction Module
Returns:
- label (spam/not spam)
- confidence score
- important words

## 3. URL Analysis Module
- Extract URLs via regex
- Analyze:
  - Domain length
  - Suspicious TLDs
  - Shorteners
- Output risk: LOW / MEDIUM / HIGH

## 4. Domain Reputation Module
- Button-triggered
- Accept API key from user input
- DO NOT store key
- Fetch result from API (mock if needed)

---

# 📊 RESULT UI STRUCTURE

## 1. RESULT CARD
- SPAM / NOT SPAM
- Confidence %

## 2. EXPLANATION PANEL
- Highlight spam words in text
- Show:
  - Top spam words
  - Indicators:
    - suspicious keywords
    - suspicious URLs
    - abnormal structure

## 3. URL ANALYSIS PANEL
- List URLs
- Show risk level
- Provide API check button

## 4. ANALYTICS PANEL
Display:
- Total words
- Spam words count
- URLs count
- Spam score contribution:
  - words %
  - URLs %

## 5. WARNING PANEL
Display prominently:

⚠️ Privacy Notice:
- No data is stored
- API keys are not saved
- Processing is temporary

---

# 🎨 UI / UX REQUIREMENTS

- Monochrome theme (black/white/grey)
- Minimalist, professional
- Responsive layout

## Layout:
Top-left:
- Spamerno logo/text

Center:
- Title: "Paste your full email below"
- Input fields:
  - Subject
  - Body

Bottom:
- Button: "Check for Spam"

After submission:
- Smooth transition to result view
- Clean section separation

Include:
- Loading state: "Analyzing email..."

---

# 🧱 PROJECT STRUCTURE

spamerno/
│── app.py
│── model/
│   ├── train.py
│   ├── model.pkl
│   ├── vectorizer.pkl
│── utils/
│   ├── text_cleaning.py
│   ├── url_analysis.py
│   ├── explain.py
│── templates/
│   ├── index.html
│   ├── result.html
│── static/
│   ├── style.css
│── requirements.txt
│── README.md

---

# 🔒 SECURITY REQUIREMENTS

- Sanitize all inputs
- Prevent script injection
- Do not log sensitive input
- Validate API inputs

---

# 📦 README REQUIREMENTS

Include:
- Project overview
- Features
- Setup instructions
- How to run locally
- Deployment guide (Render or similar)
- Notes on API usage

---

# 🚀 DEPLOYMENT

Include:
- Local run steps
- Deployment steps (Render)

---

# ❗ STRICT RULES

- NO placeholders
- NO incomplete files
- FULL working code
- Clean structure
- Beginner-readable but professional

---

# 🧠 EXPECTATION

This should feel like a real product:
- Clean UX
- Explainable AI
- Structured backend

---

Now generate the FULL project with all files and code.
