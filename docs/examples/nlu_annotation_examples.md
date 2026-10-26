# TASK 2 - Authored annotation examples

200 author-written specification examples, **not human-verified training or gold data**.
Language assignments are intended target varieties, pending native-speaker review.
Brand strings illustrate extraction only; no catalogue, availability, price or ingredient claim is made.
Canonical annotated records: [nlu_annotation_examples.json](nlu_annotation_examples.json).
Entity notation uses original-text half-open Unicode code-point spans `[start:end]`.
For every medication, normalized name, DCI and matched ID remain unset.
Questions about an unspecified pharmacy identity or hours target are marked for clarification in this context-free set.
For nearest-pharmacy requests with no location, clarify; directory lookups do not invent an answer.

## check_availability

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| check_availability.darija_ar.01 | darija_ar | واش عندكم دوليبران؟ | MEDICATION `دوليبران` [10:18] (med1) |  | false |
| check_availability.darija_ar.02 | darija_ar | كاين بانادول دابا؟ | MEDICATION `بانادول` [5:12] (med1); TIME_REF `دابا` [13:17] (span2) |  | false |
| check_availability.darija_ar.03 | darija_ar | واش متوفر أموكسيسيلين؟ | MEDICATION `أموكسيسيلين` [10:21] (med1) |  | false |
| check_availability.darija_ar.04 | darija_ar | باقي عندكم دوليبران 500 mg؟ | MEDICATION `دوليبران` [11:19] (med1); DOSAGE `500 mg` [20:26] (span2) | DOSAGE_OF span2 → med1 | false |
| check_availability.darija_ar.05 | darija_ar | عندكم أوغمنتين ولا سالا؟ | MEDICATION `أوغمنتين` [6:14] (med1) |  | false |
| check_availability.darija_latn.01 | darija_latn | wach kayn Doliprane? | MEDICATION `Doliprane` [10:19] (med1) |  | false |
| check_availability.darija_latn.02 | darija_latn | 3andkom Panadol daba? | MEDICATION `Panadol` [8:15] (med1); TIME_REF `daba` [16:20] (span2) |  | false |
| check_availability.darija_latn.03 | darija_latn | wach Amoxicilline disponible? | MEDICATION `Amoxicilline` [5:17] (med1) |  | false |
| check_availability.darija_latn.04 | darija_latn | ba9i kayn Doliprane 500 mg? | MEDICATION `Doliprane` [10:19] (med1); DOSAGE `500 mg` [20:26] (span2) | DOSAGE_OF span2 → med1 | false |
| check_availability.darija_latn.05 | darija_latn | Augmentin kayn wla sala? | MEDICATION `Augmentin` [0:9] (med1) |  | false |
| check_availability.ar.01 | ar | هل يتوفر دوليبران؟ | MEDICATION `دوليبران` [9:17] (med1) |  | false |
| check_availability.ar.02 | ar | هل بانادول متوفر الآن؟ | MEDICATION `بانادول` [3:10] (med1); TIME_REF `الآن` [17:21] (span2) |  | false |
| check_availability.ar.03 | ar | هل لديكم أموكسيسيلين؟ | MEDICATION `أموكسيسيلين` [9:20] (med1) |  | false |
| check_availability.ar.04 | ar | هل يتوفر دوليبران 500 mg؟ | MEDICATION `دوليبران` [9:17] (med1); DOSAGE `500 mg` [18:24] (span2) | DOSAGE_OF span2 → med1 | false |
| check_availability.ar.05 | ar | هل أوغمنتين موجود لديكم؟ | MEDICATION `أوغمنتين` [3:11] (med1) |  | false |
| check_availability.fr.01 | fr | Avez-vous Doliprane ? | MEDICATION `Doliprane` [10:19] (med1) |  | false |
| check_availability.fr.02 | fr | Panadol est-il disponible maintenant ? | MEDICATION `Panadol` [0:7] (med1); TIME_REF `maintenant` [26:36] (span2) |  | false |
| check_availability.fr.03 | fr | Est-ce que vous avez Amoxicilline ? | MEDICATION `Amoxicilline` [21:33] (med1) |  | false |
| check_availability.fr.04 | fr | Avez-vous Doliprane 500 mg ? | MEDICATION `Doliprane` [10:19] (med1); DOSAGE `500 mg` [20:26] (span2) | DOSAGE_OF span2 → med1 | false |
| check_availability.fr.05 | fr | Augmentin est-il en stock ? | MEDICATION `Augmentin` [0:9] (med1) |  | false |
| check_availability.mixed.01 | mixed | wach kayn Doliprane en stock ? | MEDICATION `Doliprane` [10:19] (med1) |  | false |
| check_availability.mixed.02 | mixed | عندكم Panadol disponible ? | MEDICATION `Panadol` [6:13] (med1) |  | false |
| check_availability.mixed.03 | mixed | Amoxicilline disponible daba ? | MEDICATION `Amoxicilline` [0:12] (med1); TIME_REF `daba` [24:28] (span2) |  | false |
| check_availability.mixed.04 | mixed | واش Doliprane 500 mg disponible ? | MEDICATION `Doliprane` [4:13] (med1); DOSAGE `500 mg` [14:20] (span2) | DOSAGE_OF span2 → med1 | false |
| check_availability.mixed.05 | mixed | Est-ce que Augmentin kayn 3andkom ? | MEDICATION `Augmentin` [11:20] (med1) |  | false |

