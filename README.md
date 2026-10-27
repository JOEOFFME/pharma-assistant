# Pharma-AI

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
Casablanca, Marrakech, Tanger, Fès or Agadir as a starting point, use your
location through **Autour de moi** (browser permission and
localhost/HTTPS required). Choose a distance from **1 to 100 km** and click
**Rechercher**. The search returns every saved directory record
inside that radius, sorted by straight-line distance, with a center marker,
perimeter, pharmacy markers and a contact list. City presets are search anchors,
not administrative region boundaries. Phone/hours remain unknown when absent;
no live stock or on-duty status is inferred. OSM coverage is incomplete.

No Google Maps key is required. Plotly JavaScript is served from the pinned
Python package at `/assets/plotly.min.js`; map tiles require Internet/WebGL.
If the map cannot render, the pharmacy list remains available. Configured API
protection applies to map queries as well; authentication is handled by the
operator, not by a credential field in the chat.

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

## Consumer chat interface

The demo uses a blue two-panel conversation layout with a virtual companion,
a message composer, audio attachment and microphone controls. Replies appear as
ordinary chat messages in French, Arabic or Darija. No JSON, entity labels,
confidence scores, API-key field, setup commands or raw coordinates are exposed
in the consumer interface. The pharmacy map opens from **Trouver une pharmacie**,
using city, distance and optional **Autour de moi** controls. Conversation text is
kept in page memory only; **Nouvelle conversation** clears it.

The companion panel uses the owner-provided pharmacy-robot image, with its
source markings preserved. It represents a virtual assistant. Local assets are served under `/ui/`. Plotly loads
only when the map is opened. Responsive layouts include a compact mobile
companion strip, reduced-motion preferences and Arabic text direction.

`POST /v1/assistant/text` and `/v1/assistant/voice` return readable `answer`,
`language`, `transcript`, source-backed `pharmacies`, `analysis` and `disclaimer`.
The UI consumes the answer/transcript and never renders analysis data.
Nearest-pharmacy requests offer map and location-sharing actions. Location is
requested only after a user click; the assistant never infers a position.
With an explicitly supplied position, directory replies show up to five saved
records within 10 km, sorted by straight-line distance. Without a position or
city it asks for one. Unrecognized requests get clarification; only detected
medical-advice requests receive the clinical refusal.
The existing `/v1/analyze/*` machine-consumer schemas remain unchanged.
Answers are localized templates, not unrestricted chat or medical advice. They
never confirm live stock, invent Moroccan prices, send orders or recommend doses.
Each request is analyzed independently; the visible transcript is not LLM memory.

Technical setup belongs to the operator and this README. A voice service that is
not ready shows a simple unavailability message and leaves typing available.
If `API_KEY` is enabled, API protection remains enforced; use an authenticated
upstream gateway that supplies credentials for approved visitors. Never place
the server secret in HTML/JavaScript or remove authentication to hide its UI.
The local default has API-key protection disabled. This UI does not add a login
service or bypass a configured API key.

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
without downloading anything. Only the operator sees setup instructions here;
consumers see a simple voice-availability message.
Keep `--extra speech` in voice startup commands. Windows uploads are closed before
external decoders reopen them. Duration-less MediaRecorder WebM is measured by a
bounded decode rather than rejected. Uploaded recordings are deleted after use.
A selected Arabic/Darija or French language is forwarded as an ASR hint, and the
transcript appears in the user’s voice-message bubble with a correction action.

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

## Optional consumer-interface checks

Node >=20 is needed only for these development checks, not to serve the app:

```bash
npm ci --prefix web --ignore-scripts --no-audit --no-fund
npm test --prefix web
```

See [consumer-interface Validation Report](docs/consumer_interface_validation.md)
for files, exact results, generated-asset provenance and remaining browser QA.

Duty questions are handled separately from ordinary directory lookups. The
assistant cannot verify current guard schedules and offers pharmacies to contact,
without labeling directory records as on duty. Price questions give a single
clear explanation and a contact option; brand-only requests receive a brief
product-detail reminder rather than a redundant generic clarification. Neither
live duty schedules nor verified Moroccan prices have been integrated. See
[Pharma-AI duty/price Validation Report](docs/duty_price_brand_validation.md).
