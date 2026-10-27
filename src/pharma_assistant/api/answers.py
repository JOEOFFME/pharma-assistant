"""Readable, deterministic answers grounded in requests and saved directory facts."""

from pathlib import Path

from pharma_assistant.api.schemas import AnalysisResponse
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.pharmacy_normalize import (
    normalize_city,
    normalize_name,
)
from pharma_assistant.nlp.intent import contains_medical_advice, phrase_in
from pharma_assistant.nlp.normalize import normalize

# These are presentation templates, not medical answers or model-generated claims.
MESSAGES = {
    "fr": {
        "hello": (
            "Bonjour, je suis Pharma-AI. Je peux vous aider à formuler une demande de "
            "médicament ou à trouver les coordonnées d’une pharmacie. Que "
            "recherchez-vous ?"
        ),
        "refusal": (
            "Je ne peux pas donner de conseil médical, de diagnostic ou de "
            "posologie. Pour cela, adressez-vous à un pharmacien ou à un "
            "médecin."
        ),
        "missing": (
            "Quel médicament recherchez-vous ? Indiquez son nom et, si "
            "possible, le dosage et la forme inscrits sur la boîte."
        ),
        "availability": (
            "Vous cherchez : {meds}. Je ne dispose pas du stock des "
            "pharmacies en direct. Contactez une pharmacie pour confirmer "
            "sa disponibilité."
        ),
        "request": (
            "J’ai compris votre demande pour : {meds}. Aucune commande n’a "
            "été envoyée. Contactez la pharmacie pour confirmer le produit "
            "et sa disponibilité."
        ),
        "price": (
            "Vous souhaitez connaître le prix de : {meds}. Je n’ai pas de "
            "prix marocain vérifié pour cette demande. Demandez le prix à "
            "la pharmacie."
        ),
        "clarify": (
            "Plusieurs présentations ou interprétations sont possibles. "
            "Pouvez-vous préciser le nom, le dosage et la forme écrits sur "
            "la boîte ?"
        ),
        "where": (
            "Précisez la ville ou le nom de la pharmacie. Pour les "
            "pharmacies proches de vous, choisissez un centre dans la carte"
            " ci-dessous ou utilisez votre position."
        ),
        "directory": (
            "Voici des entrées du répertoire enregistré. Les horaires et "
            "téléphones peuvent avoir changé ; la garde n’est pas vérifiée."
        ),
        "none": (
            "Je n’ai pas trouvé de pharmacie correspondante dans le "
            "répertoire enregistré. Essayez une autre ville ou la carte "
            "ci-dessous ; la couverture est incomplète."
        ),
        "unavailable": (
            "Le répertoire des pharmacies est momentanément indisponible. "
            "Vous pouvez réessayer plus tard."
        ),
        "phone": "Téléphone",
        "hours": "Horaires enregistrés",
        "unknown": "inconnu",
        "unnamed": "Nom inconnu",
    },
    "ar": {
        "hello": (
            "مرحباً، أنا Pharma-AI. يمكنني مساعدتك في صياغة طلب دواء أو "
            "العثور على معلومات"
            " صيدلية. ماذا تبحث عنه؟"
        ),
        "refusal": (
            "لا أقدم نصائح طبية أو تشخيصاً أو توصيات بالجرعات. يرجى استشارة"
            " صيدلي أو طبيب."
        ),
        "missing": (
            "ما اسم الدواء الذي تبحث عنه؟ اذكر التركيز والشكل المكتوبين على"
            " العلبة إن أمكن."
        ),
        "availability": (
            "تبحث عن: {meds}. ليست لدي معلومات مباشرة عن مخزون الصيدليات. "
            "تواصل مع الصيدلية للتأكد من توفره."
        ),
        "request": (
            "فهمت طلبك بخصوص: {meds}. لم يتم إرسال أي طلب شراء. تواصل مع "
            "الصيدلية لتأكيد المنتج وتوفره."
        ),
        "price": (
            "تريد معرفة سعر: {meds}. ليس لدي سعر مغربي موثّق لهذا الطلب. "
            "يرجى سؤال الصيدلية."
        ),
        "clarify": (
            "قد توجد عدة أشكال أو تفسيرات. هل يمكنك توضيح الاسم والتركيز "
            "والشكل المكتوب على العلبة؟"
        ),
        "where": (
            "حدد المدينة أو اسم الصيدلية. للبحث بالقرب منك، اختر مركزاً في "
            "الخريطة أدناه أو استخدم موقعك."
        ),
        "directory": (
            "هذه معلومات من الدليل المحفوظ. قد تتغير الأرقام والمواعيد، ولا"
            " توجد معلومات مؤكدة عن الحراسة."
        ),
        "none": (
            "لم أجد صيدلية مطابقة في الدليل المحفوظ. جرّب مدينة أخرى أو "
            "الخريطة أدناه؛ التغطية غير مكتملة."
        ),
        "unavailable": "دليل الصيدليات غير متاح حالياً. يرجى المحاولة لاحقاً.",
        "phone": "الهاتف",
        "hours": "المواعيد المسجلة",
        "unknown": "غير معروف",
        "unnamed": "اسم غير معروف",
    },
    "darija_ar": {
        "hello": (
            "سلام، أنا Pharma-AI. نقدر نعاونك تصيغ طلب ديال دوا ولا تلقى "
            "معلومات الصيدلية."
            " شنو كتقلب عليه؟"
        ),
        "refusal": (
            "ما نقدرش نعطيك نصيحة طبية ولا تشخيص ولا شحال تاخد من الدوا. "
            "سول الصيدلي ولا الطبيب."
        ),
        "missing": (
            "شنو سميت الدوا اللي كتقلب عليه؟ إلا ممكن، كتب التركيز والشكل "
            "اللي مكتوبين فالعلبة."
        ),
        "availability": (
            "كتقلب على: {meds}. ما عنديش الستوك ديال الصيدليات مباشرة. خاصك"
            " تسول الصيدلية باش تأكد واش كاين."
        ),
        "request": (
            "فهمت بلي بغيتي: {meds}. ما تصيفط حتى طلب شراء. تواصل مع "
            "الصيدلية باش تأكد المنتوج وواش متوفر."
        ),
        "price": (
            "بغيتي تعرف الثمن ديال: {meds}. ما عنديش ثمن مغربي موثوق لهاد "
            "الطلب. سول الصيدلية على الثمن."
        ),
        "clarify": (
            "ممكن تكون كثر من علبة ولا تفسير. وضّح ليا السمية والتركيز "
            "والشكل اللي مكتوبين فالعلبة."
        ),
        "where": (
            "عطيني المدينة ولا سميت الصيدلية. باش تلقى القريبين ليك، اختار "
            "بلاصة فالخريطة لتحت ولا استعمل الموقع ديالك."
        ),
        "directory": (
            "ها معلومات من الدليل المحفوظ. النوامر والتوقيت يقدرو يتبدلو؛ "
            "الحراسة ما مؤكداش."
        ),
        "none": (
            "ما لقيتش صيدلية مطابقة فالدليل المحفوظ. جرب مدينة أخرى ولا "
            "الخريطة؛ الدليل ما فيهش كلشي."
        ),
        "unavailable": "دليل الصيدليات ما متوفرش دابا. عاود جرّب من بعد.",
        "phone": "النمرة",
        "hours": "التوقيت المسجل",
        "unknown": "ما معروفش",
        "unnamed": "السمية ما معروفةش",
    },
    "darija_latn": {
        "hello": (
            "Salam, ana Pharma-AI. N9der n3awnek tsayeb talab dyal dwa wla "
            "tel9a ma3loumat"
            " pharmacie. Chno kat9elleb 3lih?"
        ),
        "refusal": (
            "Ma n9derch n3tik nasi7a tibbiya, diagnostic wla ch7al takhod "
            "men dwa. Sowel pharmacien wla tbib."
        ),
        "missing": (
            "Chno smit dwa li kat9elleb 3lih? Ila momkin, kteb dosage w "
            "forme li maktoubin f lboita."
        ),
        "availability": (
            "Kat9elleb 3la: {meds}. Ma 3ndich stock dyal pharmacies en "
            "direct. Sowel pharmacie bach t2ekked wach kayn."
        ),
        "request": (
            "Fhemt belli bghiti: {meds}. Ma tsift 7ta commande. Twasel m3a "
            "pharmacie bach t2ekked produit w disponibilité."
        ),
        "price": (
            "Bghiti t3ref taman dyal: {meds}. Ma 3ndich taman maghribi "
            "mwetta9 l had talab. Sowel pharmacie."
        ),
        "clarify": (
            "Momkin kaynin plusieurs présentations. Chno smiya, dosage w "
            "forme li maktoubin f lboita?"
        ),
        "where": (
            "3tini lmdina wla smit pharmacie. Ila bghiti li 9ribin lik, "
            "khtar blassa f la carte lte7t wla sta3mel position dyalek."
        ),
        "directory": (
            "Hadi ma3loumat men répertoire msajjel. Téléphone w horaires "
            "y9dro yetbeddlo; garde machi confirmée."
        ),
        "none": (
            "Ma l9itch pharmacie motabi9a f répertoire. Jerreb mdina okhra "
            "wla la carte; couverture machi kamla."
        ),
        "unavailable": (
            "Répertoire dyal pharmacies ma khddamch daba. 3awed jerreb men " "be3d."
        ),
        "phone": "Téléphone",
        "hours": "Horaires msajjelin",
        "unknown": "ma ma3roufch",
        "unnamed": "Smiya ma ma3roufach",
    },
}


