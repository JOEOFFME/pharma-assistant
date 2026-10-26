"""Evidence-only baseline extraction from reference names and generic patterns."""

import re
from collections import defaultdict
from pathlib import Path

from pharma_assistant.data_tools.nlu_dataset import read_jsonl
from pharma_assistant.matching.medications import MedicationIndex
from pharma_assistant.nlp.normalize import NormalizedText, normalize


def term_matches(
    text: str, terms: set[str], *, enabled: bool = True
) -> list[tuple[int, int]]:
    """Match normalized token windows and map them to original source offsets."""
    folded = normalize(text, arabizi=False)
    if not enabled:
        letters = [
            (folded_char, (i, i + 1))
            for i, char in enumerate(text)
            for folded_char in char.casefold()
        ]
        folded = NormalizedText(
            "".join(c for c, _ in letters), tuple(s for _, s in letters)
        )
    tokens = list(re.finditer(r"\w+", folded.text))
    spans = []
    for i in range(len(tokens)):
        for count in range(min(4, len(tokens) - i), 0, -1):
            first, last = tokens[i], tokens[i + count - 1]
            value = folded.text[first.start() : last.end()]
            start, end = folded.original_span(first.start(), last.end())
            if value in terms:
                spans.append((start, end))
                break
            # Arabic clitics are not part of a named entity.
            if count == 1 and value[:1] in "وفبل" and value[1:] in terms:
                spans.append(folded.original_span(first.start() + 1, last.end()))
                break
    return sorted(set(spans), key=lambda p: (p[0], -(p[1] - p[0])))