## request_medication

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| request_medication.darija_ar.01 | darija_ar | بغيت جوج علب ديال دوليبران | QUANTITY `جوج علب` [5:12] (span1); MEDICATION `دوليبران` [18:26] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.darija_ar.02 | darija_ar | عافاك بغيت بانادول | MEDICATION `بانادول` [11:18] (med1) |  | false |
| request_medication.darija_ar.03 | darija_ar | بغيت علبة ديال أموكسيسيلين | QUANTITY `علبة` [5:9] (span1); MEDICATION `أموكسيسيلين` [15:26] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.darija_ar.04 | darija_ar | بغيت أوغمنتين دابا | MEDICATION `أوغمنتين` [5:13] (med1); TIME_REF `دابا` [14:18] (span2) |  | false |
| request_medication.darija_ar.05 | darija_ar | بغيت دوليبران 500 mg | MEDICATION `دوليبران` [5:13] (med1); DOSAGE `500 mg` [14:20] (span2) | DOSAGE_OF span2 → med1 | false |
| request_medication.darija_latn.01 | darija_latn | bghit 2 boites dyal Doliprane | QUANTITY `2 boites` [6:14] (span1); MEDICATION `Doliprane` [20:29] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.darija_latn.02 | darija_latn | 3afak bghit Panadol | MEDICATION `Panadol` [12:19] (med1) |  | false |
| request_medication.darija_latn.03 | darija_latn | bghit 1 boite dyal Amoxicilline | QUANTITY `1 boite` [6:13] (span1); MEDICATION `Amoxicilline` [19:31] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.darija_latn.04 | darija_latn | bghit Augmentin daba | MEDICATION `Augmentin` [6:15] (med1); TIME_REF `daba` [16:20] (span2) |  | false |
| request_medication.darija_latn.05 | darija_latn | bghit Doliprane 500 mg | MEDICATION `Doliprane` [6:15] (med1); DOSAGE `500 mg` [16:22] (span2) | DOSAGE_OF span2 → med1 | false |
| request_medication.ar.01 | ar | أريد علبتين من دوليبران | QUANTITY `علبتين` [5:11] (span1); MEDICATION `دوليبران` [15:23] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.ar.02 | ar | أود طلب بانادول | MEDICATION `بانادول` [8:15] (med1) |  | false |
| request_medication.ar.03 | ar | أريد علبة من أموكسيسيلين | QUANTITY `علبة` [5:9] (span1); MEDICATION `أموكسيسيلين` [13:24] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.ar.04 | ar | أريد أوغمنتين الآن | MEDICATION `أوغمنتين` [5:13] (med1); TIME_REF `الآن` [14:18] (span2) |  | false |
| request_medication.ar.05 | ar | أريد دوليبران 500 mg | MEDICATION `دوليبران` [5:13] (med1); DOSAGE `500 mg` [14:20] (span2) | DOSAGE_OF span2 → med1 | false |
| request_medication.fr.01 | fr | Je voudrais 2 boîtes de Doliprane | QUANTITY `2 boîtes` [12:20] (span1); MEDICATION `Doliprane` [24:33] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.fr.02 | fr | Je souhaite commander Panadol | MEDICATION `Panadol` [22:29] (med1) |  | false |
| request_medication.fr.03 | fr | Je voudrais une boîte de Amoxicilline | QUANTITY `une boîte` [12:21] (span1); MEDICATION `Amoxicilline` [25:37] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.fr.04 | fr | Je voudrais Augmentin maintenant | MEDICATION `Augmentin` [12:21] (med1); TIME_REF `maintenant` [22:32] (span2) |  | false |
| request_medication.fr.05 | fr | Je voudrais Doliprane 500 mg | MEDICATION `Doliprane` [12:21] (med1); DOSAGE `500 mg` [22:28] (span2) | DOSAGE_OF span2 → med1 | false |
| request_medication.mixed.01 | mixed | bghit 2 boîtes de Doliprane | QUANTITY `2 boîtes` [6:14] (span1); MEDICATION `Doliprane` [18:27] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.mixed.02 | mixed | بغيت Panadol s’il vous plaît | MEDICATION `Panadol` [5:12] (med1) |  | false |
| request_medication.mixed.03 | mixed | Je voudrais une boîte dyal Amoxicilline | QUANTITY `une boîte` [12:21] (span1); MEDICATION `Amoxicilline` [27:39] (med1) | QUANTITY_OF span1 → med1 | false |
| request_medication.mixed.04 | mixed | بغيت Augmentin maintenant | MEDICATION `Augmentin` [5:14] (med1); TIME_REF `maintenant` [15:25] (span2) |  | false |
| request_medication.mixed.05 | mixed | bghit Doliprane 500 mg s’il vous plaît | MEDICATION `Doliprane` [6:15] (med1); DOSAGE `500 mg` [16:22] (span2) | DOSAGE_OF span2 → med1 | false |