# A domain clarification is different from a medical refusal.
PRESENTATION_HELP = {
    "fr": {
        "unsupported": (
            "Je n’ai pas compris votre demande. Cherchez-vous un médicament"
            " ou une pharmacie ? Pouvez-vous préciser ?"
        ),
        "find": "Voir les pharmacies",
        "share": "Partager ma position",
        "distance": "km",
    },
    "ar": {
        "unsupported": "لم أفهم طلبك. هل تبحث عن دواء أم عن صيدلية؟ هل يمكنك التوضيح؟",
        "find": "اعرض الصيدليات",
        "share": "شارك موقعي",
        "distance": "كم",
    },
    "darija_ar": {
        "unsupported": (
            "ما فهمتش الطلب ديالك. واش كتقلب على دوا ولا صيدلية؟ وضّح ليا " "شوية."
        ),
        "find": "شوف الصيدليات",
        "share": "شارك الموقع ديالي",
        "distance": "كم",
    },
    "darija_latn": {
        "unsupported": (
            "Ma fhemtch talab dyalek. Wach kat9elleb 3la dwa wla pharmacie?"
            " Wdde7 lia chwiya."
        ),
        "find": "Chouf pharmacies",
        "share": "Partager position dyali",
        "distance": "km",
    },
}


SERVICE_HELP = {
    "fr": {
        "duty": (
            "Je ne peux pas confirmer les gardes avec les informations "
            "disponibles. La carte peut vous aider à trouver des pharmacies"
            " à contacter, mais elle ne confirme pas leur garde. Appelez "
            "avant de vous déplacer."
        ),
        "duty_location": (
            "Dans quelle ville ou quel quartier cherchez-vous ? Vous pouvez"
            " aussi partager votre position."
        ),
        "price": (
            "Je n’ai pas de prix marocain vérifié pour {meds}. Contactez "
            "une pharmacie pour demander le prix exact de la présentation "
            "souhaitée."
        ),
        "price_hint": (
            "Pour votre demande à la pharmacie, précisez le dosage, la "
            "forme et le nombre d’unités dans la boîte."
        ),
    },
    "ar": {
        "duty": (
            "لا أستطيع تأكيد صيدليات الحراسة بالمعلومات المتاحة. تساعدك "
            "الخريطة على العثور على صيدليات للاتصال بها، لكنها لا تؤكد "
            "الحراسة. اتصل قبل الذهاب."
        ),
        "duty_location": "في أي مدينة أو حي تبحث؟ يمكنك أيضاً مشاركة موقعك.",
        "price": (
            "ليس لدي سعر مغربي موثّق لـ {meds}. تواصل مع الصيدلية للسؤال عن"
            " سعر العبوة المطلوبة بالضبط."
        ),
        "price_hint": "عند سؤال الصيدلية، حدد التركيز والشكل وعدد الوحدات في العبوة.",
    },
    "darija_ar": {
        "duty": (
            "ما نقدرش نأكد شكون داير الحراسة بالمعلومات اللي عندي. الخريطة "
            "كتعاونك تلقى صيدليات تتاصل بيهم، ولكن ما كتأكدش الحراسة. عيط "
            "قبل ما تمشي."
        ),
        "duty_location": "فاش من مدينة ولا حي كتقلب؟ تقدر حتى تشارك الموقع ديالك.",
        "price": (
            "ما عنديش ثمن مغربي موثوق ديال {meds}. تواصل مع الصيدلية باش "
            "تعرف الثمن ديال العلبة اللي بغيتي بالضبط."
        ),
        "price_hint": "ملي تسول الصيدلية، وضح التركيز والشكل وشحال من وحدة فالعلبة.",
    },
    "darija_latn": {
        "duty": (
            "Ma n9derch n2ekked chkoun dayr la garde b lma3loumat li 3ndi. "
            "La carte t3awnek tel9a pharmacies ttassel bihom, walakin ma "
            "kat2ekkedch la garde. 3ayet 9bel ma tmchi."
        ),
        "duty_location": (
            "Fach men mdina wla 7ay kat9elleb? T9der tpartagi position " "dyalek."
        ),
        "price": (
            "Ma 3ndich taman maghribi mwetta9 dyal {meds}. Ttassel b "
            "pharmacie bach t3ref taman dyal lboita li bghiti b ddabt."
        ),
        "price_hint": (
            "Mlli tsowel pharmacie, wde7 dosage, forme w ch7al men unité f " "lboita."
        ),
    },
}


