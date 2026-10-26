# Gold candidates - human review required

These 100 assistant-authored examples are unverified candidates, not gold data.
Review language, intent, exact spans, relations and clarification flags against docs/02_nlu_spec.md.
No availability or medical fact is asserted by an example request.

| ID | Variety | Intent | Text | Entity spans |
| --- | --- | --- | --- | --- |
| gold_candidate_001 | darija_ar | check_availability | ممكن تشوفو ليا واش دوليبران متوفر فالمخزون؟ | MEDICATION [19:27] دوليبران |
| gold_candidate_002 | darija_ar | check_availability | بالنسبة لبانادول، واش باقي شي علب؟ | MEDICATION [9:16] بانادول |
| gold_candidate_003 | darija_latn | check_availability | t9dro tchoufo lia wach Doliprane f stock? | MEDICATION [23:32] Doliprane |
| gold_candidate_004 | darija_latn | check_availability | bnisba l Panadol, wach ba9i chi boites? | MEDICATION [9:16] Panadol |
| gold_candidate_005 | ar | check_availability | هل يمكن التحقق من وجود دوليبران في المخزون؟ | MEDICATION [23:31] دوليبران |
| gold_candidate_006 | ar | check_availability | بالنسبة إلى بانادول، هل بقيت منه علب؟ | MEDICATION [12:19] بانادول |
| gold_candidate_007 | fr | check_availability | Pourriez-vous vérifier votre stock de Doliprane ? | MEDICATION [38:47] Doliprane |
| gold_candidate_008 | fr | check_availability | Concernant Panadol, en reste-t-il des boîtes ? | MEDICATION [11:18] Panadol |
| gold_candidate_009 | mixed | check_availability | t9dro vérifier le stock de Doliprane ? | MEDICATION [27:36] Doliprane |
| gold_candidate_010 | mixed | check_availability | بالنسبة لـ Panadol, il en reste ? | MEDICATION [11:18] Panadol |
| gold_candidate_011 | darija_ar | request_medication | إلى ممكن، بغيت نطلب دوليبران من عندكم | MEDICATION [20:28] دوليبران |
| gold_candidate_012 | darija_ar | request_medication | سجلو ليا طلب ديال بانادول عافاكم | MEDICATION [18:25] بانادول |
| gold_candidate_013 | darija_latn | request_medication | ila momkin, bghit ntleb Doliprane men 3andkom | MEDICATION [24:33] Doliprane |
| gold_candidate_014 | darija_latn | request_medication | sejjlo lia taleb dyal Panadol 3afakom | MEDICATION [22:29] Panadol |
| gold_candidate_015 | ar | request_medication | إن أمكن، أرجو تسجيل طلب دوليبران | MEDICATION [24:32] دوليبران |
| gold_candidate_016 | ar | request_medication | من فضلكم سجلوا لي طلب بانادول | MEDICATION [22:29] بانادول |
| gold_candidate_017 | fr | request_medication | Si possible, enregistrez ma demande de Doliprane | MEDICATION [39:48] Doliprane |
| gold_candidate_018 | fr | request_medication | Veuillez noter ma demande de Panadol | MEDICATION [29:36] Panadol |
| gold_candidate_019 | mixed | request_medication | ila momkin, enregistrez ma demande de Doliprane | MEDICATION [38:47] Doliprane |
| gold_candidate_020 | mixed | request_medication | سجلو ليا une demande de Panadol | MEDICATION [24:31] Panadol |
| gold_candidate_021 | darija_ar | pharmacy_info_phone | محتاج رقم باش نتاصل بشي صيدلية فالرباط | LOCATION [32:38] الرباط |
| gold_candidate_022 | darija_ar | pharmacy_info_phone | عافاكم كيفاش نتاصل بصيدلية المثال؟ | PHARMACY_NAME [20:33] صيدلية المثال |
| gold_candidate_023 | darija_latn | pharmacy_info_phone | me7taj numero bach netasel b chi pharmacie f Rabat | LOCATION [45:50] Rabat |
| gold_candidate_024 | darija_latn | pharmacy_info_phone | 3afakom kifach netasel b Pharmacie Exemple? | PHARMACY_NAME [25:42] Pharmacie Exemple |
| gold_candidate_025 | ar | pharmacy_info_phone | أحتاج وسيلة اتصال هاتفية بصيدلية في الرباط | LOCATION [36:42] الرباط |
| gold_candidate_026 | ar | pharmacy_info_phone | من فضلكم كيف أتصل هاتفيا بصيدلية المثال؟ | PHARMACY_NAME [26:39] صيدلية المثال |
| gold_candidate_027 | fr | pharmacy_info_phone | Je souhaite joindre par téléphone une pharmacie à Rabat | LOCATION [50:55] Rabat |
| gold_candidate_028 | fr | pharmacy_info_phone | Pour joindre Pharmacie Exemple, quel numéro utiliser ? | PHARMACY_NAME [13:30] Pharmacie Exemple |
| gold_candidate_029 | mixed | pharmacy_info_phone | me7taj un contact téléphonique dyal pharmacie f Rabat | LOCATION [48:53] Rabat |
| gold_candidate_030 | mixed | pharmacy_info_phone | بغيت نتاصل par téléphone à Pharmacie Exemple | PHARMACY_NAME [27:44] Pharmacie Exemple |
| gold_candidate_031 | darija_ar | pharmacy_info_location | وريو ليا البلاصة ديال شي صيدلية فمراكش | LOCATION [33:38] مراكش |
| gold_candidate_032 | darija_ar | pharmacy_info_location | أنا فالرباط وبغيت نعرف فين نمشي للصيدلية | LOCATION [5:11] الرباط |
| gold_candidate_033 | darija_latn | pharmacy_info_location | werriw lia blassa dyal chi pharmacie f Marrakech | LOCATION [39:48] Marrakech |
| gold_candidate_034 | darija_latn | pharmacy_info_location | ana f Rabat, bghit n3ref fin nemchi l pharmacie | LOCATION [6:11] Rabat |
| gold_candidate_035 | ar | pharmacy_info_location | دلوني على موقع صيدلية في مراكش | LOCATION [25:30] مراكش |
| gold_candidate_036 | ar | pharmacy_info_location | أنا في الرباط وأبحث عن مكان صيدلية | LOCATION [7:13] الرباط |
| gold_candidate_037 | fr | pharmacy_info_location | Indiquez-moi où trouver une pharmacie dans Marrakech | LOCATION [43:52] Marrakech |
| gold_candidate_038 | fr | pharmacy_info_location | Je suis à Rabat : vers quelle pharmacie me diriger ? | LOCATION [10:15] Rabat |
| gold_candidate_039 | mixed | pharmacy_info_location | werriw lia la localisation d’une pharmacie f Marrakech | LOCATION [45:54] Marrakech |
| gold_candidate_040 | mixed | pharmacy_info_location | أنا في Rabat, où trouver une pharmacie ? | LOCATION [7:12] Rabat |
| gold_candidate_041 | darija_ar | pharmacy_info_hours | بغيت نتاكد واش كاينة الحراسة فالرباط الليلة | LOCATION [30:36] الرباط; TIME_REF [37:43] الليلة |
| gold_candidate_042 | darija_ar | pharmacy_info_hours | واش عندكم وقت الإغلاق ديال صيدلية المثال؟ | PHARMACY_NAME [27:40] صيدلية المثال |
| gold_candidate_043 | darija_latn | pharmacy_info_hours | bghit net2eked men garde f Rabat had lila | LOCATION [27:32] Rabat; TIME_REF [37:41] lila |
| gold_candidate_044 | darija_latn | pharmacy_info_hours | wach 3andkom wa9t lighla9 dyal Pharmacie Exemple? | PHARMACY_NAME [31:48] Pharmacie Exemple |
| gold_candidate_045 | ar | pharmacy_info_hours | أرغب في معرفة الصيدلية المناوبة في الرباط هذه الليلة | LOCATION [35:41] الرباط; TIME_REF [46:52] الليلة |
| gold_candidate_046 | ar | pharmacy_info_hours | هل لديكم موعد إغلاق صيدلية المثال؟ | PHARMACY_NAME [20:33] صيدلية المثال |
| gold_candidate_047 | fr | pharmacy_info_hours | Je cherche les horaires de garde à Rabat pour ce soir | LOCATION [35:40] Rabat; TIME_REF [46:53] ce soir |
| gold_candidate_048 | fr | pharmacy_info_hours | Connaissez-vous l’heure de fermeture de Pharmacie Exemple ? | PHARMACY_NAME [40:57] Pharmacie Exemple |
| gold_candidate_049 | mixed | pharmacy_info_hours | bghit confirmer la garde f Rabat ce soir | LOCATION [27:32] Rabat; TIME_REF [33:40] ce soir |
| gold_candidate_050 | mixed | pharmacy_info_hours | واش عندكم l’heure de fermeture de Pharmacie Exemple ? | PHARMACY_NAME [34:51] Pharmacie Exemple |
| gold_candidate_051 | darija_ar | price_inquiry | عافاكم بغيت غير الثمن ديال دوليبران | MEDICATION [27:35] دوليبران |
| gold_candidate_052 | darija_ar | price_inquiry | قبل ما نطلب بانادول، نقدر نعرف الثمن؟ | MEDICATION [12:19] بانادول |
| gold_candidate_053 | darija_latn | price_inquiry | 3afakom bghit ghir taman dyal Doliprane | MEDICATION [30:39] Doliprane |
| gold_candidate_054 | darija_latn | price_inquiry | 9bel ma ntleb Panadol, n9der n3ref taman? | MEDICATION [14:21] Panadol |
| gold_candidate_055 | ar | price_inquiry | من فضلكم أريد الاستفسار عن ثمن دوليبران فقط | MEDICATION [31:39] دوليبران |
| gold_candidate_056 | ar | price_inquiry | قبل طلب بانادول، هل يمكن معرفة الثمن؟ | MEDICATION [8:15] بانادول |
| gold_candidate_057 | fr | price_inquiry | Pourriez-vous m’indiquer le tarif de Doliprane ? | MEDICATION [37:46] Doliprane |
| gold_candidate_058 | fr | price_inquiry | Avant de demander Panadol, j’aimerais connaître son coût | MEDICATION [18:25] Panadol |
| gold_candidate_059 | mixed | price_inquiry | 3afakom, juste le tarif de Doliprane | MEDICATION [27:36] Doliprane |
| gold_candidate_060 | mixed | price_inquiry | قبل الطلب ديال Panadol, quel coût ? | MEDICATION [15:22] Panadol |
| gold_candidate_061 | darija_ar | greeting_smalltalk | سلام عليكم، نتمنى تكونو بخير | None |
| gold_candidate_062 | darija_ar | greeting_smalltalk | شكرا ليكم على المساعدة | None |
| gold_candidate_063 | darija_latn | greeting_smalltalk | salam 3likom, netmenna tkono bikhir | None |
| gold_candidate_064 | darija_latn | greeting_smalltalk | chokran likom 3la lmosa3ada | None |
| gold_candidate_065 | ar | greeting_smalltalk | تحية طيبة لفريق الصيدلية | None |
| gold_candidate_066 | ar | greeting_smalltalk | أشكركم على حسن تعاونكم | None |
| gold_candidate_067 | fr | greeting_smalltalk | Toutes mes salutations à votre équipe | None |
| gold_candidate_068 | fr | greeting_smalltalk | Je vous remercie pour votre aide | None |
| gold_candidate_069 | mixed | greeting_smalltalk | salam à toute l’équipe, labas ? | None |
| gold_candidate_070 | mixed | greeting_smalltalk | شكرا ليكم pour votre aide | None |
| gold_candidate_071 | darija_ar | out_of_scope | عندي أعراض وبغيتكم تشخصو ليا المرض | None |
| gold_candidate_072 | darija_ar | out_of_scope | واش نقدر نعوض دوليبران بدوا آخر؟ | MEDICATION [14:22] دوليبران |
| gold_candidate_073 | darija_latn | out_of_scope | 3andi a3rad, bghitkom tchakhso lia lmarad | None |
| gold_candidate_074 | darija_latn | out_of_scope | wach n9der n3awed Doliprane b dwa akhor? | MEDICATION [18:27] Doliprane |
| gold_candidate_075 | ar | out_of_scope | أعاني أعراضا وأريد تشخيص المرض | None |
| gold_candidate_076 | ar | out_of_scope | هل يمكن استبدال دوليبران بدواء آخر؟ | MEDICATION [16:24] دوليبران |
| gold_candidate_077 | fr | out_of_scope | J’ai des symptômes, pouvez-vous poser un diagnostic ? | None |
| gold_candidate_078 | fr | out_of_scope | Par quel autre médicament puis-je remplacer Doliprane ? | MEDICATION [44:53] Doliprane |
| gold_candidate_079 | mixed | out_of_scope | عندي des symptômes, pouvez-vous diagnostiquer ? | None |
| gold_candidate_080 | mixed | out_of_scope | wach je peux remplacer Doliprane par un autre médicament ? | MEDICATION [23:32] Doliprane |
| gold_candidate_081 | darija_ar | request_medication | بغيت 2 علب ديال دوليبران و1 علبة ديال بانادول | QUANTITY [5:10] 2 علب; MEDICATION [16:24] دوليبران; QUANTITY [26:32] 1 علبة; MEDICATION [38:45] بانادول |
| gold_candidate_082 | darija_ar | check_availability | ما عرفت الاسم، واش كاين عندكم هاد الدوا؟ | None |
| gold_candidate_083 | darija_ar | price_inquiry | بغيت نسول على الثمن ولكن ما عنديش اسم الدوا | None |
| gold_candidate_084 | darija_ar | out_of_scope | دوليبران كاين؟ وزيد قولو ليا شحال من حبة ناخد | MEDICATION [0:8] دوليبران |
| gold_candidate_085 | darija_latn | request_medication | bghit 2 boites dyal Doliprane w 1 boite dyal Panadol | QUANTITY [6:14] 2 boites; MEDICATION [20:29] Doliprane; QUANTITY [32:39] 1 boite; MEDICATION [45:52] Panadol |
| gold_candidate_086 | darija_latn | check_availability | ma 3reftch smiya, wach kayn 3andkom had dwa? | None |
| gold_candidate_087 | darija_latn | price_inquiry | bghit nsowel 3la taman, walakin ma 3andich smit dwa | None |
| gold_candidate_088 | darija_latn | out_of_scope | Doliprane kayn? o golo lia ch7al men 7ebba nakhod | MEDICATION [0:9] Doliprane |
| gold_candidate_089 | ar | request_medication | أريد 2 علب من دوليبران و1 علبة من بانادول | QUANTITY [5:10] 2 علب; MEDICATION [14:22] دوليبران; QUANTITY [24:30] 1 علبة; MEDICATION [34:41] بانادول |
| gold_candidate_090 | ar | check_availability | لا أعرف الاسم، هل هذا الدواء متوفر لديكم؟ | None |
| gold_candidate_091 | ar | price_inquiry | أريد السؤال عن السعر ولكن اسم الدواء غير معروف لدي | None |
| gold_candidate_092 | ar | out_of_scope | هل دوليبران متوفر، وكم حبة يجب أن أتناول؟ | MEDICATION [3:11] دوليبران |
| gold_candidate_093 | fr | request_medication | Veuillez noter 2 boîtes de Doliprane et 1 boîte de Panadol | QUANTITY [15:23] 2 boîtes; MEDICATION [27:36] Doliprane; QUANTITY [40:47] 1 boîte; MEDICATION [51:58] Panadol |
| gold_candidate_094 | fr | check_availability | J’ai oublié le nom : avez-vous ce médicament ? | None |
| gold_candidate_095 | fr | price_inquiry | Je demande le prix, mais je ne connais pas le nom du produit | None |
| gold_candidate_096 | fr | out_of_scope | Doliprane est-il disponible, et combien de comprimés dois-je prendre ? | MEDICATION [0:9] Doliprane |
| gold_candidate_097 | mixed | request_medication | بغيت 2 boîtes de Doliprane و1 boîte de Panadol | QUANTITY [5:13] 2 boîtes; MEDICATION [17:26] Doliprane; QUANTITY [28:35] 1 boîte; MEDICATION [39:46] Panadol |
| gold_candidate_098 | mixed | check_availability | ma 3reftch le nom, واش ce médicament disponible ? | None |
| gold_candidate_099 | mixed | price_inquiry | بغيت le prix, walakin je ne connais pas le nom | None |
| gold_candidate_100 | mixed | out_of_scope | Doliprane disponible ? وقولو ليا combien de comprimés prendre | MEDICATION [0:9] Doliprane |
