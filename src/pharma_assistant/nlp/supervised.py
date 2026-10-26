"""Reproducible small-data intent and BIO NER baselines; no gold-file access."""

import pickle
import re
from pathlib import Path

from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


def tokens(text: str) -> list[re.Match]:
    """Tokenize original code points, retaining evidence offsets."""
    return list(re.finditer(r"\w+|[^\w\s]", text))


def features(words: list[re.Match], i: int) -> dict:
    """Use local lexical/context features without annotations or reference answers."""
    word = words[i].group()
    return {
        "word": word.casefold(),
        "prefix": word[:3].casefold(),
        "suffix": word[-3:].casefold(),
        "digit": word.isdigit(),
        "capital": word[0].isupper(),
        "prev": words[i - 1].group().casefold() if i else "BOS",
        "next": words[i + 1].group().casefold() if i + 1 < len(words) else "EOS",
    }


class SupervisedNLU:
    """Train only on explicit train rows; evaluation is performed by the caller."""

    def __init__(self, analyzer: str = "char_wb", seed: int = 42) -> None:
        self.intent = make_pipeline(
            TfidfVectorizer(
                analyzer=analyzer,
                ngram_range=(3, 5) if analyzer == "char_wb" else (1, 2),
            ),
            LogisticRegression(max_iter=400, random_state=seed),
        )
        self.ner = make_pipeline(
            DictVectorizer(), LogisticRegression(max_iter=400, random_state=seed)
        )

    def fit(self, rows: list[dict]) -> None:
        """Fit intent and BIO classification with exact annotation alignment."""
        self.intent.fit([r["text"] for r in rows], [r["intent"] for r in rows])
        x, y = [], []
        for row in rows:
            words = tokens(row["text"])
            for i, word in enumerate(words):
                entity = next(
                    (
                        e
                        for e in row["entities"]
                        if e["start"] <= word.start() and word.end() <= e["end"]
                    ),
                    None,
                )
                label = (
                    "O"
                    if entity is None
                    else ("B-" if word.start() == entity["start"] else "I-")
                    + entity["type"]
                )
                x.append(features(words, i))
                y.append(label)
        self.ner.fit(x, y)

    def predict(self, text: str) -> dict:
        """Decode BIO spans; these raw proposals are evaluated before API admission."""
        probabilities = self.intent.predict_proba([text])[0]
        position = probabilities.argmax()
        words = tokens(text)
        tags = (
            self.ner.predict([features(words, i) for i in range(len(words))])
            if words
            else []
        )
        entities = []
        for word, tag in zip(words, tags, strict=True):
            if tag == "O":
                continue
            kind = tag[2:]
            if (
                tag.startswith("I-")
                and entities
                and entities[-1]["type"] == kind
                and (
                    not text[entities[-1]["end"] : word.start()]
                    or text[entities[-1]["end"] : word.start()].isspace()
                )
            ):
                entities[-1]["end"] = word.end()
                entities[-1]["text"] = text[entities[-1]["start"] : word.end()]
            else:
                entities.append(
                    {
                        "type": kind,
                        "text": word.group(),
                        "start": word.start(),
                        "end": word.end(),
                    }
                )
        return {
            "input": {"raw_text": text},
            "intent": {
                "label": str(self.intent.classes_[position]),
                "confidence": float(probabilities[position]),
            },
            "entities": entities,
        }

    def save(self, path: Path) -> None:
        """Store a trusted local model only; never unpickle downloaded uploads."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(self, protocol=5))