## pharmacy_info_phone

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| pharmacy_info_phone.darija_ar.01 | darija_ar | شنو نمرة الصيدلية؟ |  |  | true |
| pharmacy_info_phone.darija_ar.02 | darija_ar | عطيني تليفون الصيدلية عافاك |  |  | true |
| pharmacy_info_phone.darija_ar.03 | darija_ar | بغيت نمرة صيدلية ف الرباط | LOCATION `الرباط` [19:25] (span1) |  | true |
| pharmacy_info_phone.darija_ar.04 | darija_ar | كيفاش نعيط للصيدلية؟ |  |  | true |
| pharmacy_info_phone.darija_ar.05 | darija_ar | فين نلقى تليفون الصيدلية؟ |  |  | true |
| pharmacy_info_phone.darija_latn.01 | darija_latn | chno nemra dyal pharmacie? |  |  | true |
| pharmacy_info_phone.darija_latn.02 | darija_latn | 3tini telephone dyal pharmacie 3afak |  |  | true |
| pharmacy_info_phone.darija_latn.03 | darija_latn | bghit nemra dyal pharmacie f Rabat | LOCATION `Rabat` [29:34] (span1) |  | true |
| pharmacy_info_phone.darija_latn.04 | darija_latn | kifach n3ayet l pharmacie? |  |  | true |
| pharmacy_info_phone.darija_latn.05 | darija_latn | fin nel9a telephone dyal pharmacie? |  |  | true |
| pharmacy_info_phone.ar.01 | ar | ما رقم هاتف الصيدلية؟ |  |  | true |
| pharmacy_info_phone.ar.02 | ar | أريد هاتف الصيدلية من فضلك |  |  | true |
| pharmacy_info_phone.ar.03 | ar | ما رقم صيدلية في الرباط؟ | LOCATION `الرباط` [17:23] (span1) |  | true |
| pharmacy_info_phone.ar.04 | ar | كيف أتصل بالصيدلية؟ |  |  | true |
| pharmacy_info_phone.ar.05 | ar | أين أجد رقم الصيدلية؟ |  |  | true |
| pharmacy_info_phone.fr.01 | fr | Quel est le numéro de la pharmacie ? |  |  | true |
| pharmacy_info_phone.fr.02 | fr | Donnez-moi le téléphone de la pharmacie |  |  | true |
| pharmacy_info_phone.fr.03 | fr | Je cherche le numéro d’une pharmacie à Rabat | LOCATION `Rabat` [39:44] (span1) |  | true |
| pharmacy_info_phone.fr.04 | fr | Comment appeler la pharmacie ? |  |  | true |
| pharmacy_info_phone.fr.05 | fr | Où trouver le numéro de téléphone de la pharmacie ? |  |  | true |
| pharmacy_info_phone.mixed.01 | mixed | chno le numéro de la pharmacie ? |  |  | true |
| pharmacy_info_phone.mixed.02 | mixed | عطيني téléphone de la pharmacie |  |  | true |
| pharmacy_info_phone.mixed.03 | mixed | Je cherche nemra dyal pharmacie f Rabat | LOCATION `Rabat` [34:39] (span1) |  | true |
| pharmacy_info_phone.mixed.04 | mixed | كيفاش نعيط à la pharmacie ? |  |  | true |
| pharmacy_info_phone.mixed.05 | mixed | fin nel9a le numéro de la pharmacie ? |  |  | true |

