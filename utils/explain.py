"""
Spamerno - Explainability Module
Provides explainable AI output: spam indicators, highlighted text, and analytics.
"""

import re
from utils.text_cleaning import extract_top_keywords, get_word_count
from utils.url_analysis import extract_urls, analyze_all_urls, get_overall_url_risk


# Common spam indicator words (used for general detection)
SPAM_INDICATOR_WORDS = {
    "free", "win", "winner", "won", "prize", "congratulations", "claim",
    "urgent", "immediately", "act", "now", "limited", "offer", "bonus",
    "click", "verify", "account", "password", "login", "suspend",
    "expire", "deal", "discount", "guaranteed", "cash", "money",
    "earn", "income", "million", "dollar", "lottery", "selected",
    "promo", "exclusive", "final", "notice", "reward", "approval",
    "fast", "instant", "slots"
}


def get_explanation(text, cleaned_text, vectorizer, model):
    """
    Generate a full explanation of the spam prediction.

    Returns structured data for rendering in the UI:
        - Top contributing keywords with scores
        - Spam indicators (suspicious keywords, URLs, structure)
        - Risk levels for words and URLs
        - Analytics breakdown

    Args:
        text (str): Original (unsanitized) text for URL extraction
        cleaned_text (str): Cleaned text for model analysis
        vectorizer: Fitted TfidfVectorizer
        model: Fitted MultinomialNB

    Returns:
        dict: Explanation data
    """
    # Get top keywords with scores
    top_keywords = extract_top_keywords(cleaned_text, vectorizer, model, top_n=15)

    # Find spam words present in the text
    text_lower = cleaned_text.lower()
    words_in_text = set(text_lower.split())
    spam_words_found = [w for w in words_in_text if w in SPAM_INDICATOR_WORDS]

    # URL analysis
    url_analyses = analyze_all_urls(text)
    urls_found = extract_urls(text)
    url_risk = get_overall_url_risk(url_analyses)

    # Indicators
    indicators = []

    if spam_words_found:
        indicators.append({
            "type": "Suspicious Keywords",
            "detail": f"Found {len(spam_words_found)} spam-associated words",
            "words": spam_words_found[:10]
        })

    if urls_found:
        high_risk_urls = [a for a in url_analyses if a["risk"] == "HIGH"]
        med_risk_urls = [a for a in url_analyses if a["risk"] == "MEDIUM"]

        url_detail = f"Found {len(urls_found)} URL(s)"
        if high_risk_urls:
            url_detail += f", {len(high_risk_urls)} HIGH risk"
        if med_risk_urls:
            url_detail += f", {len(med_risk_urls)} MEDIUM risk"

        indicators.append({
            "type": "Suspicious URLs",
            "detail": url_detail,
            "urls": urls_found
        })

    # Check structure abnormalities
    structure_issues = check_structure(text)
    if structure_issues:
        indicators.append({
            "type": "Abnormal Structure",
            "detail": "; ".join(structure_issues)
        })

    # Calculate word risk level
    word_risk = calculate_word_risk(len(spam_words_found), get_word_count(cleaned_text))

    # Analytics
    total_words = get_word_count(cleaned_text)
    spam_word_count = len(spam_words_found)
    url_count = len(urls_found)

    # Spam contribution breakdown
    word_contribution, url_contribution = calculate_contribution(
        spam_word_count, total_words, url_analyses
    )

    return {
        "top_keywords": top_keywords,
        "spam_words_found": spam_words_found,
        "indicators": indicators,
        "url_analyses": url_analyses,
        "word_risk": word_risk,
        "url_risk": url_risk,
        "analytics": {
            "total_words": total_words,
            "spam_word_count": spam_word_count,
            "url_count": url_count,
            "word_contribution": word_contribution,
            "url_contribution": url_contribution,
        }
    }


def check_structure(text):
    """
    Check for structural abnormalities common in spam emails.

    Args:
        text (str): Original text

    Returns:
        list: List of structure issue descriptions
    """
    issues = []

    # Excessive uppercase
    if len(text) > 20:
        upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if upper_ratio > 0.4:
            issues.append("Excessive uppercase characters")

    # Excessive exclamation marks
    excl_count = text.count("!")
    if excl_count > 5:
        issues.append(f"Excessive exclamation marks ({excl_count})")

    # Excessive repeated punctuation
    if re.search(r"[!?]{3,}", text):
        issues.append("Repeated punctuation patterns")

    # All caps words
    all_caps_words = re.findall(r"\b[A-Z]{4,}\b", text)
    if len(all_caps_words) > 3:
        issues.append(f"Multiple all-caps words ({len(all_caps_words)})")

    return issues


def calculate_word_risk(spam_word_count, total_words):
    """
    Calculate word-based risk level.

    Args:
        spam_word_count (int): Number of spam words found
        total_words (int): Total word count

    Returns:
        str: Risk level (LOW/MEDIUM/HIGH)
    """
    if total_words == 0:
        return "LOW"

    ratio = spam_word_count / total_words

    if spam_word_count >= 5 or ratio > 0.15:
        return "HIGH"
    elif spam_word_count >= 2 or ratio > 0.08:
        return "MEDIUM"
    return "LOW"


def calculate_contribution(spam_word_count, total_words, url_analyses):
    """
    Calculate percentage contribution of words and URLs to spam score.

    Args:
        spam_word_count (int): Number of spam words
        total_words (int): Total words
        url_analyses (list): URL analysis results

    Returns:
        tuple: (word_contribution_pct, url_contribution_pct)
    """
    word_score = min(spam_word_count * 10, 80)  # Cap at 80

    url_score = 0
    for analysis in url_analyses:
        if analysis["risk"] == "HIGH":
            url_score += 30
        elif analysis["risk"] == "MEDIUM":
            url_score += 15
        else:
            url_score += 5

    url_score = min(url_score, 80)  # Cap at 80

    total_score = word_score + url_score
    if total_score == 0:
        return 0, 0

    word_pct = round((word_score / total_score) * 100)
    url_pct = round((url_score / total_score) * 100)

    return word_pct, url_pct


def highlight_spam_words(text, spam_words):
    """
    Wrap spam words in the text with <mark> tags for red highlighting.

    Args:
        text (str): Original text
        spam_words (list): List of spam words to highlight

    Returns:
        str: HTML string with highlighted words
    """
    if not spam_words or not text:
        return text

    # Create a set of words to highlight (lowercase)
    highlight_set = set(w.lower() for w in spam_words)

    # Also add top keyword words (they come as tuples)
    if isinstance(spam_words[0], tuple):
        highlight_set = set(w[0].lower() for w in spam_words)

    def replace_word(match):
        word = match.group(0)
        if word.lower() in highlight_set:
            return f'<mark class="spam-highlight">{word}</mark>'
        return word

    # Match whole words
    result = re.sub(r'\b\w+\b', replace_word, text)
    return result


def highlight_urls_in_text(text):
    """
    Make URLs in text clickable and underlined.

    Args:
        text (str): Text possibly containing URLs

    Returns:
        str: HTML string with clickable URLs
    """
    url_pattern = r'(https?://[^\s<>\"\')\],;]+)'

    def make_link(match):
        url = match.group(1)
        return f'<a href="{url}" class="url-highlight" target="_blank" rel="noopener noreferrer">{url}</a>'

    return re.sub(url_pattern, make_link, text)
