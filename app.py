"""
Spamerno - Flask Web Application
Explainable AI Email Spam Detection with Hybrid Decision System
"""

import os
import re
import joblib
import bleach
from flask import Flask, render_template, request, jsonify

from utils.text_cleaning import clean_text, combine_email
from utils.url_analysis import check_domain_reputation, extract_urls, analyze_all_urls
from utils.explain import (
    get_explanation,
    highlight_spam_words,
    highlight_urls_in_text,
)

# ─── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)

# Maximum allowed input length (characters)
MAX_INPUT_LENGTH = 10000

# Spam classification threshold (tuned above default 0.5)
SPAM_THRESHOLD = 0.65

# Maximum confidence cap to avoid overconfident predictions
MAX_CONFIDENCE = 99.5

# Strong HAM indicator phrases (reduce spam probability when found)
HAM_INDICATORS = [
    "i am writing to apply",
    "please find attached",
    "i am interested in the role",
    "i am interested in the position",
    "looking forward to hearing from you",
    "please find my resume",
    "thank you for considering my application",
    "i would like to apply",
    "as discussed in our meeting",
    "per our conversation",
    "please see attached",
    "i am following up on",
    "we are pleased to offer you",
    "welcome to the team",
    "your start date is",
    "annual performance review",
    "onboarding session",
    "best regards",
    "kind regards",
    "sincerely",
]

# Load model and vectorizer once at startup
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")

model = None
vectorizer = None


def load_model():
    """Load the trained model and vectorizer."""
    global model, vectorizer
    try:
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        print(f"✓ Model loaded from {MODEL_PATH}")
        print(f"✓ Vectorizer loaded from {VECTORIZER_PATH}")
    except FileNotFoundError:
        print("⚠ Model files not found. Please run: python model/train.py")
        print(f"  Expected: {MODEL_PATH}")
        print(f"  Expected: {VECTORIZER_PATH}")


# ─── Sanitization ────────────────────────────────────────────────────────────

def sanitize_input(text):
    """
    Sanitize user input to prevent XSS and script injection.
    Preserves URLs for analysis but strips HTML tags.
    """
    if not isinstance(text, str):
        return ""
    cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)
    return cleaned.strip()


# ─── Structure Feature Extraction ─────────────────────────────────────────────

def extract_structure_features(text):
    """
    Extract structural features from email text for hybrid decision.

    Returns:
        dict with exclamation_count, uppercase_ratio, url_count,
        email_length, all_caps_words
    """
    exclamation_count = text.count("!")
    email_length = len(text)

    uppercase_ratio = 0.0
    if email_length > 0:
        uppercase_ratio = round(
            sum(1 for c in text if c.isupper()) / email_length, 3
        )

    url_count = len(extract_urls(text))
    all_caps_words = len(re.findall(r"\b[A-Z]{4,}\b", text))

    return {
        "exclamation_count": exclamation_count,
        "uppercase_ratio": uppercase_ratio,
        "url_count": url_count,
        "email_length": email_length,
        "all_caps_words": all_caps_words,
    }


# ─── Context Bias Adjustment ──────────────────────────────────────────────────

def compute_ham_bias(text_lower):
    """
    Detect strong HAM indicators and return a bias value
    that reduces spam probability for legitimate emails.

    Returns:
        float: Bias value (0.0 to max 0.25)
    """
    matches = sum(1 for phrase in HAM_INDICATORS if phrase in text_lower)
    return min(matches * 0.05, 0.25)


# ─── Hybrid Decision System ──────────────────────────────────────────────────