## pharmacy_info_location

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| pharmacy_info_location.darija_ar.01 | darija_ar | فين كاينة الصيدلية؟ |  |  | true |
| pharmacy_info_location.darija_ar.02 | darija_ar | بغيت عنوان الصيدلية |  |  | true |
| pharmacy_info_location.darija_ar.03 | darija_ar | فين أقرب صيدلية ف الرباط؟ | LOCATION `الرباط` [18:24] (span1) |  | false |
| pharmacy_info_location.darija_ar.04 | darija_ar | كاينة شي صيدلية حدايا؟ |  |  | true |
| pharmacy_info_location.darija_ar.05 | darija_ar | فين كاينة شي صيدلية ف مراكش؟ | LOCATION `مراكش` [22:27] (span1) |  | false |
| pharmacy_info_location.darija_latn.01 | darija_latn | fin kayna pharmacie? |  |  | true |
| pharmacy_info_location.darija_latn.02 | darija_latn | bghit adresse dyal pharmacie |  |  | true |
| pharmacy_info_location.darija_latn.03 | darija_latn | fin a9rab pharmacie f Rabat? | LOCATION `Rabat` [22:27] (span1) |  | false |
| pharmacy_info_location.darija_latn.04 | darija_latn | kayna chi pharmacie 7daya? |  |  | true |
| pharmacy_info_location.darija_latn.05 | darija_latn | fin kayna chi pharmacie f Marrakech? | LOCATION `Marrakech` [26:35] (span1) |  | false |
| pharmacy_info_location.ar.01 | ar | أين تقع الصيدلية؟ |  |  | true |
| pharmacy_info_location.ar.02 | ar | أريد عنوان الصيدلية |  |  | true |
| pharmacy_info_location.ar.03 | ar | أين أقرب صيدلية في الرباط؟ | LOCATION `الرباط` [19:25] (span1) |  | false |
| pharmacy_info_location.ar.04 | ar | هل توجد صيدلية قريبة مني؟ |  |  | true |
| pharmacy_info_location.ar.05 | ar | أين توجد صيدلية في مراكش؟ | LOCATION `مراكش` [19:24] (span1) |  | false |
| pharmacy_info_location.fr.01 | fr | Où se trouve la pharmacie ? |  |  | true |
| pharmacy_info_location.fr.02 | fr | Je cherche l’adresse de la pharmacie |  |  | true |
| pharmacy_info_location.fr.03 | fr | Où est la pharmacie la plus proche à Rabat ? | LOCATION `Rabat` [37:42] (span1) |  | false |
| pharmacy_info_location.fr.04 | fr | Y a-t-il une pharmacie près de moi ? |  |  | true |
| pharmacy_info_location.fr.05 | fr | Où trouver une pharmacie à Marrakech ? | LOCATION `Marrakech` [27:36] (span1) |  | false |
| pharmacy_info_location.mixed.01 | mixed | fin kayna la pharmacie ? |  |  | true |
| pharmacy_info_location.mixed.02 | mixed | بغيت l’adresse de la pharmacie |  |  | true |
| pharmacy_info_location.mixed.03 | mixed | Où est a9rab pharmacie f Rabat ? | LOCATION `Rabat` [25:30] (span1) |  | false |
| pharmacy_info_location.mixed.04 | mixed | كاينة une pharmacie près de moi ? |  |  | true |
| pharmacy_info_location.mixed.05 | mixed | fin kayna une pharmacie à Marrakech ? | LOCATION `Marrakech` [26:35] (span1) |  | false |

