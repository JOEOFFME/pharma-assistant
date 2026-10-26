# User-recorded voice evaluation protocol

No user-recorded audio has been supplied. WER/CER on real recordings is unavailable.
The temporary synthetic flite smoke test in docs/asr_smoke.json is not evaluation data.

Record each prompt naturally in a quiet room, then optionally repeat with mild background noise.
Keep recordings under 60 seconds and 10 MiB. Use WAV, MP3, M4A, OGG or WebM.
Do not record another person or include real patient identifiers.
Correct each human reference transcript to exactly what you actually said, including typos/hesitations as agreed.
One UTF-8 JSON object per line in data/audio/transcripts.jsonl:
`{"audio_path":"recordings/001.wav","language":"darija_ar","reference_text":"<what you actually said>"}`

Run `make speech-install`, then cache the pinned model explicitly:
`uv run --frozen --extra speech python scripts/cache_asr.py`.
Set configs/asr.yaml model to a copied local model directory when using Docker/offline deployment.
Run `uv run --frozen --extra speech python scripts/evaluate_speech.py data/audio/transcripts.jsonl`.
The runner decodes each file and computes per-variety micro WER/CER from actual hypotheses.
Normalization is case/whitespace folding; punctuation is retained. Deletions/substitutions/insertions use Levenshtein distance.

## Forty recording prompts (assistant-authored; not recordings)

| # | Variety | Prompt |
| --- | --- | --- |
| 01 | darija_ar | واش عندكم دوليبران؟ |
| 02 | darija_ar | بغيت جوج علب ديال دوليبران |
| 03 | darija_ar | شنو نمرة الصيدلية؟ |
| 04 | darija_ar | فين كاينة الصيدلية؟ |
| 05 | darija_ar | الصيدلية محلولة دابا؟ |
| 06 | darija_ar | بشحال دوليبران؟ |
| 07 | darija_ar | السلام عليكم |
| 08 | darija_ar | شنو ناخد لوجع الراس؟ |
| 09 | darija_latn | wach kayn Doliprane? |
| 10 | darija_latn | bghit 2 boites dyal Doliprane |
| 11 | darija_latn | chno nemra dyal pharmacie? |
| 12 | darija_latn | fin kayna pharmacie? |
| 13 | darija_latn | pharmacie me7loula daba? |
| 14 | darija_latn | bch7al Doliprane? |
| 15 | darija_latn | salam 3likom |
| 16 | darija_latn | chno nakhod l sda3? |
| 17 | ar | هل يتوفر دوليبران؟ |
| 18 | ar | أريد علبتين من دوليبران |
| 19 | ar | ما رقم هاتف الصيدلية؟ |
| 20 | ar | أين تقع الصيدلية؟ |
| 21 | ar | هل الصيدلية مفتوحة الآن؟ |
| 22 | ar | ما سعر دوليبران؟ |
| 23 | ar | السلام عليكم ورحمة الله |
| 24 | ar | ماذا أتناول لعلاج الصداع؟ |
| 25 | fr | Avez-vous Doliprane ? |
| 26 | fr | Je voudrais 2 boîtes de Doliprane |
| 27 | fr | Quel est le numéro de la pharmacie ? |
| 28 | fr | Où se trouve la pharmacie ? |
| 29 | fr | La pharmacie est-elle ouverte maintenant ? |
| 30 | fr | Quel est le prix de Doliprane ? |
| 31 | fr | Bonjour |
| 32 | fr | Quel médicament prendre contre le mal de tête ? |
| 33 | mixed | wach kayn Doliprane en stock ? |
| 34 | mixed | bghit 2 boîtes de Doliprane |
| 35 | mixed | chno le numéro de la pharmacie ? |
| 36 | mixed | fin kayna la pharmacie ? |
| 37 | mixed | wach la pharmacie ouverte daba ? |
| 38 | mixed | bch7al le Doliprane ? |
| 39 | mixed | salam, bonjour |
| 40 | mixed | chno prendre pour le mal de tête ? |