def hybrid_decision(spam_prob, url_analyses, structure_features, text_lower):
    """
    Combine ML prediction, URL risk, and structural signals.

    Returns:
        tuple: (adjusted_prob, label, uncertain, decision_factors)
    """
    adjusted_prob = spam_prob
    decision_factors = []

    # --- Context-based bias (HAM indicators) ---
    ham_bias = compute_ham_bias(text_lower)
    if ham_bias > 0:
        has_high_risk_url = any(a["risk"] == "HIGH" for a in url_analyses)
        if not has_high_risk_url:
            adjusted_prob = max(adjusted_prob - ham_bias, 0.01)
            decision_factors.append(f"HAM bias applied (-{ham_bias:.2f})")

    # --- URL risk signal ---
    if url_analyses:
        high_risk_count = sum(1 for a in url_analyses if a["risk"] == "HIGH")

        if high_risk_count > 0:
            url_boost = min(high_risk_count * 0.08, 0.20)
            adjusted_prob = min(adjusted_prob + url_boost, 0.99)
            decision_factors.append(f"URL risk boost (+{url_boost:.2f})")
        else:
            max_url_risk = max(a.get("risk_score", 0) for a in url_analyses)
            if max_url_risk > 20:
                url_boost = 0.04
                adjusted_prob = min(adjusted_prob + url_boost, 0.99)
                decision_factors.append(f"URL medium risk (+{url_boost:.2f})")

    # --- Structural signal ---
    excl = structure_features["exclamation_count"]
    caps_ratio = structure_features["uppercase_ratio"]
    caps_words = structure_features["all_caps_words"]

    structure_boost = 0.0
    if excl > 5:
        structure_boost += 0.03
    if caps_ratio > 0.3:
        structure_boost += 0.04
    if caps_words > 3:
        structure_boost += 0.03

    if structure_boost > 0:
        adjusted_prob = min(adjusted_prob + structure_boost, 0.99)
        decision_factors.append(f"Structure boost (+{structure_boost:.2f})")

    # --- No URLs + formal tone → reduce spam ---
    if not url_analyses and ham_bias > 0 and excl <= 2 and caps_ratio < 0.1:
        formal_reduction = 0.10
        adjusted_prob = max(adjusted_prob - formal_reduction, 0.01)
        decision_factors.append(f"Formal tone (-{formal_reduction:.2f})")

    # --- Strong context override ---
    # When multiple HAM indicators + no URLs + no exclamations + low caps
    # the email is very likely legitimate — apply stronger correction
    if ham_bias >= 0.10 and not url_analyses and excl == 0 and caps_words == 0:
        if adjusted_prob > SPAM_THRESHOLD:
            override_reduction = min(adjusted_prob - 0.30, 0.25)
            adjusted_prob = max(adjusted_prob - override_reduction, 0.10)
            decision_factors.append(f"Strong context override (-{override_reduction:.2f})")

    # --- Final decision ---
    label = "SPAM" if adjusted_prob > SPAM_THRESHOLD else "NOT SPAM"
    uncertain = 0.45 <= adjusted_prob <= 0.65

    return adjusted_prob, label, uncertain, decision_factors


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main input page."""
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check_spam():
    """
    Process email using hybrid decision system:
    ML + URL risk + structural signals + context bias.
    """
    if model is None or vectorizer is None:
        return render_template(
            "index.html", error="Model not loaded. Please train the model first."
        )

    # Get and sanitize inputs
    subject = sanitize_input(request.form.get("subject", ""))
    body = sanitize_input(request.form.get("body", ""))

    if not subject and not body:
        return render_template(
            "index.html", error="Please enter at least a subject or body."
        )

    # Input length handling
    truncated = False
    total_length = len(subject) + len(body)
    if total_length > MAX_INPUT_LENGTH:
        max_body_length = MAX_INPUT_LENGTH - len(subject)
        if max_body_length > 0:
            body = body[:max_body_length]
        else:
            subject = subject[:MAX_INPUT_LENGTH]
            body = ""
        truncated = True

    # Combine and clean text
    original_text = combine_email(subject, body)
    cleaned_text = clean_text(original_text)

    # ML prediction with calibrated probability
    text_tfidf = vectorizer.transform([cleaned_text])
    probabilities = model.predict_proba(text_tfidf)[0]
    ml_spam_prob = probabilities[1]

    # Extract structural features
    raw_text = f"{subject} {body}"
    structure_features = extract_structure_features(raw_text)

    # URL analysis
    url_analyses = analyze_all_urls(raw_text)

    # Hybrid decision
    adjusted_prob, label, uncertain, decision_factors = hybrid_decision(
        ml_spam_prob, url_analyses, structure_features, raw_text.lower()
    )

    # Confidence with cap
    if label == "SPAM":
        raw_confidence = adjusted_prob * 100
    else:
        raw_confidence = (1 - adjusted_prob) * 100
    confidence = round(min(raw_confidence, MAX_CONFIDENCE), 1)

    prediction = 1 if label == "SPAM" else 0

    # Get explanation
    explanation = get_explanation(original_text, cleaned_text, vectorizer, model)

    # Highlight text
    highlight_words = list(set(
        [kw[0] for kw in explanation["top_keywords"]]
        + explanation["spam_words_found"]
    ))

    highlighted_body = body
    if highlight_words and prediction == 1:
        highlighted_body = highlight_spam_words(body, highlight_words)
    highlighted_body = highlight_urls_in_text(highlighted_body)

    highlighted_subject = subject
    if highlight_words and prediction == 1:
        highlighted_subject = highlight_spam_words(subject, highlight_words)

    return render_template(
        "result.html",
        label=label,
        confidence=confidence,
        spam_probability=round(adjusted_prob * 100, 1),
        uncertain=uncertain,
        truncated=truncated,
        subject=subject,
        body=body,
        highlighted_subject=highlighted_subject,
        highlighted_body=highlighted_body,
        top_keywords=explanation["top_keywords"],
        spam_words=explanation["spam_words_found"],
        indicators=explanation["indicators"],
        url_analyses=explanation["url_analyses"],
        word_risk=explanation["word_risk"],
        url_risk=explanation["url_risk"],
        analytics=explanation["analytics"],
        structure_features=structure_features,
        decision_factors=decision_factors,
    )


@app.route("/api/domain-check", methods=["POST"])
def domain_check():
    """
    API endpoint for domain reputation checking.
    Does NOT store the API key.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    url = data.get("url", "").strip()
    api_key = data.get("api_key", "").strip()

    if not url:
        return jsonify({"success": False, "error": "No URL provided"}), 400
    if not api_key:
        return jsonify(
            {"success": False, "error": "No API key provided. Enter your VirusTotal API key."}
        ), 400

    result = check_domain_reputation(url, api_key)
    return jsonify(result)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_model()
    app.run(debug=True, host="0.0.0.0", port=5000)
