"""Unicode normalization with a map back to original code-point intervals."""

import re
import unicodedata
from dataclasses import dataclass

ARABIZI = str.maketrans(
    {"2": "ء", "3": "ع", "5": "خ", "6": "ط", "7": "ح", "8": "غ", "9": "ق"}
)
ARABIC = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        **{chr(0x660 + i): str(i) for i in range(10)},
    }
)


@dataclass(frozen=True)
class NormalizedText:
    """Normalized evidence and each character's original half-open interval."""

    text: str
    spans: tuple[tuple[int, int], ...]

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        """Map a nonempty normalized interval back to original text."""
        if not 0 <= start < end <= len(self.spans):
            raise ValueError("Invalid normalized interval")
        return self.spans[start][0], self.spans[end - 1][1]


def normalize(text: str, *, arabizi: bool = True) -> NormalizedText:
    """Fold marks/alef/ya, punctuation and 3+ repetitions; preserve numeric units."""
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, original in enumerate(text):
        for char in unicodedata.normalize("NFKD", original).casefold():
            if unicodedata.category(char).startswith("M") or char == "ـ":
                if spans:
                    spans[-1] = (spans[-1][0], index + 1)
                continue
            char = char.translate(ARABIC)
            char = char if char.isalnum() else " "
            if char == " " and (not chars or chars[-1] == " "):
                if spans and chars[-1] == " ":
                    spans[-1] = (spans[-1][0], index + 1)
                continue
            chars.append(char)
            spans.append((index, index + 1))
    while chars and chars[-1] == " ":
        chars.pop()
        spans.pop()
    if arabizi:
        for match in re.finditer(r"[a-z0-9]+", "".join(chars)):
            token = match.group()
            numeric_unit = re.fullmatch(r"\d+(?:mg|g|mcg|ml|iu|ui)", token)
            if re.search("[a-z]", token) and not numeric_unit:
                for i in range(match.start(), match.end()):
                    chars[i] = chars[i].translate(ARABIZI)
    output: list[str] = []
    mapping: list[tuple[int, int]] = []
    for char, span in zip(chars, spans, strict=True):
        if len(output) >= 2 and char.isalpha() and output[-1] == output[-2] == char:
            mapping[-1] = (mapping[-1][0], span[1])
        else:
            output.append(char)
            mapping.append(span)
    return NormalizedText("".join(output), tuple(mapping))
