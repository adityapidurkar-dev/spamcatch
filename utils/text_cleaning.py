"""
Spamerno - Text Cleaning Module
Handles text preprocessing, tokenization, and keyword extraction.
"""

import re
import string
import numpy as np


def clean_text(text):
    """
    Clean and preprocess text for ML prediction.

    Steps:
        1. Lowercase
        2. Remove punctuation
        3. Remove extra whitespace

    Args:
        text (str): Raw input text

    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def combine_email(subject, body):
    """
    Combine email subject and body into one text field.
    Subject is repeated for increased weighting in the model.

    Args:
        subject (str): Email subject line
        body (str): Email body text

    Returns:
        str: Combined text with subject weighted
    """
    subject = subject.strip() if isinstance(subject, str) else ""
    body = body.strip() if isinstance(body, str) else ""
    # Subject weighting: repeat subject to increase its importance
    return f"{subject} {subject} {body}".strip()


def tokenize(text):
    """
    Simple whitespace tokenizer.

    Args:
        text (str): Input text

    Returns:
        list: List of tokens
    """
    if not isinstance(text, str):
        return []
    return text.split()


def extract_top_keywords(text, vectorizer, model, top_n=10):
    """
    Extract top contributing spam keywords with their TF-IDF scores.

    Uses the model's feature log probabilities to find which words
    contribute most to the spam classification.

    Args:
        text (str): Cleaned input text
        vectorizer: Fitted TfidfVectorizer
        model: Fitted MultinomialNB model
        top_n (int): Number of top keywords to return

    Returns:
        list: List of tuples (word, score) sorted by contribution
    """
    try:
        # Get TF-IDF vector for the input text
        text_tfidf = vectorizer.transform([text])

        # Get feature names
        feature_names = vectorizer.get_feature_names_out()

        # Get the base NB model's log probabilities
        # Handle both raw MultinomialNB and CalibratedClassifierCV wrapper
        if hasattr(model, "feature_log_prob_"):
            # Direct MultinomialNB
            base_nb = model
        elif hasattr(model, "calibrated_classifiers_"):
            # CalibratedClassifierCV — extract the base estimator
            base_nb = model.calibrated_classifiers_[0].estimator
        else:
            return []

        spam_log_probs = base_nb.feature_log_prob_[1]  # spam class
        ham_log_probs = base_nb.feature_log_prob_[0]   # ham class

        # Calculate the difference (spam - ham) to find spam-indicative words
        log_prob_diff = spam_log_probs - ham_log_probs

        # Get non-zero features in the input text
        non_zero_indices = text_tfidf.nonzero()[1]

        if len(non_zero_indices) == 0:
            return []

        # Calculate contribution scores for words in the input
        word_scores = []
        for idx in non_zero_indices:
            word = feature_names[idx]
            tfidf_weight = text_tfidf[0, idx]
            spam_contribution = log_prob_diff[idx] * tfidf_weight
            if spam_contribution > 0:  # Only include spam-indicative words
                word_scores.append((word, round(float(spam_contribution), 4)))

        # Sort by score descending
        word_scores.sort(key=lambda x: x[1], reverse=True)

        return word_scores[:top_n]

    except Exception:
        return []


def get_word_count(text):
    """
    Get total word count of text.

    Args:
        text (str): Input text

    Returns:
        int: Word count
    """
    return len(tokenize(text))