class EntityExtractor:
    """Initialize once; never load draft/gold files or infer medication facts."""

    def __init__(
        self, index: MedicationIndex, config: dict, seed_path: Path, cities: dict
    ) -> None:
        self.index = index
        self.config = config
        self.names: set[str] = set()
        self.places = {normalize(city, arabizi=False).text for city in cities}
        for row in read_jsonl(seed_path):
            for entity in row["entities"]:
                if entity["type"] == "MEDICATION":
                    self.names.add(normalize(entity["text"], arabizi=False).text)
                if entity["type"] == "LOCATION":
                    self.places.add(normalize(entity["text"], arabizi=False).text)
        for record in index.records.values():
            # Full specialty names may include strength; only short name aliases here.
            for alias in record.aliases:
                value = normalize(alias.text, arabizi=False).text
                if (
                    value
                    and len(value) >= 4
                    and not any(c.isdigit() for c in value)
                    and len(value.split()) <= 4
                ):
                    self.names.add(value)
        self.names -= {
            normalize(p, arabizi=False).text
            for phrases in config["rules"].values()
            for p in phrases
        }

    def extract(self, text: str) -> tuple[list[dict], list[dict], bool]:
        """Extract non-overlapping spans, local attributes and conservative matches."""
        entities: list[dict] = []
        links: list[tuple[dict, dict]] = []
        clarify = False

        def add(kind: str, start: int, end: int, **fields: object) -> dict | None:
            if any(start < e["end"] and e["start"] < end for e in entities):
                return None
            entity = {
                "type": kind,
                "text": text[start:end],
                "start": start,
                "end": end,
                **fields,
            }
            entities.append(entity)
            return entity

        # First claim names/locations, preventing common pharmacy words as medicines.
        for start, end in term_matches(
            text, self.places, enabled=self.config.get("normalize_entities", True)
        ):
            add("LOCATION", start, end)
        generic = {
            "la",
            "le",
            "de",
            "garde",
            "plus",
            "proche",
            "est",
            "ouverte",
            "ouvert",
            "في",
            "قريبة",
            "الحراسة",
            "ديال",
            "مسدودة",
            "دابا",
            "à",
            "a",
            "f",
        }
        for match in re.finditer(
            r"(?:\bpharmacie\b|صيدلية)\s+([^?؟!,;:]+)", text, re.I
        ):
            words = list(re.finditer(r"\S+", match[1]))
            selected = []
            for word in words[:4]:
                if normalize(word.group(), arabizi=False).text in generic:
                    break
                selected.append(word)
            if selected:
                add(
                    "PHARMACY_NAME",
                    match.start(1) + selected[0].start(),
                    match.start(1) + selected[-1].end(),
                )
        for start, end in term_matches(
            text, self.names, enabled=self.config.get("normalize_entities", True)
        ):
            add("MEDICATION", start, end)
        medications = sorted(
            [e for e in entities if e["type"] == "MEDICATION"], key=lambda e: e["start"]
        )
        strength = re.compile(
            r"\s*(?P<span>\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?(?:\s*(?P<unit>mg/mL|g/L|mcg|mg|g|ملغ|غ|%|IU))?)(?!\w)",
            re.I,
        )
        for med in medications:
            match = strength.match(text, med["end"])
            dosage = None
            if match:
                unit = match["unit"]
                fields = {}
                scalar = re.match(r"\d+(?:[.,]\d+)?", match["span"]).group()
                if (
                    unit
                    and "/" not in match["span"].split(unit)[0]
                    and float(scalar.replace(",", ".")) > 0
                ):
                    canonical_unit = {
                        "غ": "g",
                        "ملغ": "mg",
                        "mg/ml": "mg/mL",
                        "g/l": "g/L",
                        "iu": "IU",
                    }.get(unit.lower(), unit.lower())
                    fields = {
                        "value": float(
                            re.match(r"\d+(?:[.,]\d+)?", match["span"])
                            .group()
                            .replace(",", ".")
                        ),
                        "unit": canonical_unit,
                    }
                dosage = add("DOSAGE", *match.span("span"), **fields)
                if dosage:
                    links.append((dosage, med))
                    clarify |= not bool(fields)
            query = med["text"] + (" " + dosage["text"] if dosage else "")
            candidates = (
                self.index.search(query, k=3)
                if self.config.get("resolve_medications", True)
                else []
            )
            if (
                candidates
                and candidates[0].score >= self.config["match_threshold"]
                and not candidates[0].needs_clarification
            ):
                winner = candidates[0].medication
                med.update(normalized=winner.brand_name, matched_id=winner.id)
                if winner.dci:
                    med["dci"] = winner.dci
            else:
                clarify = True
        units = self.config["quantity_units"]
        packages = "|".join(re.escape(p) for p in sorted(units, key=len, reverse=True))
        for match in re.finditer(
            rf"(?<![\w.,/+-])(?P<qty>[1-9]\d*\s+(?P<unit>{packages}))(?!\w)", text, re.I
        ):
            add(
                "QUANTITY",
                *match.span("qty"),
                value=int(re.match(r"\d+", match["qty"]).group()),
                unit=units[match["unit"].lower()],
            )
        for match in re.finditer("علبتين|علبتان", text):
            add("QUANTITY", *match.span(), value=2, unit="box")
        for kind, key in [
            ("FORM", "forms"),
            ("TIME_REF", "times"),
            ("URGENCY", "urgency"),
        ]:
            terms = {
                normalize(term, arabizi=False).text: term for term in self.config[key]
            }
            for start, end in term_matches(
                text, set(terms), enabled=self.config.get("normalize_entities", True)
            ):
                folded = normalize(text[start:end], arabizi=False).text
                value = (
                    "urgent" if kind == "URGENCY" else self.config[key][terms[folded]]
                )
                add(kind, start, end, normalized=value)
        for entity in entities.copy():
            if entity["type"] not in {"QUANTITY", "FORM"}:
                continue
            # Attach within the local noun phrase; shared counts remain unresolved.
            following = [
                m
                for m in medications
                if m["start"] >= entity["end"]
                and re.fullmatch(
                    r"\s*(?:(?:de|d['’]|dyal|ديال|من|en)\s*)?",
                    text[entity["end"] : m["start"]],
                    re.I,
                )
            ]
            if len(following) == 1:
                links.append((entity, following[0]))
            elif len(medications) == 1:
                links.append((entity, medications[0]))
            else:
                clarify = True
        counters: dict[str, int] = defaultdict(int)
        entities.sort(key=lambda e: e["start"])
        for entity in entities:
            counters[entity["type"]] += 1
            entity["entity_id"] = entity["type"].lower() + str(counters[entity["type"]])
        relations = []
        for entity, med in links:
            entity["medication_ref"] = med["entity_id"]
            if entity["type"] in {"DOSAGE", "QUANTITY"}:
                relations.append(
                    {
                        "type": entity["type"] + "_OF",
                        "from": entity["entity_id"],
                        "to": med["entity_id"],
                    }
                )
        return entities, relations, clarify
