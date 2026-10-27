# Pharma Assistant

Arabic, Moroccan Darija, French and mixed-language pharmacy-request prototype.
It structures requests and searches attributed reference data. It provides **no
medical advice, dosage recommendations, diagnosis, substitutions or live stock**.

## Run the demo

Python 3.11, pinned `uv==0.13.4`, and ffmpeg/ffprobe are required.

```bash
make install
make lint
make test
make demo
```

Open **http://127.0.0.1:8000/** for the text/audio demo and
**http://127.0.0.1:8000/docs** for OpenAPI. `make demo` builds missing SQLite
files from committed public snapshots. It does not scrape or download weights.
`GET /health` returns exactly `{"status":"ok"}` and a disclaimer header.

```bash
curl -X POST http://127.0.0.1:8000/v1/analyze/text \
  -H 'Content-Type: application/json' \
  -d '{"text":"wach kayn Doliprane 500 mg?"}'
curl 'http://127.0.0.1:8000/v1/medications/search?q=dolipran&k=3'
curl 'http://127.0.0.1:8000/v1/pharmacies/nearby?lat=34.0209&lon=-6.8416&k=3'
```

Copy `.env.example` to `.env` (make install does this). Set `API_KEY` to protect
analysis/search endpoints and send `X-API-Key`. Set `CORS_ORIGINS` to allowed
browser origins; it is empty by default. `RATE_LIMIT_PER_MINUTE` defaults to 120.
`user_location` is validated on text requests; nearby searches use explicit
coordinates in the directory endpoint. Analysis does not invent a geocoded
LOCATION entity or confirm a directory answer from the hint.

## Pharmacy map

The demo includes a **Plotly Express + OpenStreetMap** map. Choose Rabat,
Casablanca, Marrakech, Tanger, Fès or Agadir as a starting point, enter custom
latitude/longitude, or click **Utiliser ma position** (browser permission and
localhost/HTTPS required). Set a radius from **0.1 to 100 km** and click
**Afficher les pharmacies**. The search returns every saved directory record
inside that radius, sorted by straight-line distance, with a center marker,
perimeter, pharmacy markers and a contact list. City presets are search anchors,
not administrative region boundaries. Phone/hours remain unknown when absent;
no live stock or on-duty status is inferred. OSM coverage is incomplete.

No Google Maps key is required. Plotly JavaScript is served from the pinned
Python package at `/assets/plotly.min.js`; map tiles require Internet/WebGL.
If the map cannot render, the pharmacy list remains available. The API key input
also applies to map queries when `API_KEY` is configured.

```bash
curl 'http://127.0.0.1:8000/v1/pharmacies/map?lat=34.0209&lon=-6.8416&radius_km=5'
```

Response: `pharmacies`, `count`, `radius_km`, Plotly `figure`, coverage,
attribution and disclaimer. All matching records are returned, without the
nearest-search endpoint's `k` limit. No user location is persisted by the map;
the browser sends selected coordinates to this API and fetches map tiles from
OpenStreetMap.

## Text tracks and evaluation

```bash
make medications       # attributed BDPM database + saved 50-query mini-test
make pharmacies        # attributed OSM directory + coverage report
make dataset           # reproducible family splits and quality inventory
make baseline-eval     # explicitly user-reviewed draft, not independent human gold
make train-nlu          # word/character TF-IDF intent + learned BIO token classifier
uv run --frozen python scripts/compare_tracks.py
make scenarios         # 40 multilingual scenarios; failures are retained
uv run --frozen python scripts/run_ablations.py
```

Default `NLU_TRACK=baseline`. After `make train-nlu`, `NLU_TRACK=hybrid` uses
`models/char_wb/model.pkl` (override with `NLU_MODEL_PATH`). Load only trusted
locally trained pickle files, never uploaded or downloaded arbitrary files.
The hybrid keeps baseline extraction and safety routing.

`NLU_TRACK=llm` requires an operator-configured `LLM_ENDPOINT` (HTTPS) and
`LLM_API_KEY`. Adapter contract: POST `{text,schema}`, return a complete v1 JSON
response. This is provider-neutral, not a drop-in OpenAI chat-completions client.
Invalid JSON, timeout, unsupported evidence or clinical routing conflict falls
back to the baseline. `FakeLLM` is test-only; no real-provider scores are claimed.

A separate optional local encoder fine-tuning path is available:

