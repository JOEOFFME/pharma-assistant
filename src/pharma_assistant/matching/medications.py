"""Hybrid name retrieval with similarity scores, not medical probabilities."""

import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from pydantic import BaseModel
from rapidfuzz import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer

from pharma_assistant.data.medications import MedicationRecord, MedicationRepository
from pharma_assistant.data_tools.medication_names import basic_normalize, phonetic_key


def strength_tokens(text: str) -> set[tuple[float, str, str]]:
    """Compare stated amounts while keeping concentrations separate."""
    text = basic_normalize(text)
    text = re.sub(r"pour\s+cent", "%", text)
    values = set()
    pattern = (
        r"(\d+(?:[.,]\d+)?)\s*(microgrammes?|mcg|mg|g|ui|%)"
        r"(?:\s*/\s*(\d+(?:[.,]\d+)?)?\s*(ml|l))?(?=$|[^a-z])"
    )
    for match in re.finditer(pattern, text):
        value = float(match[1].replace(",", "."))
        unit = match[2]
        if unit == "g":
            value, unit = value * 1000, "mg"
        if unit in {"mcg", "microgramme", "microgrammes"}:
            value, unit = value / 1000, "mg"
        denominator = ""
        if match[4]:
            denominator = f"/{float((match[3] or '1').replace(',', '.')):g}{match[4]}"
        values.add((round(value, 9), unit, denominator))
    return values


def name_query(text: str) -> str:
    """Remove strength numbers from name scoring without discarding form words."""
    text = phonetic_key(text)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:mg|g|mcg|ml|ui|%)?", " ", text)
    return " ".join(text.split())


class MedicationCandidate(BaseModel):
    """A catalogue candidate with uncertainty preserved for ambiguous families."""

    medication: MedicationRecord
    score: float
    name_score: float
    tfidf_score: float
    matched_alias: str
    alias_synthetic: bool
    strength_match: bool | None
    needs_clarification: bool = False


class MedicationIndex:
    """RapidFuzz and character n-gram TF-IDF with explicit strength/form constraints."""

    def __init__(self, records: list[MedicationRecord], config: dict) -> None:
        weights = config["fuzzy_weight"], config["tfidf_weight"]
        if (
            any(not 0 <= weight <= 1 for weight in weights)
            or abs(sum(weights) - 1) > 1e-9
        ):
            raise ValueError("Matching weights must be nonnegative and sum to one")
        if (
            not 0 < config["min_name_score"] <= 1
            or not 0 <= config["ambiguity_margin"] <= 1
        ):
            raise ValueError("Matching thresholds must lie in [0,1]")
        if (
            type(config["retrieval_aliases"]) is not int
            or config["retrieval_aliases"] < 1
        ):
            raise ValueError("retrieval_aliases must be a positive integer")
        self.records = {row.id: row for row in records}
        if len(self.records) != len(records):
            raise ValueError("Duplicate medication IDs")
        self.config = config
        self.aliases: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)
        for row in records:
            for alias in row.aliases:
                key = name_query(alias.text)
                if key:
                    self.aliases[key].append((row.id, alias.text, alias.synthetic))
        self.keys = sorted(self.aliases)
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(config["char_ngram_min"], config["char_ngram_max"]),
            lowercase=False,
            dtype=np.float32,
        )
        self.matrix = self.vectorizer.fit_transform(self.keys) if self.keys else None

    @classmethod
    def from_database(cls, path: Path, config: dict) -> "MedicationIndex":
        """Build the in-memory index from typed, provenance-bearing records."""
        return cls(MedicationRepository(path).all(), config)

    def search(self, query: str, k: int = 3) -> list[MedicationCandidate]:
        """Return ranked candidates, or none when constraints cannot match."""
        if type(k) is not int or not 1 <= k <= 100:
            raise ValueError("k must be an integer from 1 to 100")
        if not isinstance(query, str) or len(query) > 500:
            raise ValueError("query must be text of at most 500 code points")
        needle = name_query(query)
        if not needle or self.matrix is None:
            return []
        similarities = (
            (self.matrix @ self.vectorizer.transform([needle]).T).toarray().ravel()
        )
        count = min(int(self.config["retrieval_aliases"]), len(self.keys))
        positions = np.argsort(similarities, kind="stable")[-count:]
        retrieved = {
            self.keys[int(index)]: float(similarities[index]) for index in positions
        }
        for key, _, position in process.extract(
            needle, self.keys, scorer=fuzz.WRatio, limit=count
        ):
            retrieved[key] = float(similarities[position])
        required = strength_tokens(query)
        numbers = set(re.findall(r"\b\d+(?:[.,]\d+)?\b", basic_normalize(query)))
        explicit_forms = {
            word
            for word in [
                "comprime",
                "gelule",
                "sirop",
                "suppositoire",
                "suspension",
                "pommade",
                "creme",
            ]
            if word in basic_normalize(query)
        }
        best: dict[str, MedicationCandidate] = {}
        for key, cosine in retrieved.items():
            fuzzy = fuzz.WRatio(needle, key) / 100
            if fuzzy < float(self.config["min_name_score"]):
                continue
            score = (
                self.config["fuzzy_weight"] * fuzzy
                + self.config["tfidf_weight"] * cosine
            )
            for identifier, alias, synthetic in self.aliases[key]:
                row = self.records[identifier]
                available = strength_tokens(row.full_name)
                if required and not required.issubset(available):
                    continue
                if not required and numbers:
                    source_numbers = set(
                        re.findall(
                            r"\b\d+(?:[.,]\d+)?\b", basic_normalize(row.full_name)
                        )
                    )
                    if not numbers.issubset(source_numbers):
                        continue
                if explicit_forms and not all(
                    form in basic_normalize(row.form or "") for form in explicit_forms
                ):
                    continue
                candidate = MedicationCandidate(
                    medication=row,
                    score=round(float(score), 6),
                    name_score=round(fuzzy, 6),
                    tfidf_score=round(cosine, 6),
                    matched_alias=alias,
                    alias_synthetic=synthetic,
                    strength_match=True if required else None,
                )
                previous = best.get(identifier)
                if previous is None or (candidate.score, not synthetic, alias) > (
                    previous.score,
                    not previous.alias_synthetic,
                    previous.matched_alias,
                ):
                    best[identifier] = candidate
        ranked = sorted(
            best.values(), key=lambda item: (-item.score, item.medication.id)
        )
        ambiguous = len(ranked) > 1 and ranked[0].score - ranked[1].score < float(
            self.config["ambiguity_margin"]
        )
        for candidate in ranked[:k]:
            candidate.needs_clarification = ambiguous
        return ranked[:k]
