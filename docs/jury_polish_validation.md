# Jury demo interface polish — 2026-10-27

The consumer chat now labels the provenance of saved contacts and local information,
separately from online-search success or failure. Labels follow the selected language
(French, Arabic, Darija-Arabic fallback or Darija-Latin). No model IDs, API settings,
JSON or diagnostic codes are added to the consumer flow.

Published Moroccan phone numbers in sourced answers offer a user-initiated `tel:`
link. The UI canonicalizes separators, deduplicates numbers, caps the action count,
and omits phone actions for unsourced or explicitly fictional replies. Creating the
link does not place a call. Existing source links remain HTTPS-only, reject embedded
credentials, use safe text and `noopener noreferrer`, and now deduplicate URLs.

Changes: web/assets/assistant.js, web/assets/assistant.css, web/index.html and
existing tests/ui_journeys.mjs. The script cache marker is `jury-polish-v7`.

Validation:

```bash
node --check web/assets/assistant.js
npm test --prefix web
```

Both passed. The existing HappyDOM journeys exercise the real UI script with mocked
network, speech, media and location. Additional checks verify that failed online
search and saved contact labels remain distinct in Darija and that a formatted
published phone produces the canonical `tel:+212537686317` link. Earlier French
search-success, source safety, voice, chat reset, location/map and isolated jury-mode
journeys still pass. No native dialer was invoked and no call was placed.

The prior backend revision passed 706 Python tests. No backend code changed in this
UI polish, so the Python suite was not repeated. Human voice accuracy and live
OpenRouter permissions remain outside this verification. No browser screenshot or
real-device rendering claim is made.

Acceptance:

- [x] Saved information has a clear source label.
- [x] Search outcome labels follow the language setting.
- [x] Sourced phone numbers offer click-to-call links.
- [x] Duplicate source URLs collapse to one link.
- [x] Existing consumer journeys pass.

Windows: update `codex/assistant-answers-voice`, restart the service and Ctrl+F5.