REQUEST_CLARIFICATIONS = {
    "fr": {
        "form": "Quelle forme est indiquée sur la boîte (comprimés, sirop…) ?",
        "strength": "Quel dosage est inscrit sur la boîte ?",
        "verify": (
            "Faites confirmer le nom complet de la présentation sur la boîte "
            "par le pharmacien."
        ),
    },
    "ar": {
        "form": "ما الشكل المكتوب على العلبة (أقراص، شراب…)؟",
        "strength": "ما التركيز المكتوب على العلبة؟",
        "verify": "اطلب من الصيدلي تأكيد الاسم الكامل للعبوة المطلوبة.",
    },
    "darija_ar": {
        "form": "شنو الشكل اللي مكتوب فالعلبة (أقراص، شراب…)؟",
        "strength": "شنو التركيز اللي مكتوب فالعلبة؟",
        "verify": "خلي الصيدلي يأكد ليك السمية الكاملة ديال العلبة المطلوبة.",
    },
    "darija_latn": {
        "form": "Chno forme li maktouba f lboita (comprimés, sirop…) ?",
        "strength": "Chno dosage li maktoub f lboita ?",
        "verify": "Khlli pharmacien y2ekked smiya kamla dyal présentation f lboita.",
    },
}


def present_answer(analysis: AnalysisResponse, user_location=None) -> dict:
    """Answer the in-scope part without fabricating stock, prices or transactions."""
    language = analysis.input.language
    messages = MESSAGES.get(language, MESSAGES["fr"])
    intent = analysis.intent.label
    evidence = analysis.input.transcript or analysis.input.raw_text
    is_duty = intent == "pharmacy_info_hours" and any(
        phrase_in(normalize(evidence, arabizi=False).text, term)
        for term in load_config(Path("configs/baseline.yaml")).get("duty_terms", [])
    )
    service = SERVICE_HELP.get(language, SERVICE_HELP["fr"])
    medications = [
        e
        for e in analysis.entities
        if e.type == "MEDICATION" and e.assertion == "affirmed"
    ]
    # Echo only the extracted names. Clinical text from mixed requests is excluded.
    names = ", ".join(f"« {e.text} »" for e in medications)
    # Strength/form/quantity are quoted request details, never dosing advice.
    # With multiple medicines the parser does not reliably associate each detail;
    # keep them out of the summary rather than attach them to the wrong product.
    if len(medications) == 1 and intent in {"check_availability", "request_medication"}:
        details = [
            e.text
            for e in analysis.entities
            if e.type in {"DOSAGE", "FORM", "QUANTITY"} and e.assertion == "affirmed"
        ]
        if details:
            names += " — " + ", ".join(dict.fromkeys(details))
    help_text = PRESENTATION_HELP.get(language, PRESENTATION_HELP["fr"])
    records = []
    distances = {}
    actions = []
    if intent == "out_of_scope":
        config = load_config(Path("configs/baseline.yaml"))
        evidence = analysis.input.transcript or analysis.input.raw_text
        answer = (
            messages["refusal"]
            if contains_medical_advice(evidence, config)
            else help_text["unsupported"]
        )
    elif intent == "greeting_smalltalk":
        answer = messages["hello"]
    elif is_duty:
        answer = service["duty"]
        if user_location is None and not any(
            e.type == "LOCATION" for e in analysis.entities
        ):
            answer += "\n\n" + service["duty_location"]
    elif intent == "price_inquiry":
        answer = (
            service["price"].format(meds=names) if medications else messages["missing"]
        )
        if medications and not any(
            e.type in {"DOSAGE", "FORM", "QUANTITY"} and e.assertion == "affirmed"
            for e in analysis.entities
        ):
            answer += " " + service["price_hint"]
    elif intent in {"check_availability", "request_medication"}:
        kind = {
            "check_availability": "availability",
            "request_medication": "request",
            "price_inquiry": "price",
        }[intent]
        answer = (
            messages[kind].format(meds=names) if medications else messages["missing"]
        )
        if medications and analysis.needs_clarification:
            supplied = {e.type for e in analysis.entities if e.assertion == "affirmed"}
            clarification = messages["clarify"]
            if len(medications) == 1:
                specific = REQUEST_CLARIFICATIONS.get(
                    language, REQUEST_CLARIFICATIONS["fr"]
                )
                if {"DOSAGE", "FORM"} <= supplied:
                    clarification = specific["verify"]
                elif "DOSAGE" in supplied:
                    clarification = specific["form"]
                elif "FORM" in supplied:
                    clarification = specific["strength"]
            answer += "\n\n" + clarification
    else:
        pharmacy_names = [
            e.text for e in analysis.entities if e.type == "PHARMACY_NAME"
        ]
        locations = [e.text for e in analysis.entities if e.type == "LOCATION"]
        if not pharmacy_names and not locations and user_location is None:
            answer = messages["where"]
        else:
            try:
                config = load_config(Path("configs/pharmacies.yaml"))
                repository = PharmacyRepository(
                    Path(config["database_path"]), config["city_aliases"]
                )
                if pharmacy_names:
                    records = repository.search_by_name(pharmacy_names[0], limit=5)
                elif locations:
                    records = repository.by_city(locations[0], limit=5)
                else:
                    nearby = repository.within_radius(
                        user_location.latitude, user_location.longitude, radius_km=10
                    )[:5]
                    records = [row.pharmacy for row in nearby]
                    distances = {row.pharmacy.id: row.distance_km for row in nearby}
                lines = [messages["directory"]]
                for record in records:
                    phone = ", ".join(record.phones_e164) or messages["unknown"]
                    hours = record.opening_hours or messages["unknown"]
                    distance = (
                        f"{distances[record.id]:.2f} {help_text['distance']} — "
                        if record.id in distances
                        else ""
                    )
                    lines.append(
                        f"{record.name or messages['unnamed']} — {distance}"
                        f"{messages['phone']}: {phone}; "
                        f"{messages['hours']}: {hours} "
                        f"{record.city or ''}"
                    )
                answer = "\n\n".join(lines) if records else messages["none"]
            except (FileNotFoundError, OSError):
                answer = messages["unavailable"]
    if intent in {"pharmacy_info_location", "price_inquiry"} or is_duty:
        actions = [
            {"type": "find_pharmacy", "label": help_text["find"]},
        ]
        locations = [e.text for e in analysis.entities if e.type == "LOCATION"]
        if locations:
            city_aliases = load_config(Path("configs/pharmacies.yaml"))["city_aliases"]
            city = normalize_city(
                locations[0],
                {normalize_name(key): value for key, value in city_aliases.items()},
            )
            if city:
                actions[0]["city"] = city
        if user_location is None:
            actions.append({"type": "share_location", "label": help_text["share"]})
    if analysis.contains_out_of_scope_request and intent != "out_of_scope":
        answer += "\n\n" + messages["refusal"]
    return {
        "answer": answer,
        "actions": actions,
        "language": language,
        "transcript": analysis.input.transcript,
        "pharmacies": [record.model_dump(mode="json") for record in records],
        "analysis": analysis.model_dump(mode="json", by_alias=True),
        "disclaimer": analysis.disclaimer,
    }
