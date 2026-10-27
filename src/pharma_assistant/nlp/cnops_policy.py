"""Require attributable CNOPS evidence for Moroccan medicine money claims."""

import re
from decimal import Decimal
from urllib.parse import urlsplit


def validate_cnops_claims(reply, sources, medicine_context=False):
    """Keep PPV/base/date visible and prevent an old source becoming a current price."""
    monetary = re.findall(
        r"(?<!\w)(\d+(?:[.,]\d{1,2})?)\s*(?:MAD|DH|dirhams?|درهم)\b", reply.answer, re.I
    )
    cited = [sources[i] for i in reply.source_ids]
    if (
        not medicine_context
        and "cnops" not in reply.answer.casefold()
        and not any(s.get("kind") in {"cnops_record", "cnops_web"} for s in cited)
    ):
        return
    if reply.kind == "information" and any(
        s.get("kind") == "cnops_record" for s in cited
    ):
        if "2014" not in reply.answer:
            raise ValueError("Historical CNOPS fact without edition")
    if not monetary:
        return
    official = [
        s
        for s in cited
        if s.get("kind") == "cnops_record"
        or (
            (urlsplit(s.get("url", "")).hostname or "").removeprefix("www.")
            == "cnops.org.ma"
        )
        or (
            (urlsplit(s.get("url", "")).hostname or "").removeprefix("www.")
            == "data.gov.ma"
            and (
                "referentiel-des-medicaments" in s.get("url", "")
                or "094733f5-5434-4163-b837-df0e7b665127" in s.get("url", "")
            )
        )
    ]
    if not official:
        raise ValueError("Medicine money claim without CNOPS evidence")
    allowed = set()
    for source in official:
        if source.get("kind") == "cnops_record":
            if "2014" not in reply.answer:
                raise ValueError("Historical CNOPS price without edition")
            if re.search(
                r"prix actuel (?:est|:)|co[uû]te actuellement|current price(?: is|:)",
                reply.answer,
                re.I,
            ):
                raise ValueError("Historical CNOPS price presented as current")
            allowed.update(
                Decimal(source[f])
                for f in ["ppv_mad", "hospital_price_mad", "reimbursement_base_mad"]
                if source.get(f) is not None
            )
        else:
            allowed.update(
                Decimal(n.replace(",", "."))
                for n in re.findall(
                    r"(?<!\w)\d+(?:[.,]\d{1,2})?(?!\w)", source.get("excerpt", "")
                )
            )
    if any(Decimal(value.replace(",", ".")) not in allowed for value in monetary):
        raise ValueError("Medicine amount absent from CNOPS evidence")
