"""Named pharmacy and dated duty requests must not degrade to a generic city list."""

import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import phonenumbers


def plain(text):
    """Fold accents for matching public place names and date words."""
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )


def today():
    """Resolve relative dates in Morocco."""
    return datetime.now(ZoneInfo("Africa/Casablanca")).date()


def lookup_request(baseline, text, history=None):
    """Resolve only explicit named contacts/duty intent and user-supplied cities."""
    users = [t["text"] for t in (history or []) if t["role"] == "user"]
    candidates = [text] + list(reversed(users))
    city = None
    for candidate in candidates:
        city = next(
            (
                e.text
                for e in baseline.analyze(candidate).entities
                if e.type == "LOCATION"
            ),
            None,
        )
        if city:
            break
    duty = bool(re.search(r"\bgardes?\b|حراسة|مناوبة", text, re.I))
    contact = bool(
        re.search(r"contact|t[eé]l[eé]phone|num[eé]ro|نمرة|هاتف", text, re.I)
    )
    query_text = text
    # A location-only answer continues the preceding named-contact request.
    if not duty and not contact and city and len(text.split()) <= 10:
        previous = next(
            (
                q
                for q in reversed(users[-2:])
                if re.search(r"contact|t[eé]l[eé]phone|num[eé]ro", q, re.I)
            ),
            None,
        )
        if previous:
            contact, query_text = True, previous
    if not duty and not contact:
        return None
    match = re.search(
        r"(?:pharmac(?:ie|y))\s+(.+?)(?:\s+(?:a|à|de)\s+(?:Rabat|Casablanca)|[?!.]|$)",
        query_text,
        re.I,
    )
    name = match[1].strip() if match and contact else None
    if contact and not name:
        return None
    start = today()
    end = start
    if re.search(r"semaine|week|السيمانة|أسبوع", text, re.I):
        start -= timedelta(days=start.weekday())
        if re.search(r"prochaine|next|جاي", text, re.I):
            start += timedelta(days=7)
        end = start + timedelta(days=6)
    elif re.search(r"demain|tomorrow|غدا", text, re.I):
        start += timedelta(days=1)
        end = start
    return {
        "kind": "duty" if duty else "contact",
        "name": name,
        "city": city,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "language": baseline.analyze(text).input.language,
    }


def phones(text):
    """Extract valid Moroccan phones, canonicalized for evidence comparison."""
    return {
        phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164)
        for m in phonenumbers.PhoneNumberMatcher(text, "MA")
        if phonenumbers.is_valid_number(m.number)
    }


def dates(text):
    """Accept explicit complete source dates; never infer a date from a page title."""
    found = set()
    for year, month, day in re.findall(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text):
        try:
            found.add(date(int(year), int(month), int(day)))
        except ValueError:
            pass
    for day, month, year in re.findall(
        r"\b(\d{1,2})[/.](\d{1,2})[/.](20\d{2})\b", text
    ):
        try:
            found.add(date(int(year), int(month), int(day)))
        except ValueError:
            pass
    months = (
        "janvier fevrier mars avril mai juin juillet aout "
        "septembre octobre novembre decembre"
    ).split()
    for day, month, year in re.findall(
        r"\b(\d{1,2})\s+(" + "|".join(months) + r")\s+(20\d{2})\b", plain(text)
    ):
        try:
            found.add(date(int(year), months.index(month) + 1, int(day)))
        except ValueError:
            pass
    return found


def contact_matches(source, request):
    """City and distinctive name must appear together in the cited evidence."""
    body = plain(source.get("excerpt", ""))
    tokens = [
        t
        for t in re.findall(r"\w+", plain(request["name"] or ""))
        if t not in {"al", "el", "pharmacie", "pharmacy"}
    ]
    return bool(
        tokens
        and plain(request["city"] or "") in body
        and all(t in body for t in tokens)
    )


