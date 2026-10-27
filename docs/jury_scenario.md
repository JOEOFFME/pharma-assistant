# Three concrete jury scenarios — fictional data

Enable **Scénario du jury** in the chat header, then open **Exemples à essayer**.
It now offers these three questions. Send or record the complete question. The mode
starts disabled and every simulated answer includes a fiction notice, including when
read aloud. Switching modes clears the conversation and any shared location.

All pharmacies, addresses, distances, inventory counts and duty hours below are
**presentation fixtures**. They are not observations about real Al Irfane pharmacies.
No real customer should use these results to travel, obtain medicine or find tonight's duty.
There are no fabricated phone numbers or navigation links.

## 1. Nearby list

**Question:** `3tini list dyal a9rab les pharmacy lya`

**Answer (after the fiction notice):**

> Hadi list dyal a9rab pharmacies f scénario, men point fictif Al Irfane :
>
> 1. Pharmacie Al Irfane (fictive)
> Point A — avenue de démonstration
> Distance simulée : 350 m
>
> 2. Pharmacie Démo Atlas (fictive)
> Point B — place de démonstration
> Distance simulée : 800 m
>
> 3. Pharmacie Démo Nuit (fictive)
> Point C — boulevard de démonstration
> Distance simulée : 1200 m

The origin is a fixed fictional point, not the user's actual location. Real map controls
are disabled while this mode is active, so simulated distances cannot become directions.

## 2. Stock at a named pharmacy

**Question:** `f pharmacy al Irfane wach n9der nl9a endhom Panadol`

**Answer (after the fiction notice):**

> Ah, f had scénario, Panadol kayn f Pharmacie Al Irfane (fictive) :
> 12 boîtes f stock simulé.
>
> Pharmacie Al Irfane (fictive)
> Point A — avenue de démonstration
> Distance simulée : 350 m

Only the named Panadol example has this simulated count. Unknown products, pharmacies
and prices receive an explanation of what the scenario contains, rather than another
invented stock or price. No strength, substitution or dosing recommendation is inferred.

## 3. Duty pharmacy

**Question:** `fin n9der nl9a une pharmachie de garde`

**Answer (after the fiction notice):**

> F had scénario, pharmacie li dayra la garde hiya :
>
> Pharmacie Démo Nuit (fictive)
> Point C — boulevard de démonstration
> Distance simulée : 1200 m
> Garde simulée : 20:00–08:00, f lil dyal scénario.

This is the night of the fictional scenario, not a current dated duty schedule.

## Run and check

Update the branch and start as described in [jury_demo.md](jury_demo.md). The same
microphone, transcript correction and read-aloud controls work in either mode. Human
speech recognition and browser voice output still need rehearsal on the jury laptop.

```powershell
uv run --frozen --extra speech python scripts/check_jury_demo.py --require-voice
```

Expected: ten normal question checks, three `fictional scenario` checks, Rabat map,
and voice readiness. This is a functional preflight, not an accuracy evaluation.

## Implementation boundary

- `configs/jury_scenario.yaml`: visibly synthetic fixture records, separate from SQLite.
- `web/assets/jury-scenarios.json`: the three editable prompt choices.
- `/v1/demo/assistant/text` and `/v1/demo/assistant/voice`: explicit simulation routes.
- Normal `/v1/assistant/*` routes continue to use the real saved directory and truthful limits.
- Medical advice remains refused in both modes. No live stock or duty provider was added.
- In normal mode, “fin … de garde” now prioritizes the duty intent over generic location words.
