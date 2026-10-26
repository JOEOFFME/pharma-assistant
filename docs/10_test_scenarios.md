# End-to-end text scenarios

Observed: 33/40 matching primary intents. Failures retained.

| Scenario | Message | Expected | Actual | Pass |
| --- | --- | --- | --- | --- |
| check_availability.darija_ar.01 | واش عندكم دوليبران؟ | check_availability | check_availability | True |
| request_medication.darija_ar.01 | بغيت جوج علب ديال دوليبران | request_medication | request_medication | True |
| pharmacy_info_phone.darija_ar.01 | شنو نمرة الصيدلية؟ | pharmacy_info_phone | pharmacy_info_phone | True |
| pharmacy_info_location.darija_ar.01 | فين كاينة الصيدلية؟ | pharmacy_info_location | check_availability | False |
| pharmacy_info_hours.darija_ar.01 | الصيدلية محلولة دابا؟ | pharmacy_info_hours | out_of_scope | False |
| out_of_scope.darija_ar.01 | شنو ناخد لوجع الراس؟ | out_of_scope | out_of_scope | True |
| price_inquiry.darija_ar.01 | بشحال دوليبران؟ | price_inquiry | price_inquiry | True |
| greeting_smalltalk.darija_ar.01 | السلام عليكم | greeting_smalltalk | greeting_smalltalk | True |
| check_availability.darija_latn.01 | wach kayn Doliprane? | check_availability | check_availability | True |
| request_medication.darija_latn.01 | bghit 2 boites dyal Doliprane | request_medication | request_medication | True |
| pharmacy_info_phone.darija_latn.01 | chno nemra dyal pharmacie? | pharmacy_info_phone | out_of_scope | False |
| pharmacy_info_location.darija_latn.01 | fin kayna pharmacie? | pharmacy_info_location | check_availability | False |
| pharmacy_info_hours.darija_latn.01 | pharmacie me7loula daba? | pharmacy_info_hours | out_of_scope | False |
| out_of_scope.darija_latn.01 | chno nakhod l sda3? | out_of_scope | out_of_scope | True |
| price_inquiry.darija_latn.01 | bch7al Doliprane? | price_inquiry | price_inquiry | True |
| greeting_smalltalk.darija_latn.01 | salam 3likom | greeting_smalltalk | greeting_smalltalk | True |
| check_availability.ar.01 | هل يتوفر دوليبران؟ | check_availability | check_availability | True |
| request_medication.ar.01 | أريد علبتين من دوليبران | request_medication | request_medication | True |
| pharmacy_info_phone.ar.01 | ما رقم هاتف الصيدلية؟ | pharmacy_info_phone | pharmacy_info_phone | True |
| pharmacy_info_location.ar.01 | أين تقع الصيدلية؟ | pharmacy_info_location | pharmacy_info_location | True |
| pharmacy_info_hours.ar.01 | هل الصيدلية مفتوحة الآن؟ | pharmacy_info_hours | pharmacy_info_hours | True |
| out_of_scope.ar.01 | ماذا أتناول لعلاج الصداع؟ | out_of_scope | out_of_scope | True |
| price_inquiry.ar.01 | ما سعر دوليبران؟ | price_inquiry | price_inquiry | True |
| greeting_smalltalk.ar.01 | السلام عليكم ورحمة الله | greeting_smalltalk | greeting_smalltalk | True |
| check_availability.fr.01 | Avez-vous Doliprane ? | check_availability | check_availability | True |
| request_medication.fr.01 | Je voudrais 2 boîtes de Doliprane | request_medication | request_medication | True |
| pharmacy_info_phone.fr.01 | Quel est le numéro de la pharmacie ? | pharmacy_info_phone | pharmacy_info_phone | True |
| pharmacy_info_location.fr.01 | Où se trouve la pharmacie ? | pharmacy_info_location | out_of_scope | False |
| pharmacy_info_hours.fr.01 | La pharmacie est-elle ouverte maintenant ? | pharmacy_info_hours | pharmacy_info_hours | True |
| out_of_scope.fr.01 | Quel médicament prendre contre le mal de tête ? | out_of_scope | out_of_scope | True |
| price_inquiry.fr.01 | Quel est le prix de Doliprane ? | price_inquiry | price_inquiry | True |
| greeting_smalltalk.fr.01 | Bonjour | greeting_smalltalk | greeting_smalltalk | True |
| check_availability.mixed.01 | wach kayn Doliprane en stock ? | check_availability | check_availability | True |
| request_medication.mixed.01 | bghit 2 boîtes de Doliprane | request_medication | request_medication | True |
| pharmacy_info_phone.mixed.01 | chno le numéro de la pharmacie ? | pharmacy_info_phone | pharmacy_info_phone | True |
| pharmacy_info_location.mixed.01 | fin kayna la pharmacie ? | pharmacy_info_location | check_availability | False |
| pharmacy_info_hours.mixed.01 | wach la pharmacie ouverte daba ? | pharmacy_info_hours | pharmacy_info_hours | True |
| out_of_scope.mixed.01 | chno prendre pour le mal de tête ? | out_of_scope | out_of_scope | True |
| price_inquiry.mixed.01 | bch7al le Doliprane ? | price_inquiry | price_inquiry | True |
| greeting_smalltalk.mixed.01 | salam, bonjour | greeting_smalltalk | greeting_smalltalk | True |
