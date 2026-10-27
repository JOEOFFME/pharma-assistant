# Optional OpenRouter language understanding

The assistant can use your OpenRouter key to interpret French, Arabic and Darija
requests. It accepts a structured intent and literal medication/pharmacy/location
mentions, then looks up and formats facts locally. It does **not** let the model
invent pharmacy stock, prices, duty schedules or medical advice.

## Windows PowerShell setup

Stop the old server with Ctrl+C. From the repository directory:

```powershell
git pull origin codex/assistant-answers-voice
$env:ASSISTANT_NLU="openrouter"
$env:OPENROUTER_MODEL="openai/gpt-4.1"
$openRouterSecret = Read-Host "OpenRouter API key" -AsSecureString
$env:OPENROUTER_API_KEY = [System.Net.NetworkCredential]::new("", $openRouterSecret).Password
Remove-Variable openRouterSecret
uv run --frozen --extra speech python scripts/check_openrouter.py
uv run --frozen --extra speech python scripts/start_service.py
```

The key is entered privately on your machine. It is not part of the command history,
browser code or repository. These variables apply to this terminal session.
`.env.example` documents them; the start script does not automatically load `.env`.

`openai/gpt-4.1` is an example model ID whose OpenRouter model page lists structured
output support. You can replace it with your preferred compatible author/model ID.
This is a compatibility starting point, not a measured recommendation for Darija.
The key itself does not choose a model. Current availability and billing depend on
your OpenRouter account and the selected model/provider.

The explicit check script makes **one API request** using a non-personal example.
Expected output:

```text
OpenRouter connection and structured-output parsing: OK
Model: openai/gpt-4.1
Interpreted intent: pharmacy_info_location
```

A failed check means authentication, credit, model/provider support, network access or
interpretation needs review. It does not report connection success without a response.
The script suppresses raw provider error bodies and never prints the key.

Open http://localhost:8000 and refresh. Keep **Scénario du jury off** to use online
interpretation with saved directory facts. Voice still uses local transcription;
review the recognized text and click Send before it is interpreted by OpenRouter.

## Behavior and boundaries

- `ASSISTANT_NLU=baseline` (default) makes no OpenRouter calls.
- `ASSISTANT_NLU=openrouter` requires both key and model ID. Missing configuration returns
  a service error; it is not represented as a successful connection.
- Consumer mode is independent of the research `NLU_TRACK` setting.
- The model returns a small JSON plan, not answer prose or factual pharmacy records.
- Every accepted mention must select the exact original text at its claimed offsets.
  An invalid/overlapping span, omitted locally recognized city or schema violation causes
  fallback. Locally detected medication negation is preserved.
- Request parameters: temperature 0, max 1,200 completion tokens, 12-second network timeout,
  a bounded response body and one application-level request without paid automatic retries.
- Invalid, unsupported, truncated, unavailable, rate-limited or unauthorized responses fall
  back to the local pipeline. A valid schema alone does not prove correct interpretation.
- Known clinical phrases bypass the model. Newly detected medical requests get the fixed
  refusal, without a model-generated diagnosis or recommendation.
- The three fictional jury questions retain their explicit, finite matching and labels;
  enabling a paid model does not turn them into real stock or duty observations.
- Confirmed text is sent to OpenRouter when online mode is enabled. Audio files, directory
  records and separate location fields are not sent by this adapter. The UI privacy dialog
  discloses the optional online text service.
- The normal jury preflight uses your selected consumer mode. Run it with baseline mode
  for offline checks; running it in OpenRouter mode can make multiple paid requests.
  Pytest forces offline defaults and uses mocked providers in its integration checks.

`GET /version` shows `consumer_nlu=openrouter` when configured; that marker is a setting,
not proof that the remote service answered. Use the explicit check above to test it.
To return to the offline parser, stop the server, set `$env:ASSISTANT_NLU="baseline"`
and restart it.

## References

- [OpenRouter HTTP quickstart](https://openrouter.ai/docs/quickstart)
- [Structured outputs and model compatibility](https://openrouter.ai/docs/guides/features/structured-outputs)
- [GPT-4.1 model and structured-output support](https://openrouter.ai/openai/gpt-4.1)

No real user key was supplied during implementation, so live authentication, billing,
model availability and Darija accuracy remain unverified. The tests use mocked responses;
they are adapter/grounding checks, not a model performance benchmark.
