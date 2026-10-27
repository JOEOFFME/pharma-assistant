"""Readable, deterministic answers grounded in requests and saved directory facts."""

from pathlib import Path

from pharma_assistant.api.schemas import AnalysisResponse
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config

# These are presentation templates, not medical answers or model-generated claims.
MESSAGES = {
    "fr": {
        "hello": (
            "Bonjour ! Je peux vous aider à formuler une demande de "
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
            "مرحباً! يمكنني مساعدتك في صياغة طلب دواء أو العثور على معلومات"
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
            "سلام! نقدر نعاونك تصيغ طلب ديال دوا ولا تلقى معلومات الصيدلية."
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
            "Salam! N9der n3awnek tsayeb talab dyal dwa wla tel9a ma3loumat"
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


def present_answer(analysis: AnalysisResponse, user_location=None) -> dict:
    """Answer the in-scope part without fabricating stock, prices or transactions."""
    language = analysis.input.language
    messages = MESSAGES.get(language, MESSAGES["fr"])
    intent = analysis.intent.label
    medications = [
        e
        for e in analysis.entities
        if e.type == "MEDICATION" and e.assertion == "affirmed"
    ]
    # Echo only the extracted names. Clinical text from mixed requests is excluded.
    names = ", ".join(f"« {e.text} »" for e in medications)
    records = []
    if intent == "out_of_scope":
        answer = messages["refusal"]
    elif intent == "greeting_smalltalk":
        answer = messages["hello"]
    elif intent in {"check_availability", "request_medication", "price_inquiry"}:
        kind = {
            "check_availability": "availability",
            "request_medication": "request",
            "price_inquiry": "price",
        }[intent]
        answer = (
            messages[kind].format(meds=names) if medications else messages["missing"]
        )
        if medications and analysis.needs_clarification:
            answer += "\n\n" + messages["clarify"]
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
                    records = [
                        row.pharmacy
                        for row in repository.nearest(
                            user_location.latitude, user_location.longitude, k=5
                        )
                    ]
                lines = [messages["directory"]]
                for record in records:
                    phone = ", ".join(record.phones_e164) or messages["unknown"]
                    hours = record.opening_hours or messages["unknown"]
                    lines.append(
                        f"{record.name or messages['unnamed']} — "
                        f"{messages['phone']}: {phone}; "
                        f"{messages['hours']}: {hours} "
                        f"({record.latitude:.5f}, {record.longitude:.5f})"
                    )
                answer = "\n\n".join(lines) if records else messages["none"]
            except (FileNotFoundError, OSError):
                answer = messages["unavailable"]
    if analysis.contains_out_of_scope_request and intent != "out_of_scope":
        answer += "\n\n" + messages["refusal"]
    return {
        "answer": answer,
        "language": language,
        "transcript": analysis.input.transcript,
        "pharmacies": [record.model_dump(mode="json") for record in records],
        "analysis": analysis.model_dump(mode="json", by_alias=True),
        "disclaimer": analysis.disclaimer,
    }
