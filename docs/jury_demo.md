# Pharma-AI: jury demonstration

For the three concrete nearby/Al Irfane stock/duty examples requested later, use
[the explicitly fictional jury scenario](jury_scenario.md). The ten questions below
remain the normal-mode script.

This is a focused multilingual pharmacy-assistance MVP. The ten examples below use the
normal assistant endpoint and the saved source databases. They are a regression-tested
presentation script, not a measure of unrestricted conversation or speech accuracy.

## Start on Windows (PowerShell)

Stop the old server with Ctrl+C, then run from the repository directory:

```powershell
git pull origin codex/assistant-answers-voice
$env:PYTHONUTF8="1"
$env:NLU_TRACK="baseline"
uv sync --frozen --extra speech
uv run --frozen --extra speech python scripts/cache_asr.py
uv run --frozen --extra speech python scripts/start_service.py
```

The cache command downloads the pinned speech weights once. Install FFmpeg first if
`ffmpeg -version` or `ffprobe -version` fails (`winget install Gyan.FFmpeg`, then reopen
PowerShell). Startup builds missing databases from the committed snapshots.

Open **http://localhost:8000**, then Ctrl+F5. The conversation fills the viewport;
the supplied robot image appears as the assistant avatar rather than occupying a side panel.

In a second terminal, run the rehearsal check:

```powershell
uv run --frozen --extra speech python scripts/check_jury_demo.py --require-voice
```

Expected: ten normal `PASS` lines, three fictional scenario `PASS` lines,
`PASS Rabat map`, `Voice prerequisites: READY`, exit code 0.
This verifies the installed server prerequisites, not browser permission or human speech.
Send “Bonjour” once in the open browser before the jury arrives to warm its text pipeline.

## Presentation flow

1. Click **Exemples à essayer**. Choose a question; it fills the composer and selects its
   language. Click Send. Answers are computed normally; the picker never inserts a reply.
2. Show the French medication request, then Darija and Arabic. The summary repeats the
   requested quantity, strength and form. These are the user's words, not dosing advice.
3. Show the saved phone lookup. Explain that directory information can become outdated.
4. Show **Trouver une pharmacie**, choose Rabat and a radius, then Rechercher. Open one
   location from the results. “Autour de moi” asks browser permission only when clicked.
   Internet is needed for map tiles; the saved pharmacy list remains available without tiles.
5. Record a short question using the microphone; click again to stop and send. Use a quiet
   room and select Français or العربية for a language hint. Check the visible transcript;
   **Corriger ce message** lets you edit and resend recognition errors.
6. Click **Écouter la réponse**, or enable **Lecture vocale** for subsequent replies.
   **Arrêter la lecture** stops playback. Auto playback starts disabled. Playback depends
   on voices installed in the browser/OS; Darija pronunciation is not guaranteed.
7. Finish with price, duty and medical-boundary questions to show truthful limitations.

Microphone capture requires localhost or HTTPS and browser permission. Chrome/Edge are
suitable rehearsal targets. If speech is unavailable, the chat remains usable and offers
**Réessayer le micro** after setup. Recording can be cancelled without an upload, stops
automatically after 55 seconds, and audio files can also be attached. No human-audio WER
or cross-browser microphone success is claimed; rehearse these exact spoken prompts on
the presentation laptop before relying on voice.

Each preset is a complete independent request. Chat history is visible, but follow-up
messages such as “and tomorrow?” do not carry prior context. Use the complete questions.

## Ten questions and expected replies

The following replies were generated using the committed snapshot and baseline pipeline.
Names, phones and availability of records depend on that snapshot. Unknown hours stay unknown.

### 1. Découvrir l’assistant

**Question:** Bonjour

**Expected reply:**

> Bonjour, je suis Pharma-AI. Je peux vous aider à formuler une demande de médicament ou à trouver les coordonnées d’une pharmacie. Que recherchez-vous ?

### 2. Demander en darija

**Question:** Wach kayn Doliprane 1000 mg ?

**Expected reply:**

> Kat9elleb 3la: « Doliprane » — 1000 mg. Ma 3ndich stock dyal pharmacies en direct. Sowel pharmacie bach t2ekked wach kayn.
> 
> Chno forme li maktouba f lboita (comprimés, sirop…) ?

