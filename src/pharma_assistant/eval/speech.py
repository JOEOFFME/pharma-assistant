"""Word/character edit-distance metrics; never invent recorded-audio results."""


def distance(reference: list, hypothesis: list) -> int:
    """Compute Levenshtein distance with linear memory."""
    previous = list(range(len(hypothesis) + 1))
    for i, left in enumerate(reference, 1):
        current = [i]
        for j, right in enumerate(hypothesis, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right))
            )
        previous = current
    return previous[-1]


def speech_metrics(pairs: list[tuple[str, str]]) -> dict:
    """Compute micro WER/CER after whitespace/case folding; preserve punctuation."""
    words = characters = word_errors = character_errors = 0
    if not pairs:
        raise ValueError("No recorded transcripts; WER/CER unavailable")
    for reference, hypothesis in pairs:
        reference = " ".join(reference.casefold().split())
        hypothesis = " ".join(hypothesis.casefold().split())
        words += len(reference.split())
        characters += len(reference)
        word_errors += distance(reference.split(), hypothesis.split())
        character_errors += distance(list(reference), list(hypothesis))
    if not words or not characters:
        raise ValueError("Reference transcripts must be nonempty")
    return {
        "wer": word_errors / words,
        "cer": character_errors / characters,
        "reference_words": words,
        "reference_characters": characters,
    }
