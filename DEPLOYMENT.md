# 🚀 Spamerno — Deployment Guide

Complete instructions for running Spamerno locally and deploying to cloud platforms.

---

## 1. Local Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Step-by-Step

```bash
# Clone the repository (or download and extract)
git clone <your-repo-url>
cd spamerno

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Train the ML model
python model/train.py

# Start the development server
python app.py
```

The app will be available at **http://localhost:5000**

---

## 2. Running with Gunicorn (Production)

Flask's built-in server is for development only. For production, use **gunicorn**:

```bash
# Basic usage
gunicorn app:app

# With custom port and workers
gunicorn app:app --bind 0.0.0.0:8000 --workers 4

# With logging
gunicorn app:app --bind 0.0.0.0:8000 --workers 4 --access-logfile -
```

> **Note:** Gunicorn does not run natively on Windows. For local Windows development, use `python app.py`. Gunicorn is used on Linux-based cloud platforms (Render, Railway, Heroku, etc.).

---

## 3. Deploying to Render

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---|---|
| **Name** | `spamerno` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python model/train.py` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

5. Click **Create Web Service**

### Step 3: Set Environment Variables (Optional)

If using VirusTotal domain reputation checks:

1. Go to your service's **Environment** tab
2. Add: `VIRUSTOTAL_API_KEY` = `your-api-key-here`

> Your app currently accepts API keys via the frontend form. Environment variables are an alternative for server-side usage.

---

## 4. Deploying to Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select your repository
4. Railway auto-detects Python. Add:

| Setting | Value |
|---|---|
| **Build Command** | `pip install -r requirements.txt && python model/train.py` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |

5. Deploy

---

## 5. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | Auto-set by platform | The port the app listens on (handled by gunicorn `$PORT`) |
| `VIRUSTOTAL_API_KEY` | ❌ Optional | API key for domain reputation checks |

### Setting Environment Variables

**Render:** Dashboard → Service → Environment tab → Add variable

**Railway:** Dashboard → Service → Variables tab → Add variable

**Local (.env file):**
```bash
# Create a .env file (do NOT commit this to git)
VIRUSTOTAL_API_KEY=your-key-here
```

> **Security:** Never commit API keys to your repository. Always use environment variables.

---

## 6. Pre-Deployment Checklist

- [ ] `requirements.txt` includes all dependencies (including `gunicorn`)
- [ ] Model trained successfully (`model/model.pkl` and `model/vectorizer.pkl` exist)
- [ ] No hardcoded file paths — all paths use `os.path` relative to project root
- [ ] `.gitignore` excludes virtual environments, `__pycache__`, and `.env` files
- [ ] App starts without errors locally

### Recommended `.gitignore`

```
venv/
__pycache__/
*.pyc
.env
*.pkl
```

> **Note:** `.pkl` files are excluded because the model is retrained during the build step. If you prefer to include pre-trained models, remove `*.pkl` from `.gitignore`.

---

## 7. Troubleshooting

### "Model not found" error

The model files (`model.pkl`, `vectorizer.pkl`) need to be generated before starting the app.

```bash
python model/train.py
```

On cloud platforms, ensure the **build command** includes `python model/train.py`.

---

### Port already in use

```bash
# Find and kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

Or run on a different port:

```bash
gunicorn app:app --bind 0.0.0.0:8080
```

---

### Dependency errors

```bash
# Upgrade pip first
pip install --upgrade pip

# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

---

### Gunicorn not found (Windows)

Gunicorn does not support Windows natively. For local development on Windows:

```bash
python app.py
```

For production, deploy to a Linux-based platform (Render, Railway, etc.) where gunicorn runs natively.

---

### Static files not loading

Ensure all templates use Flask's `url_for()` for static files:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

This is already implemented in the project.

---

## 8. Architecture Overview

```
Client Browser
      │
      ▼
  Flask App (app.py)
      │
      ├── ML Pipeline ──► model.pkl + vectorizer.pkl
      │
      ├── URL Analysis ──► utils/url_analysis.py
      │
      ├── Explainability ──► utils/explain.py
      │
      └── Templates ──► templates/ + static/
```

All processing is **in-memory and stateless** — no database required.