## pharmacy_info_hours

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| pharmacy_info_hours.darija_ar.01 | darija_ar | الصيدلية محلولة دابا؟ | TIME_REF `دابا` [16:20] (span1) |  | true |
| pharmacy_info_hours.darija_ar.02 | darija_ar | فوقاش كتسد الصيدلية؟ |  |  | true |
| pharmacy_info_hours.darija_ar.03 | darija_ar | شحال كتفتح الصيدلية؟ |  |  | true |
| pharmacy_info_hours.darija_ar.04 | darija_ar | كاينة شي صيدلية ديال الحراسة الليلة؟ | TIME_REF `الليلة` [29:35] (span1) |  | true |
| pharmacy_info_hours.darija_ar.05 | darija_ar | غدا الصيدلية محلولة؟ | TIME_REF `غدا` [0:3] (span1) |  | true |
| pharmacy_info_hours.darija_latn.01 | darija_latn | pharmacie me7loula daba? | TIME_REF `daba` [19:23] (span1) |  | true |
| pharmacy_info_hours.darija_latn.02 | darija_latn | fo9ach katsed pharmacie? |  |  | true |
| pharmacy_info_hours.darija_latn.03 | darija_latn | ch7al kat7el pharmacie? |  |  | true |
| pharmacy_info_hours.darija_latn.04 | darija_latn | kayna pharmacie de garde lila? | TIME_REF `lila` [25:29] (span1) |  | true |
| pharmacy_info_hours.darija_latn.05 | darija_latn | ghdda pharmacie me7loula? | TIME_REF `ghdda` [0:5] (span1) |  | true |
| pharmacy_info_hours.ar.01 | ar | هل الصيدلية مفتوحة الآن؟ | TIME_REF `الآن` [19:23] (span1) |  | true |
| pharmacy_info_hours.ar.02 | ar | متى تغلق الصيدلية؟ |  |  | true |
| pharmacy_info_hours.ar.03 | ar | متى تفتح الصيدلية؟ |  |  | true |
| pharmacy_info_hours.ar.04 | ar | هل توجد صيدلية مناوبة الليلة؟ | TIME_REF `الليلة` [22:28] (span1) |  | true |
| pharmacy_info_hours.ar.05 | ar | هل تفتح الصيدلية غدا؟ | TIME_REF `غدا` [17:20] (span1) |  | true |
| pharmacy_info_hours.fr.01 | fr | La pharmacie est-elle ouverte maintenant ? | TIME_REF `maintenant` [30:40] (span1) |  | true |
| pharmacy_info_hours.fr.02 | fr | À quelle heure ferme la pharmacie ? |  |  | true |
| pharmacy_info_hours.fr.03 | fr | Quand ouvre la pharmacie ? |  |  | true |
| pharmacy_info_hours.fr.04 | fr | Quelle pharmacie est de garde ce soir ? | TIME_REF `ce soir` [30:37] (span1) |  | true |
| pharmacy_info_hours.fr.05 | fr | La pharmacie ouvre-t-elle demain ? | TIME_REF `demain` [26:32] (span1) |  | true |
| pharmacy_info_hours.mixed.01 | mixed | wach la pharmacie ouverte daba ? | TIME_REF `daba` [26:30] (span1) |  | true |
| pharmacy_info_hours.mixed.02 | mixed | فوقاش ferme la pharmacie ? |  |  | true |
| pharmacy_info_hours.mixed.03 | mixed | Quand kat7el la pharmacie ? |  |  | true |
| pharmacy_info_hours.mixed.04 | mixed | كاينة une pharmacie de garde الليلة؟ | TIME_REF `الليلة` [29:35] (span1) |  | true |
| pharmacy_info_hours.mixed.05 | mixed | ghdda la pharmacie sera ouverte ? | TIME_REF `ghdda` [0:5] (span1) |  | true |