### 3. Demander en arabe

**Question:** هل دوليبران متوفر؟

**Expected reply:**

> تبحث عن: « دوليبران ». ليست لدي معلومات مباشرة عن مخزون الصيدليات. تواصل مع الصيدلية للتأكد من توفره.
> 
> قد توجد عدة أشكال أو تفسيرات. هل يمكنك توضيح الاسم والتركيز والشكل المكتوب على العلبة؟

### 4. Préparer une demande

**Question:** Je voudrais 2 boîtes de Doliprane 1000 mg en comprimés.

**Expected reply:**

> J’ai compris votre demande pour : « Doliprane » — 2 boîtes, 1000 mg, comprimés. Aucune commande n’a été envoyée. Contactez la pharmacie pour confirmer le produit et sa disponibilité.
> 
> Faites confirmer le nom complet de la présentation sur la boîte par le pharmacien.

### 5. Reconnaître une faute de frappe

**Question:** Est-ce que dolipran est disponible ?

**Expected reply:**

> Vous cherchez : « dolipran ». Je ne dispose pas du stock des pharmacies en direct. Contactez une pharmacie pour confirmer sa disponibilité.
> 
> Plusieurs présentations ou interprétations sont possibles. Pouvez-vous préciser le nom, le dosage et la forme écrits sur la boîte ?

### 6. Trouver des pharmacies à Rabat

**Question:** Adresse des pharmacies à Rabat ?

**Expected reply:**

> Voici des entrées du répertoire enregistré. Les horaires et téléphones peuvent avoir changé ; la garde n’est pas vérifiée.
> 
> Pharmacie Benyahya صيدلية بنيحيى — Téléphone: inconnu; Horaires enregistrés: inconnu Rabat
> 
> AL MASBAH — Téléphone: inconnu; Horaires enregistrés: inconnu Rabat
> 
> Pharmacie 16 Novembre — Téléphone: +212537675669; Horaires enregistrés: inconnu Rabat
> 
> Pharmacie ANZI — Téléphone: inconnu; Horaires enregistrés: inconnu Rabat
> 
> Pharmacie et Laboratoire Zitoune صيدلية و مختبر الزيتون — Téléphone: inconnu; Horaires enregistrés: inconnu Rabat

### 7. Contacter une pharmacie

**Question:** Quel est le téléphone de la pharmacie 16 Novembre à Rabat ?

**Expected reply:**

> Voici des entrées du répertoire enregistré. Les horaires et téléphones peuvent avoir changé ; la garde n’est pas vérifiée.
> 
> Pharmacie 16 Novembre — Téléphone: +212537675669; Horaires enregistrés: inconnu Rabat

### 8. Demander un prix

**Question:** Quel est le prix de Doliprane ?

**Expected reply:**

> Je n’ai pas de prix marocain vérifié pour « Doliprane ». Contactez une pharmacie pour demander le prix exact de la présentation souhaitée. Pour votre demande à la pharmacie, précisez le dosage, la forme et le nombre d’unités dans la boîte.

### 9. Chercher une pharmacie de garde

**Question:** chno howa l pharmacie li fih la garde had lila

**Expected reply:**

> Je ne peux pas confirmer les gardes avec les informations disponibles. La carte peut vous aider à trouver des pharmacies à contacter, mais elle ne confirme pas leur garde. Appelez avant de vous déplacer.
> 
> Dans quelle ville ou quel quartier cherchez-vous ? Vous pouvez aussi partager votre position.

### 10. Reconnaître une demande médicale

**Question:** Quelle dose de Doliprane dois je prendre ?

**Expected reply:**

> Je ne peux pas donner de conseil médical, de diagnostic ou de posologie. Pour cela, adressez-vous à un pharmacien ou à un médecin.

## Scope to state to the jury

The app structures requests and searches a saved pharmacy directory. It does not confirm
live stock, send orders, supply verified Moroccan prices, identify tonight's guard, or
provide clinical advice. The medicine reference is the French BDPM fallback, not a
Moroccan product/price register. The map is not a live “open now” or duty map.

Text cases are curated regression checks, not a new held-out language evaluation. The
voice pipeline uses cached multilingual transcription; browser playback uses available
speech voices. User audio is not persisted after processing. Browser/OS voices may use
network services depending on installed voices and device settings.