def cached_contact(request):
    """Read attributed enrichment; it is never labelled as a fresh web search."""
    if request["kind"] != "contact" or not request["city"]:
        return None
    path = (
        Path(__file__).resolve().parents[3] / "data/pharmacies/contact_enrichment.json"
    )
    for row in json.loads(path.read_text(encoding="utf-8")):
        if plain(request["city"]) == plain(row["city"]) and plain(request["name"]) in [
            plain(a) for a in row["aliases"]
        ]:
            return {
                "answer": (
                    f"{row['name']} — {row['address']}, {row['city']}.\n"
                    f"Téléphone publié : {row['phone']}.\n"
                    f"Source enregistrée le {row['checked_on']} ; "
                    "appelez pour confirmer."
                ),
                "sources": row["sources"],
                "answer_source": "saved_contact",
                "pharmacies": [],
                "model": None,
            }
    return None


def lookup_answer(tools, request):
    """Invoke business web research and validate the evidence before display."""
    from pharma_assistant.nlp.agent import failure_code

    base = {
        "pharmacies": [],
        "actions": [],
        "model": None,
        "tools_used": [],
        "sources": [],
        "tool_failures": [],
        "web_search": {"attempted": False, "succeeded": False},
    }
    if not request["city"]:
        return {
            **base,
            "answer": "Dans quelle ville cherchez-vous cette pharmacie ?",
            "answer_source": "clarification",
        }
    query = (
        f"Pharmacie {request['name']} {request['city']} contact téléphone adresse"
        if request["kind"] == "contact"
        else (
            f"Pharmacies de garde {request['city']} planning du "
            f"{request['start']} au {request['end']} dates et téléphones"
        )
    )
    try:
        base["web_search"]["attempted"] = any(
            d["name"] == "search_pharmacy_web" for d in tools.definitions()
        )
        research = tools.call("search_pharmacy_web", {"query": query})
        sources = research["sources"]
        summary = research["research_summary"]
        if request["kind"] == "contact":
            matching = [
                s
                for s in sources
                if contact_matches(s, request) and phones(s.get("excerpt", ""))
            ]
            if not matching:
                raise ValueError("No matching city/name/phone evidence")
            numbers = sorted(set.union(*(phones(s["excerpt"]) for s in matching)))
            answer = (
                f"Pharmacie {request['name']} à {request['city']} — "
                f"téléphone publié : {', '.join(numbers)}. "
                "Appelez pour confirmer les informations."
            )
            sources = matching
        else:
            start, end = date.fromisoformat(request["start"]), date.fromisoformat(
                request["end"]
            )
            matching = [
                s
                for s in sources
                if plain(request["city"]) in plain(s.get("excerpt", ""))
                and re.search(r"garde|حراسة", s.get("excerpt", ""), re.I)
                and any(start <= d <= end for d in dates(s.get("excerpt", "")))
            ]
            if not matching:
                raise ValueError("No duty source with matching city and dates")
            corpus = "\n".join(s.get("excerpt", "") for s in matching)
            if not phones(summary) <= phones(corpus):
                raise ValueError("Unsupported web phone")
            if dates(summary) - dates(corpus):
                raise ValueError("Unsupported web date")
            for name in re.findall(r"\bpharmacie\s+([^\n:;—–(),.|]+)", summary, re.I):
                if plain(name.strip(" *")) not in plain(corpus):
                    raise ValueError("Unsupported web pharmacy name")
            answer = (
                f"Planning publié consulté pour {request['city']}, "
                f"période demandée du {start} au {end}.\n\n{summary}\n\n"
                "La couverture peut être partielle. "
                "Confirmez par téléphone avant de vous déplacer."
            )
            sources = matching
        return {
            **base,
            "answer": answer,
            "sources": [
                {k: v for k, v in s.items() if k != "excerpt"} for s in sources
            ],
            "answer_source": "pharmacy_web",
            "tools_used": ["search_pharmacy_web"],
            "web_search": {"attempted": True, "succeeded": True},
        }
    except (ValueError, OSError) as error:
        base["tool_failures"] = [failure_code(error)]
        saved = cached_contact(request)
        if saved:
            return {**base, **saved}
        answer = (
            (
                f"Je n’ai pas pu vérifier le contact de la pharmacie "
                f"{request['name']} à {request['city']}."
            )
            if request["kind"] == "contact"
            else (
                f"Je n’ai pas pu obtenir un planning de garde daté et vérifiable "
                f"pour {request['city']} du {request['start']} au {request['end']}. "
                "Le répertoire habituel ne confirme pas les gardes."
            )
        )
        return {**base, "answer": answer, "answer_source": "web_lookup_unavailable"}