## price_inquiry

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| price_inquiry.darija_ar.01 | darija_ar | بشحال دوليبران؟ | MEDICATION `دوليبران` [6:14] (med1) |  | false |
| price_inquiry.darija_ar.02 | darija_ar | شحال ثمن بانادول؟ | MEDICATION `بانادول` [9:16] (med1) |  | false |
| price_inquiry.darija_ar.03 | darija_ar | بغيت نعرف ثمن أموكسيسيلين | MEDICATION `أموكسيسيلين` [14:25] (med1) |  | false |
| price_inquiry.darija_ar.04 | darija_ar | دوليبران 500 mg بشحال؟ | MEDICATION `دوليبران` [0:8] (med1); DOSAGE `500 mg` [9:15] (span2) | DOSAGE_OF span2 → med1 | false |
| price_inquiry.darija_ar.05 | darija_ar | شحال كيدير أوغمنتين؟ | MEDICATION `أوغمنتين` [11:19] (med1) |  | false |
| price_inquiry.darija_latn.01 | darija_latn | bch7al Doliprane? | MEDICATION `Doliprane` [7:16] (med1) |  | false |
| price_inquiry.darija_latn.02 | darija_latn | ch7al taman Panadol? | MEDICATION `Panadol` [12:19] (med1) |  | false |
| price_inquiry.darija_latn.03 | darija_latn | bghit n3ref prix dyal Amoxicilline | MEDICATION `Amoxicilline` [22:34] (med1) |  | false |
| price_inquiry.darija_latn.04 | darija_latn | Doliprane 500 mg bch7al? | MEDICATION `Doliprane` [0:9] (med1); DOSAGE `500 mg` [10:16] (span2) | DOSAGE_OF span2 → med1 | false |
| price_inquiry.darija_latn.05 | darija_latn | ch7al kaydir Augmentin? | MEDICATION `Augmentin` [13:22] (med1) |  | false |
| price_inquiry.ar.01 | ar | ما سعر دوليبران؟ | MEDICATION `دوليبران` [7:15] (med1) |  | false |
| price_inquiry.ar.02 | ar | كم ثمن بانادول؟ | MEDICATION `بانادول` [7:14] (med1) |  | false |
| price_inquiry.ar.03 | ar | أريد معرفة سعر أموكسيسيلين | MEDICATION `أموكسيسيلين` [15:26] (med1) |  | false |
| price_inquiry.ar.04 | ar | ما سعر دوليبران 500 mg؟ | MEDICATION `دوليبران` [7:15] (med1); DOSAGE `500 mg` [16:22] (span2) | DOSAGE_OF span2 → med1 | false |
| price_inquiry.ar.05 | ar | كم يكلف أوغمنتين؟ | MEDICATION `أوغمنتين` [8:16] (med1) |  | false |
| price_inquiry.fr.01 | fr | Quel est le prix de Doliprane ? | MEDICATION `Doliprane` [20:29] (med1) |  | false |
| price_inquiry.fr.02 | fr | Combien coûte Panadol ? | MEDICATION `Panadol` [14:21] (med1) |  | false |
| price_inquiry.fr.03 | fr | Je voudrais connaître le prix de Amoxicilline | MEDICATION `Amoxicilline` [33:45] (med1) |  | false |
| price_inquiry.fr.04 | fr | Quel est le prix de Doliprane 500 mg ? | MEDICATION `Doliprane` [20:29] (med1); DOSAGE `500 mg` [30:36] (span2) | DOSAGE_OF span2 → med1 | false |
| price_inquiry.fr.05 | fr | Combien coûte Augmentin ? | MEDICATION `Augmentin` [14:23] (med1) |  | false |
| price_inquiry.mixed.01 | mixed | bch7al le Doliprane ? | MEDICATION `Doliprane` [10:19] (med1) |  | false |
| price_inquiry.mixed.02 | mixed | شحال le prix de Panadol ? | MEDICATION `Panadol` [16:23] (med1) |  | false |
| price_inquiry.mixed.03 | mixed | Je voudrais n3ref prix dyal Amoxicilline | MEDICATION `Amoxicilline` [28:40] (med1) |  | false |
| price_inquiry.mixed.04 | mixed | دوليبران 500 mg quel prix ? | MEDICATION `دوليبران` [0:8] (med1); DOSAGE `500 mg` [9:15] (span2) | DOSAGE_OF span2 → med1 | false |
| price_inquiry.mixed.05 | mixed | ch7al coûte Augmentin ? | MEDICATION `Augmentin` [12:21] (med1) |  | false |

