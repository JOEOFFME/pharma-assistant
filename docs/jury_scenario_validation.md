# Concrete fictional jury scenarios: validation

## Change

The user requested direct nearby, named-pharmacy Panadol stock and duty answers, and
allowed made-up examples for the jury. These are implemented as an explicit simulation.
`Scénario du jury` starts disabled. A persistent banner and every response identify all
fixture pharmacy/address/distance/stock/duty information as fictional. Switching modes
clears prior messages and shared location. No real pharmacy phone, address, stock,
price or current guard information was invented in the production directory.

Fixtures live in `configs/jury_scenario.yaml`, prompt choices in
`web/assets/jury-scenarios.json`, and rendering/routing in `api/jury_scenario.py`.
Dedicated `/v1/demo/assistant/text` and `/v1/demo/assistant/voice` routes use them;
normal routes keep their existing directory and unverified-stock/duty behavior.
The real map controls are disabled during simulation; fixtures have no map coordinates,
phone numbers or route links. The simulated origin is not the user's real location.

Additionally, duty phrases now outrank generic location terms in normal intent routing:
`fin n9der nl9a une pharmachie de garde` gets the honest duty response in normal mode.
Medical advice remains refused, including in simulation. Unknown products, pharmacies
and prices do not silently inherit the Panadol fixture.

## Validation commands

```bash
uv run --frozen --extra speech pytest -q
uv run --frozen --extra speech ruff check .
uv run --frozen --extra speech black --check .
node --check web/assets/assistant.js
npm test --prefix web
uv run --frozen --extra speech python scripts/check_jury_demo.py --require-voice
```

## Results

- Full pytest suite: 606 passed, one existing Starlette/AnyIO deprecation warning.

- All three exact requested examples passed through the simulation API.
- The preflight passed ten normal questions, all three fictional scenarios, the real
  Rabat map and voice prerequisites (READY). The simulation is not measured as real NLU
  or speech accuracy.
- Ruff, Black, JavaScript syntax and DOM journeys passed.
- New backend cases cover ordered simulated distances, original point labeling,
  language variants, clinical boundaries, unknown stock/price cases, default-mode
  isolation, authentication/validation and fake-ASR transcript passthrough to simulation.
- DOM cases cover default-off mode, fiction banner, clearing history, three examples,
  disabling map navigation, isolated text/voice URLs and restoring normal requests.

## Acceptance and limitations

- [x] Concrete nearby list, Panadol count and duty-name/hours examples.
- [x] Every simulated response and the active UI state explicitly label fiction.
- [x] Default assistant/directory remain free of simulated stock and duty assertions.
- [x] Text and voice use the same fixture answers; no invented transcription.
- [x] Reproducible tests and presentation script in `docs/jury_scenario.md`.
- [ ] Current real stock/duty provider: not integrated by this change.
- [ ] Human microphone accuracy and audible/visual browser rehearsal on the jury laptop.

The fixed hours refer to the night of the scenario, not tonight's real duty schedule.
The only real data query in this change's preflight remains the saved directory/map.
