import os
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
INTENTS_PATH = BASE_DIR / "nlu" / "intents.json"

class IntentClassifier:
    def __init__(self):
        self.pipeline = None
        self.classes = []
        self._train()

    def _train(self):
        with open(INTENTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        X = []
        y = []
        for intent in data["intents"]:
            tag = intent["tag"]
            for pattern in intent["patterns"]:
                X.append(pattern.lower().strip())
                y.append(tag)

        # Pipeline TF-IDF (1-2 gram) + LinearSVC
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, max_features=3000)),
            ("clf", LinearSVC(C=1.0, random_state=42, dual='auto'))
        ])
        self.pipeline.fit(X, y)
        self.classes = self.pipeline.named_steps["clf"].classes_

    def predict(self, text: str) -> tuple[str, float]:
        """
        Memprediksi tag intent dan skor estimasi kecocokan (confidence).
        Latency < 5ms.
        """
        text_clean = text.lower().strip()
        if not text_clean:
            return "help", 0.0

        decision = self.pipeline.decision_function([text_clean])[0]
        if len(self.classes) == 2:
            pred_idx = int(decision > 0)
            confidence = abs(decision)
        else:
            # Softmax sederhana untuk estimasi confidence
            exp_scores = np.exp(decision - np.max(decision))
            probs = exp_scores / np.sum(exp_scores)
            pred_idx = np.argmax(probs)
            confidence = float(probs[pred_idx])

        predicted_intent = self.classes[pred_idx]
        return predicted_intent, round(confidence, 3)

# Global singleton classifier
classifier = IntentClassifier()

def get_intent(text: str) -> tuple[str, float]:
    return classifier.predict(text)