## greeting_smalltalk

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| greeting_smalltalk.darija_ar.01 | darija_ar | السلام عليكم |  |  | false |
| greeting_smalltalk.darija_ar.02 | darija_ar | سلام |  |  | false |
| greeting_smalltalk.darija_ar.03 | darija_ar | شكرا بزاف |  |  | false |
| greeting_smalltalk.darija_ar.04 | darija_ar | صباح الخير |  |  | false |
| greeting_smalltalk.darija_ar.05 | darija_ar | لباس عليكم؟ |  |  | false |
| greeting_smalltalk.darija_latn.01 | darija_latn | salam 3likom |  |  | false |
| greeting_smalltalk.darija_latn.02 | darija_latn | salam |  |  | false |
| greeting_smalltalk.darija_latn.03 | darija_latn | chokran bzzaf |  |  | false |
| greeting_smalltalk.darija_latn.04 | darija_latn | sba7 lkhir |  |  | false |
| greeting_smalltalk.darija_latn.05 | darija_latn | labas 3likom? |  |  | false |
| greeting_smalltalk.ar.01 | ar | السلام عليكم ورحمة الله |  |  | false |
| greeting_smalltalk.ar.02 | ar | مرحبا |  |  | false |
| greeting_smalltalk.ar.03 | ar | شكرا لكم |  |  | false |
| greeting_smalltalk.ar.04 | ar | صباح الخير لكم |  |  | false |
| greeting_smalltalk.ar.05 | ar | كيف حالكم؟ |  |  | false |
| greeting_smalltalk.fr.01 | fr | Bonjour |  |  | false |
| greeting_smalltalk.fr.02 | fr | Salut |  |  | false |
| greeting_smalltalk.fr.03 | fr | Merci beaucoup |  |  | false |
| greeting_smalltalk.fr.04 | fr | Bonsoir |  |  | false |
| greeting_smalltalk.fr.05 | fr | Comment allez-vous ? |  |  | false |
| greeting_smalltalk.mixed.01 | mixed | salam, bonjour |  |  | false |
| greeting_smalltalk.mixed.02 | mixed | سلام et bonsoir |  |  | false |
| greeting_smalltalk.mixed.03 | mixed | Merci bzzaf |  |  | false |
| greeting_smalltalk.mixed.04 | mixed | صباح الخير, bonjour |  |  | false |
| greeting_smalltalk.mixed.05 | mixed | labas, comment allez-vous ? |  |  | false |

