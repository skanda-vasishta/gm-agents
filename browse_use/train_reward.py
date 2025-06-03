import re, json, joblib, pathlib
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

###############################################################################
# 1) Load & parse your feedback dataset
###############################################################################
RAW_FILE = pathlib.Path("trade_feedback.txt").read_text()

# --- split on the header line you saw ("=== Trade Evaluation ... ===") ----------
blocks = [b.strip() for b in re.split(r"=== Trade Evaluation .*? ===", RAW_FILE) if b.strip()]
records = []
for b in blocks:
    # a) full natural-language description (state + action)
    description = b.split("AI Decision")[0].strip()
    
    # b) human label (yes = good trade, no = bad trade) --------------------------
    m = re.search(r"User Feedback:\s*(yes|no)", b, re.I)
    label = 1 if (m and m.group(1).lower() == "yes") else 0
    
    records.append({"text": description, "label": label})

print(f"Parsed {len(records)} labelled trades.")

###############################################################################
# 2) Prepare data for ML
###############################################################################
texts  = [r["text"]   for r in records]
labels = [r["label"]  for r in records]

###############################################################################
# 3) Define pipeline TF-IDF  →  LogisticRegression
###############################################################################
clf = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=20_000,
                              ngram_range=(1,2),
                              stop_words="english")),
    ("lr",    LogisticRegression(max_iter=400, C=3.0))
])

###############################################################################
# 4) Train / evaluate quickly
###############################################################################
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, stratify=labels, random_state=42)

clf.fit(X_train, y_train)
print(f"Test accuracy  : {clf.score(X_test, y_test):.3f}")
print(f"5-fold CV mean : {cross_val_score(clf, texts, labels, cv=5).mean():.3f}")

###############################################################################
# 5) Save the reward model
###############################################################################
joblib.dump(clf, "reward_model.pkl")
print("Reward model saved to reward_model.pkl") 