```bash
uv sync --frozen --extra encoder
uv run --frozen --extra encoder python scripts/fine_tune_encoder.py \
  --model-path <licensed-local-encoder-snapshot> --output models/encoder --steps 40
uv run --frozen --extra encoder python scripts/evaluate_encoder.py \
  --model-dir models/encoder --output reports/encoder_dev.json
```

No encoder snapshots were supplied or encoder training results claimed. Two
lightweight supervised variants were actually trained; their poor intent dev
scores are preserved. See [evaluation](docs/10_evaluation.md),
[architecture](docs/architecture.md), and [acceptance checklist](docs/11_checklist.md).

## Readable answers

The demo displays a readable response in French, Arabic or Darija. Structured
JSON and entity highlighting are tucked inside **Détails techniques (facultatif)**.
`POST /v1/assistant/text` accepts the same input as `/v1/analyze/text` and returns
`answer`, `language`, `transcript`, optional source-backed `pharmacies`, `analysis`
and `disclaimer`. `/v1/assistant/voice` presents the same output for audio uploads.
The existing `/v1/analyze/*` machine-consumer schemas are unchanged.

Answers use deterministic localized templates; this is a pharmacy-request helper,
not unrestricted chat or a medical adviser. It never confirms live stock, invents
Moroccan prices, sends orders, or recommends dosages. Directory replies use saved
records; missing contact fields and on-duty status remain unknown. Ambiguous
medication names produce a specific product-clarification question.

## Voice

For Windows / PowerShell (install FFmpeg once, then reopen the terminal):

```powershell
winget install --id Gyan.FFmpeg --exact
```

Inside the project folder, in a new terminal:

```powershell
$env:PYTHONUTF8 = "1"
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/cache_asr.py
uv run --frozen --extra speech python scripts/start_service.py
```

For Linux/macOS with ffmpeg/ffprobe installed:

```bash
make speech-install
uv run --frozen --extra speech python scripts/cache_asr.py
uv run --frozen --extra speech python scripts/start_service.py
curl -X POST http://127.0.0.1:8000/v1/analyze/voice -F 'file=@your-recording.wav'
```

ASR uses CPU/int8 faster-whisper and a pinned multilingual tiny checkpoint.
The explicit cache step downloads weights; inference uses local files only.
[Model source/license](https://huggingface.co/Systran/faster-whisper-tiny/tree/d90ca5f).
The Docker image is text-capable by default; install the speech extra and mount
complete cached model files/configure a local model directory to enable voice.
The browser microphone requires localhost or HTTPS and user permission.
`GET /v1/voice/status` reports missing tools, speech packages or cached weights
without downloading anything. The UI shows readiness and setup instructions.
Keep `--extra speech` in voice startup commands. Windows uploads are closed before
external decoders reopen them. Duration-less MediaRecorder WebM is measured by a
bounded decode rather than rejected. Uploaded recordings are deleted after use.
A selected Arabic/Darija or French language is forwarded as an ASR hint, and the
transcript appears above the optional technical details so users can correct it.

Actual model inference was smoke-tested on synthetic flite speech. Its poor
transcript is retained in [asr_smoke.json](docs/asr_smoke.json); this is not a
user-recorded benchmark. No WER/CER is claimed without user recordings.
[Recording protocol and 40 prompts](data/audio/README.md) and
`scripts/evaluate_speech.py` provide the reproducible evaluation path.

## Data and gold status

The latest user correction/attestation applies to 84 draft messages/intent labels.
The file `gold_human.jsonl` remains empty. Review annotations retain assistant
creation provenance and are not silently relabelled human. Entity scores against
automatic proposals are **provisional agreement**, not verified-gold entity F1.
Two duplicate greetings are explicitly quarantined in the review queue.
See [review attestation](docs/draft_review_attestation.json),
[review table](docs/gold_draft_review.md), [annotation spec](docs/02_nlu_spec.md),
and [human collection instructions](docs/gold_annotation_howto.md).

BDPM source is France and has no Moroccan PPV/availability. OSM coverage is
incomplete and live duty status is unknown. No missing facts are manufactured.
Sources/licenses and coverage: [medications](data/medications/README.md),
[pharmacies](data/pharmacies/README.md), [problem study](docs/01_problem_study.md).

## Docker and verification

```bash
docker compose up --build
make schema
make lint
make test
```

Docker binds localhost:8000. CI runs frozen installation, schema/data
reproducibility, lint, tests and an image build. Local Docker verification is
reported separately from CI because this workspace has no Docker executable.
No secrets, real patient data, model weights or generated user recordings belong
in git. See [final Validation Report](docs/11_validation.md) for actual checks,
remaining externally dependent validations and exact measured results.