## out_of_scope

| ID | Variety | Text | Entities | Relations | Clarify |
| --- | --- | --- | --- | --- | --- |
| out_of_scope.darija_ar.01 | darija_ar | شنو ناخد لوجع الراس؟ |  |  | false |
| out_of_scope.darija_ar.02 | darija_ar | شحال من حبة ناخد ديال دوليبران؟ | MEDICATION `دوليبران` [22:30] (med1) |  | false |
| out_of_scope.darija_ar.03 | darija_ar | واش نبدل هاد الدوا بشي واحد آخر؟ |  |  | false |
| out_of_scope.darija_ar.04 | darija_ar | شخص ليا هاد الأعراض |  |  | false |
| out_of_scope.darija_ar.05 | darija_ar | شنو نتيجة الماتش؟ |  |  | false |
| out_of_scope.darija_latn.01 | darija_latn | chno nakhod l sda3? |  |  | false |
| out_of_scope.darija_latn.02 | darija_latn | ch7al men 7ebba nakhod dyal Doliprane? | MEDICATION `Doliprane` [28:37] (med1) |  | false |
| out_of_scope.darija_latn.03 | darija_latn | wach nbdel had dwa b chi wa7ed akhor? |  |  | false |
| out_of_scope.darija_latn.04 | darija_latn | chakhess lia had l a3rad |  |  | false |
| out_of_scope.darija_latn.05 | darija_latn | chno resultat dyal match? |  |  | false |
| out_of_scope.ar.01 | ar | ماذا أتناول لعلاج الصداع؟ |  |  | false |
| out_of_scope.ar.02 | ar | كم حبة من دوليبران يجب أن أتناول؟ | MEDICATION `دوليبران` [10:18] (med1) |  | false |
| out_of_scope.ar.03 | ar | هل أستبدل هذا الدواء بآخر؟ |  |  | false |
| out_of_scope.ar.04 | ar | شخص هذه الأعراض من فضلك |  |  | false |
| out_of_scope.ar.05 | ar | ما نتيجة المباراة؟ |  |  | false |
| out_of_scope.fr.01 | fr | Quel médicament prendre contre le mal de tête ? |  |  | false |
| out_of_scope.fr.02 | fr | Combien de comprimés de Doliprane dois-je prendre ? | MEDICATION `Doliprane` [24:33] (med1) |  | false |
| out_of_scope.fr.03 | fr | Puis-je remplacer ce médicament par un autre ? |  |  | false |
| out_of_scope.fr.04 | fr | Pouvez-vous diagnostiquer ces symptômes ? |  |  | false |
| out_of_scope.fr.05 | fr | Quel est le résultat du match ? |  |  | false |
| out_of_scope.mixed.01 | mixed | chno prendre pour le mal de tête ? |  |  | false |
| out_of_scope.mixed.02 | mixed | شحال de comprimés de Doliprane ناخد؟ | MEDICATION `Doliprane` [21:30] (med1) |  | false |
| out_of_scope.mixed.03 | mixed | wach je peux remplacer had dwa ? |  |  | false |
| out_of_scope.mixed.04 | mixed | شخص ليا ces symptômes |  |  | false |
| out_of_scope.mixed.05 | mixed | chno le résultat du match ? |  |  | false |
