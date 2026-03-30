"""
Spamerno - ML Training Script
Trains a TF-IDF + Multinomial Naive Bayes model for spam detection.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.naive_bayes import MultinomialNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import re
import string


def get_custom_stopwords():
    """
    Build a custom stopword list from sklearn's English stopwords.
    Keeps important negation words ('not', 'no') that affect spam context.
    """
    # Words to KEEP (remove from stopword list)
    keep_words = {"not", "no", "never", "neither", "nor", "none", "nothing"}

    custom_stopwords = list(ENGLISH_STOP_WORDS - keep_words)
    return custom_stopwords


def clean_text(text):
    """Preprocess text: lowercase, remove punctuation, strip extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def train_model():
    """Train the spam detection model using dataset/spam.csv."""

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    dataset_path = os.path.join(project_dir, "dataset", "spam.csv")
    model_path = os.path.join(script_dir, "model.pkl")
    vectorizer_path = os.path.join(script_dir, "vectorizer.pkl")

    # Load dataset
    print(f"Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found at {dataset_path}")
        sys.exit(1)

    df = pd.read_csv(dataset_path)
    print(f"Dataset loaded: {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"Label distribution:\n{df['label'].value_counts()}")

    # Map labels: spam -> 1, ham -> 0
    df["label_encoded"] = df["label"].map({"spam": 1, "ham": 0})

    # Drop any rows with missing labels
    df = df.dropna(subset=["label_encoded"])
    df["label_encoded"] = df["label_encoded"].astype(int)

    # Combine subject + body with subject weighting
    df["subject"] = df["subject"].fillna("")
    df["body"] = df["body"].fillna("")
    # Subject repeated for increased importance (matches prediction pipeline)
    df["combined_text"] = df["subject"] + " " + df["subject"] + " " + df["body"]

    # Clean text
    df["cleaned_text"] = df["combined_text"].apply(clean_text)

    # Remove empty rows
    df = df[df["cleaned_text"].str.len() > 0]
    print(f"After cleaning: {len(df)} rows")

    # Split data
    X = df["cleaned_text"]
    y = df["label_encoded"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # TF-IDF Vectorization with custom stopwords
    custom_stopwords = get_custom_stopwords()
    print(f"Custom stopwords: {len(custom_stopwords)} words (kept negation words)")

    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=custom_stopwords,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")

    # Train Multinomial Naive Bayes with Calibration
    base_model = MultinomialNB(alpha=0.1)

    # Wrap with CalibratedClassifierCV for better-calibrated probabilities
    model = CalibratedClassifierCV(
        base_model,
        method="sigmoid",
        cv=5,
    )
    model.fit(X_train_tfidf, y_train)
    print("Model trained with CalibratedClassifierCV (sigmoid, 5-fold)")

    # Evaluate
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*50}")
    print(f"Model Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"{'='*50}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Ham", "Spam"]))
    print(f"Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Test calibrated probabilities
    sample_proba = model.predict_proba(X_test_tfidf[:5])
    print(f"\nCalibrated probabilities (first 5 test samples):")
    for i, proba in enumerate(sample_proba):
        print(f"  Sample {i+1}: Ham={proba[0]:.4f}, Spam={proba[1]:.4f}")

    # Save model and vectorizer
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    print(f"\nModel saved to: {model_path}")
    print(f"Vectorizer saved to: {vectorizer_path}")
    print("\nTraining complete!")


if __name__ == "__main__":
    train_model()
