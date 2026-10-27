'use strict';
const $ = id => document.getElementById(id);
const STRINGS = {
  fr: {
    limitedService: 'Le service de conversation est momentanément indisponible. Voici les informations du répertoire enregistré.', transcribing: 'Je transcris votre message…', reviewTranscript: 'Vérifiez le texte reconnu ci-dessous, corrigez-le si besoin, puis appuyez sur Envoyer.', scenarioMode: 'Scénario du jury', scenarioBanner: 'DÉMONSTRATION — Pharmacies, adresses, distances, stocks et gardes fictifs. Point de départ simulé : Al Irfane. Aucun résultat ne confirme une disponibilité réelle.', examples: 'Exemples à essayer', demoIntro: 'Choisissez une question, puis envoyez-la ou prononcez-la au micro. Chaque exemple est une demande complète.', autoSpeak: 'Lecture vocale', listen: 'Écouter la réponse', stopSpeaking: 'Arrêter la lecture', speechOff: 'La lecture vocale est indisponible dans ce navigateur.', cancelRecording: 'Annuler l’enregistrement', retryVoice: 'Réessayer le micro',
    headerNote: 'Un coup de main, tout simplement.', virtual: 'Votre assistant virtuel', language: 'Langue', newChat: 'Nouvelle conversation', findPharmacy: 'Trouver une pharmacie', privacy: 'Confidentialité',
    welcomeEyebrow: 'BIENVENUE DANS VOTRE ESPACE', welcomeTitle: 'Bonjour, je suis Pharma-AI.', welcomeText: 'Je vous aide à préparer votre demande de médicament et à trouver une pharmacie. Comment puis-je vous aider aujourd’hui ?',
    medicationSuggestion: 'Une demande de médicament', pharmacySuggestion: 'Une pharmacie près de moi', priceSuggestion: 'Une question sur un prix', disclaimer: 'Pour vos demandes en pharmacie. Sans conseil médical ni confirmation de stock.',
    companionBadge: 'À vos côtés', virtualTag: 'VIRTUEL', companionSubtitle: 'Votre espace pharmacie,\nen toute simplicité.', nearYou: 'Autour de vous, en quelques clics', footer: 'Français, العربية, الدارجة — parlons comme vous.',
    mapEyebrow: 'À PROXIMITÉ', mapTitle: 'Votre prochaine pharmacie', city: 'Ville', distance: 'À moins de', search: 'Rechercher', aroundMe: 'Autour de moi', mapDisclaimer: 'Distances à vol d’oiseau. Certaines pharmacies peuvent ne pas apparaître. Appelez pour confirmer les horaires.',
    privacyText: 'Votre conversation reste dans cette page et n’est pas enregistrée dans l’historique de l’assistant. Les enregistrements vocaux sont supprimés après traitement. Votre position n’est utilisée que si vous choisissez de la partager. La carte utilise un service cartographique externe. Si l’assistance linguistique en ligne est activée, votre conversation et les informations utiles du répertoire sont envoyées au service de langage configuré. La lecture vocale dépend des voix de votre appareil, qui peuvent utiliser un service externe. Évitez de partager des informations médicales personnelles.',
    placeholder: 'Écrivez votre message…', send: 'Envoyer le message', record: 'Enregistrer un message vocal', stop: 'Arrêter et envoyer', attach: 'Joindre un message vocal', you: 'Vous', modify: 'Corriger ce message', empty: 'Écrivez votre message avant de l’envoyer.',
    waiting: 'Je prépare votre réponse…', voiceOff: 'Les messages vocaux sont indisponibles pour le moment. Vous pouvez m’écrire.', noMic: 'Le microphone n’est pas disponible dans ce navigateur. Vous pouvez m’écrire.', denied: 'Autorisez le microphone dans les paramètres du site pour enregistrer un message.', recording: 'Je vous écoute… Arrêtez l’enregistrement pour envoyer.', audioMessage: 'Message vocal', audioEmpty: 'Je n’ai pas reçu de son. Essayez un nouvel enregistrement.', audioLarge: 'Ce message vocal est trop long ou trop volumineux. Essayez un enregistrement plus court.',
    error: 'Je n’ai pas pu répondre pour le moment. Réessayez dans un instant.', network: 'La connexion a été interrompue. Réessayez dans un instant.', reserved: 'Cet espace est réservé. Contactez la personne qui vous a donné accès à cet assistant.', tooMany: 'Un petit instant… Vous pourrez réessayer dans une minute.', audioInvalid: 'Je n’arrive pas à lire cet enregistrement. Essayez un autre fichier ou enregistrez un nouveau message.', unclear: 'Je n’ai pas bien compris. Pouvez-vous reformuler ou réenregistrer votre demande ?',
    locating: 'Je recherche votre position…', locationOff: 'Votre position n’est pas accessible. Vous pouvez choisir une ville à la place.', myPosition: 'Ma position', searching: 'Je recherche les pharmacies autour de vous…', noPharmacies: 'Aucune pharmacie trouvée ici. Essayez d’élargir la distance.', found: '{count} pharmacie(s) à moins de {radius} km.', mapOff: 'La carte ne peut pas être affichée. Les adresses restent dans la liste.', unnamed: 'Pharmacie', phoneUnknown: 'Téléphone non renseigné', hoursUnknown: 'Horaires non renseignés', call: 'Appeler', place: 'Voir l’emplacement', close: 'Fermer',
    medicationPrompt: 'Est-ce que Doliprane est disponible ?', pricePrompt: 'Quel est le prix de Doliprane ?'
  },
  ar: {
    limitedService: 'خدمة المحادثة غير متاحة حالياً. هذه معلومات من الدليل المحفوظ.', transcribing: 'أحوّل رسالتك إلى نص…', reviewTranscript: 'راجع النص أدناه وصححه عند الحاجة، ثم اضغط إرسال.', scenarioMode: 'سيناريو العرض', scenarioBanner: 'عرض توضيحي — الصيدليات والعناوين والمسافات والمخزون والحراسة افتراضية. نقطة الانطلاق محاكاة. النتائج لا تؤكد توفراً حقيقياً.', examples: 'أمثلة للتجربة', demoIntro: 'اختر سؤالاً ثم أرسله أو اقرأه بالميكروفون. كل مثال طلب كامل.', autoSpeak: 'قراءة صوتية', listen: 'استمع للإجابة', stopSpeaking: 'أوقف القراءة', speechOff: 'القراءة الصوتية غير متاحة في هذا المتصفح.', cancelRecording: 'إلغاء التسجيل', retryVoice: 'أعد تجربة الميكروفون',
    headerNote: 'مساعدتك بكل بساطة.', virtual: 'مساعدك الافتراضي', language: 'اللغة', newChat: 'محادثة جديدة', findPharmacy: 'ابحث عن صيدلية', privacy: 'الخصوصية',
    welcomeEyebrow: 'مرحباً بك في مساحتك', welcomeTitle: 'مرحباً، أنا Pharma-AI.', welcomeText: 'أساعدك في صياغة طلب دواء والعثور على معلومات الصيدليات. كيف أستطيع مساعدتك اليوم؟', medicationSuggestion: 'طلب دواء', pharmacySuggestion: 'صيدلية بالقرب مني', priceSuggestion: 'سؤال عن السعر', disclaimer: 'لمساعدتك في طلبات الصيدلية. دون نصائح طبية أو تأكيد للمخزون.',
    companionBadge: 'بجانبك', virtualTag: 'افتراضي', companionSubtitle: 'طلبات الصيدلية،\nبكل بساطة.', nearYou: 'بالقرب منك، بخطوات بسيطة', footer: 'العربية، الدارجة، Français — نتحدث بلغتك.', mapEyebrow: 'بالقرب منك', mapTitle: 'اعثر على صيدلية', city: 'المدينة', distance: 'ضمن مسافة', search: 'ابحث', aroundMe: 'بالقرب مني', mapDisclaimer: 'المسافات بخط مستقيم. قد لا تظهر بعض الصيدليات. اتصل للتأكد من المواعيد.',
    privacyText: 'تبقى محادثتك في هذه الصفحة ولا تُحفظ في سجل المساعد. تُحذف التسجيلات بعد معالجتها. لا يُستخدم موقعك إلا إذا اخترت مشاركته. تستخدم الخريطة خدمة خارجية. عند تفعيل خدمة فهم اللغة عبر الإنترنت، تُرسل المحادثة ومعلومات الدليل المفيدة إلى الخدمة المخصصة. تعتمد القراءة الصوتية على أصوات جهازك وقد تستخدم خدمة خارجية. تجنب مشاركة معلومات طبية شخصية.',
    placeholder: 'اكتب رسالتك…', send: 'أرسل الرسالة', record: 'سجل رسالة صوتية', stop: 'أوقف وأرسل', attach: 'أرفق رسالة صوتية', you: 'أنت', modify: 'صحح الرسالة', empty: 'اكتب رسالتك أولاً.', waiting: 'أجهز إجابتك…', voiceOff: 'الصوت غير متاح حالياً. يمكنك الكتابة لي.', noMic: 'الميكروفون غير متاح في هذا المتصفح. يمكنك الكتابة.', denied: 'اسمح للمتصفح باستخدام الميكروفون لتسجيل رسالتك.', recording: 'أستمع إليك… أوقف التسجيل لإرساله.', audioMessage: 'رسالة صوتية', audioEmpty: 'لم أستقبل صوتاً. جرب تسجيلاً جديداً.', audioLarge: 'التسجيل طويل أو حجمه كبير. جرب رسالة أقصر.',
    error: 'لم أتمكن من الإجابة الآن. حاول بعد قليل.', network: 'انقطع الاتصال. حاول بعد قليل.', reserved: 'هذه المساحة مخصصة للمصرح لهم. تواصل مع الشخص الذي منحك الوصول.', tooMany: 'انتظر قليلاً، ثم حاول بعد دقيقة.', audioInvalid: 'تعذر تشغيل هذا التسجيل. أرسل ملفاً آخر أو سجل رسالة جديدة.', unclear: 'لم أفهم جيداً. هل يمكنك إعادة الصياغة أو التسجيل؟', locating: 'أبحث عن موقعك…', locationOff: 'تعذر تحديد موقعك. يمكنك اختيار مدينة بدلاً من ذلك.', myPosition: 'موقعي', searching: 'أبحث عن الصيدليات القريبة…', noPharmacies: 'لم أجد صيدليات هنا. جرب مسافة أكبر.', found: '{count} صيدلية ضمن {radius} كم.', mapOff: 'تعذر عرض الخريطة. يمكنك الاطلاع على القائمة.', unnamed: 'صيدلية', phoneUnknown: 'الهاتف غير مسجل', hoursUnknown: 'المواعيد غير مسجلة', call: 'اتصل', place: 'اعرض الموقع', close: 'أغلق', medicationPrompt: 'هل دوليبران متوفر؟', pricePrompt: 'ما سعر دوليبران؟'
  },
  darija_ar: {
    virtual: 'المساعد الافتراضي ديالك', welcomeTitle: 'سلام، أنا Pharma-AI.', welcomeText: 'نعاونك تصيغ الطلب ديال الدوا وتلقى معلومات الصيدليات. كيفاش نقدر نعاونك اليوم؟', placeholder: 'كتب الرسالة ديالك…', you: 'نتا', waiting: 'كنوجد ليك الجواب…', voiceOff: 'الصوت ما متوفرش دابا. تقدر تكتب ليا.', medicationPrompt: 'واش كاين دوليبران؟', pricePrompt: 'بشحال دوليبران؟'
  },
  darija_latn: {
    virtual: 'L’assistant dyalek', welcomeTitle: 'Salam, ana Pharma-AI.', welcomeText: 'N3awnek tsayeb talab dyal dwa w tel9a ma3loumat pharmacie. Kifach n9der n3awnek lyoum ?', placeholder: 'Kteb message dyalek…', you: 'Nta', waiting: 'Kanwejjed lik ljawab…', voiceOff: 'Sout ma khddamch daba. T9der tkteb lia.', medicationPrompt: 'Wach kayn Doliprane ?', pricePrompt: 'Bch7al Doliprane ?'
  }
};
function t(key, values = {}) {
  const lang = $('language').value;
  const fallback = lang === 'darija_ar' ? STRINGS.ar : STRINGS.fr;
  let text = STRINGS[lang]?.[key] || fallback[key] || STRINGS.fr[key] || '';
  for (const [name, value] of Object.entries(values)) text = text.replaceAll(`{${name}}`, String(value));
  return text;
}
let chatHistory = [];
let demoMode = false;
let autoSpeak = false;
let speakingButton = null, activeUtterance = null;
let busy = false, voiceReady = false, recording = null, requestNumber = 0, activeRequest;
let selectedCenter = { lat: 34.0209, lon: -6.8416 }, sharedLocation = null, mapRequest = 0, plotlyPromise;
const CITIES = { Rabat: [34.0209, -6.8416], Casablanca: [33.5731, -7.5898], Marrakech: [31.6295, -7.9811], Tanger: [35.7595, -5.8340], 'Fès': [34.0331, -5.0003], Agadir: [30.4278, -9.5981] };
const safeStatus = (code, audio = false) => code === 401 || code === 403 ? t('reserved') : code === 429 ? t('tooMany') : code === 413 ? t('audioLarge') : code === 415 ? t('audioInvalid') : code === 422 ? t('unclear') : code === 503 && audio ? t('voiceOff') : t('error');
function updateControls() {
  $('send').disabled = busy || !!recording;
  $('attach').disabled = busy || !!recording || !voiceReady;
  $('record').disabled = busy || (!voiceReady && !recording);
  $('message').disabled = !!recording;
  $('language').disabled = busy || !!recording;
  $('record').classList.toggle('recording', !!recording);
  $('record').setAttribute('aria-pressed', String(!!recording));
  $('record').setAttribute('aria-label', t(recording ? 'stop' : 'record'));
  $('record').title = voiceReady ? t(recording ? 'stop' : 'record') : t('voiceOff');
  $('attach').title = voiceReady ? t('attach') : t('voiceOff');
  $('record').querySelector('use').setAttribute('href', recording ? '#i-close' : '#i-mic');
}
function applyLanguage() {
  document.documentElement.lang = ['ar', 'darija_ar'].includes($('language').value) ? 'ar' : 'fr';
  document.documentElement.dir = ['ar', 'darija_ar'].includes($('language').value) ? 'rtl' : 'ltr';
  for (const node of document.querySelectorAll('[data-i18n]')) {
    node.textContent = t(node.dataset.i18n);
    node.dir = 'auto';
  }
  $('message').placeholder = t('placeholder');
  for (const [id, key] of [['message','placeholder'],['send','send'],['attach','attach'],['language','language']]) $(id).setAttribute('aria-label', t(key));
  for (const button of document.querySelectorAll('.close-dialog')) button.setAttribute('aria-label', t('close'));
  $('map-city').querySelector('[value="position"]').textContent = t('myPosition');
  $('status').textContent = voiceReady ? '' : t('voiceOff');
  updateControls();
}
function scrollChat() { $('conversation').scrollTop = $('conversation').scrollHeight; }
function stopSpeaking() {
  activeUtterance = null;
  window.speechSynthesis?.cancel();
  $('stop-speaking').hidden = true;
  if (speakingButton) speakingButton.setAttribute('aria-pressed', 'false');
  speakingButton = null;
}
function speakAnswer(text, language, button) {
  stopSpeaking();
  if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) { $('status').textContent = t('speechOff'); return; }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = ['ar', 'darija_ar'].includes(language) ? 'ar-MA' : 'fr-FR';
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find(v => v.lang === utterance.lang) || voices.find(v => v.lang.startsWith(utterance.lang.slice(0, 2)));
  if (voice) utterance.voice = voice;
  activeUtterance = utterance; speakingButton = button; button?.setAttribute('aria-pressed', 'true');
  $('stop-speaking').hidden = false;
  utterance.onend = () => { if (activeUtterance === utterance) stopSpeaking(); };
  utterance.onerror = event => { if (event.error !== 'canceled' && event.error !== 'interrupted') $('status').textContent = t('speechOff'); if (activeUtterance === utterance) stopSpeaking(); };
  window.speechSynthesis.speak(utterance);
}
function addPlayback(reply, text, language) {
  if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
  const button = document.createElement('button'); button.type = 'button'; button.className = 'playback-button';
  button.textContent = '▶ ' + t('listen'); button.setAttribute('aria-pressed', 'false');
  button.onclick = () => speakingButton === button ? stopSpeaking() : speakAnswer(text, language, button);
  reply.article.append(button);
  if (autoSpeak) speakAnswer(text, language, button);
}
function bubble(text, role) {
  const article = document.createElement('article'); article.className = `message ${role}`;
  const label = document.createElement('span'); label.className = 'message-label'; label.textContent = role === 'user' ? t('you') : 'Pharma-AI';
  const body = document.createElement('p'); body.className = 'message-text'; body.dir = 'auto'; body.textContent = text;
  article.append(label, body); $('conversation').append(article); scrollChat(); return { article, body };
}
function typingBubble() {
  const { article, body } = bubble('', 'assistant'); body.className = 'typing'; body.setAttribute('aria-label', t('waiting'));
  for (let i = 0; i < 3; i++) body.append(document.createElement('span'));
  return article;
}
function resizeComposer() { $('message').style.height = 'auto'; $('message').style.height = Math.min($('message').scrollHeight, 125) + 'px'; }
async function sendRequest(body, isAudio, displayText) {
  if (busy || recording) return;
  stopSpeaking(); const id = ++requestNumber; busy = true; updateControls(); $('welcome').hidden = true;
  const mine = bubble(displayText, 'user'), pending = typingBubble();
  $('status').textContent = t(isAudio ? 'transcribing' : 'waiting'); const controller = new AbortController(); activeRequest = controller;
  const timer = setTimeout(() => controller.abort(), 120000);
  try {
    const response = await fetch(isAudio ? '/v1/transcribe/voice' : `${demoMode ? '/v1/demo/assistant' : '/v1/assistant'}/text`, {
      method: 'POST', body: isAudio ? body : JSON.stringify(body), headers: isAudio ? {} : { 'Content-Type': 'application/json' }, signal: controller.signal, credentials: 'same-origin'
    });
    if (id !== requestNumber) return;
    if (!response.ok) throw new Error(safeStatus(response.status, isAudio));
    const data = await response.json(); if (id !== requestNumber) return;
    if (isAudio) {
      if (data.requires_confirmation !== true || typeof data.transcript !== 'string' || !data.transcript.trim()) throw new Error(t('unclear'));
      pending.remove(); mine.article.remove();
      $('message').value = data.transcript; resizeComposer();
      $('status').textContent = t('reviewTranscript');
      if (!$('conversation').querySelector('.message')) $('welcome').hidden = false;
      return;
    }
    if (demoMode && data.synthetic !== true) throw new Error(t('error'));
    if (typeof data.answer !== 'string' || !data.answer.trim()) throw new Error(t('error'));
    pending.remove(); const reply = bubble(data.answer, 'assistant');
    if (!demoMode) { chatHistory.push({ role: 'user', text: displayText.slice(0,4000) }, { role: 'assistant', text: data.answer.slice(0,4000) }); chatHistory = chatHistory.slice(-10); }
    addPlayback(reply, data.answer, data.language || $('language').value);
    if (Array.isArray(data.actions)) {
      const controls = document.createElement('div'); controls.className = 'reply-actions';
      for (const action of data.actions) {
        if (!['find_pharmacy','share_location'].includes(action.type)) continue;
        const button = document.createElement('button'); button.type = 'button';
        button.textContent = action.label || t(action.type === 'find_pharmacy' ? 'findPharmacy' : 'aroundMe');
        button.onclick = () => {
          if (typeof action.city === 'string' && Object.hasOwn(CITIES, action.city)) $('map-city').value = action.city;
          openMap(action.type !== 'share_location');
          if (action.type === 'share_location') locate();
        };
        controls.append(button);
      }
      if (controls.childElementCount) reply.article.append(controls);
    }
    scrollChat();
    $('status').textContent = data.fallback_reason ? t('limitedService') : '';
  } catch (error) {
    if (id !== requestNumber) return;
    pending.remove(); bubble(error instanceof TypeError || error.name === 'AbortError' ? t('network') : error.message, 'assistant'); $('status').textContent = '';
  } finally {
    clearTimeout(timer);
    if (id === requestNumber) { busy = false; activeRequest = null; updateControls(); $('message').focus(); }
  }
}
function submitText() {
  const text = $('message').value.trim(); if (!text) { $('status').textContent = t('empty'); return; }
  if (busy || recording) return;
  $('message').value = ''; resizeComposer();
  const body = { text, language_hint: $('language').value || null, history: demoMode ? [] : chatHistory };
  if (sharedLocation && !demoMode) body.user_location = { latitude: sharedLocation.lat, longitude: sharedLocation.lon };
  sendRequest(body, false, text);
}
function sendAudio(blob, name) {
  if (!blob.size) { $('status').textContent = t('audioEmpty'); return; }
  if (blob.size > 10485760) { $('status').textContent = t('audioLarge'); return; }
  const form = new FormData(); form.append('file', blob, name);
  if ($('language').value) form.append('language_hint', $('language').value);
  sendRequest(form, true, t('audioMessage'));
}
function releaseRecording(session) {
  if (session.released) return;
  session.released = true;
  $('cancel-recording').hidden = true; clearTimeout(session.timeout); clearInterval(session.ticker); session.stream.getTracks().forEach(track => track.stop());
  if (recording === session) recording = null; updateControls();
}
async function toggleRecording() {
  if (recording) { if (recording.recorder.state === 'recording') recording.recorder.stop(); return; }
  if (busy || !voiceReady) return;
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { $('status').textContent = t('noMic'); return; }
  stopSpeaking(); const number = requestNumber;
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (number !== requestNumber || busy || recording) { stream.getTracks().forEach(track => track.stop()); return; }
    const mime = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4'].find(type => MediaRecorder.isTypeSupported(type));
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
    const session = { recorder, stream, parts: [], cancelled: false, seconds: 0 }; recording = session;
    recorder.ondataavailable = event => { if (event.data.size) session.parts.push(event.data); };
    recorder.onerror = () => { session.cancelled = true; releaseRecording(session); $('status').textContent = t('audioInvalid'); };
    recorder.onstop = () => {
      const type = recorder.mimeType; releaseRecording(session);
      if (session.cancelled || number !== requestNumber) return;
      const extension = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm';
      sendAudio(new Blob(session.parts, { type }), `voice.${extension}`);
    };
    recorder.start(); $('cancel-recording').hidden = false; updateControls(); $('status').textContent = t('recording');
    session.ticker = setInterval(() => { session.seconds++; $('status').textContent = `${t('recording')} ${String(Math.floor(session.seconds / 60)).padStart(2,'0')}:${String(session.seconds % 60).padStart(2,'0')}`; }, 1000);
    session.timeout = setTimeout(() => { if (recorder.state === 'recording') recorder.stop(); }, 55000);
  } catch (error) { stream?.getTracks().forEach(track => track.stop()); recording = null; updateControls(); $('status').textContent = error.name === 'NotAllowedError' ? t('denied') : t('noMic'); }
}
async function checkVoice() {
  try { const response = await fetch('/v1/voice/status', { credentials: 'same-origin' }); voiceReady = response.ok && (await response.json()).ready === true; }
  catch { voiceReady = false; }
  $('retry-voice').hidden = voiceReady;
  if (!busy && !recording) $('status').textContent = voiceReady ? '' : t('voiceOff'); updateControls();
}
function newConversation() {
  stopSpeaking(); requestNumber++; activeRequest?.abort(); activeRequest = null;
  if (recording) { const session = recording; session.cancelled = true; if (session.recorder.state === 'recording') session.recorder.stop(); releaseRecording(session); }
  busy = false; sharedLocation = null; chatHistory = [];
  for (const node of $('conversation').querySelectorAll('.message')) node.remove();
  $('welcome').hidden = false; $('message').value = ''; resizeComposer(); $('main-menu').hidden = true; $('menu-button').setAttribute('aria-expanded', 'false');
  $('status').textContent = voiceReady ? '' : t('voiceOff'); updateControls(); $('message').focus();
}
function openMap(search = true) { $('main-menu').hidden = true; $('menu-button').setAttribute('aria-expanded','false'); $('map-dialog').showModal(); if (search) searchPharmacies(); }
async function loadPlotly() {
  if (window.Plotly) return window.Plotly;
  if (!plotlyPromise) plotlyPromise = new Promise((resolve,reject) => {
    const script = document.createElement('script'); script.src = '/assets/plotly.min.js'; script.onload = () => resolve(window.Plotly); script.onerror = () => { script.remove(); plotlyPromise = null; reject(new Error(t('mapOff'))); }; document.head.append(script);
  });
  return plotlyPromise;
}
function pharmacyCard(row) {
  const p = row.pharmacy, card = document.createElement('article'); card.className = 'pharmacy-card';
  const title = document.createElement('h3'); title.dir = 'auto'; title.textContent = p.name || t('unnamed');
  const detail = document.createElement('p'); detail.dir = 'auto'; detail.textContent = `${row.distance_km.toFixed(2)} km · ${p.phones_e164.join(', ') || t('phoneUnknown')}\n${p.opening_hours || t('hoursUnknown')}`;
  const place = document.createElement('a'); place.textContent = t('place'); place.href = `https://www.openstreetmap.org/?mlat=${p.latitude}&mlon=${p.longitude}#map=18/${p.latitude}/${p.longitude}`; place.target = '_blank'; place.rel = 'noopener noreferrer';
  card.append(title, detail);
  const phone = p.phones_e164.find(number => /^\+\d{7,15}$/.test(number));
  if (phone) { const call = document.createElement('a'); call.href = `tel:${phone}`; call.textContent = t('call'); card.append(call); }
  card.append(place); return card;
}
async function searchPharmacies() {
  const id = ++mapRequest; $('map-status').textContent = t('searching'); $('pharmacy-list').replaceChildren();
  if (window.Plotly) window.Plotly.purge('pharmacy-map');
  try {
    const city = $('map-city').value;
    if (city !== 'position') { const pair = CITIES[city]; selectedCenter = { lat: pair[0], lon: pair[1] }; }
    const params = new URLSearchParams({ lat: selectedCenter.lat, lon: selectedCenter.lon, radius_km: $('map-radius').value });
    const response = await fetch('/v1/pharmacies/map?' + params, { credentials: 'same-origin' });
    if (id !== mapRequest) return;
    if (!response.ok) throw new Error(safeStatus(response.status));
    const data = await response.json(); if (id !== mapRequest) return;
    for (const row of data.pharmacies) $('pharmacy-list').append(pharmacyCard(row));
    const summary = data.count ? t('found', { count: data.count, radius: data.radius_km }) : t('noPharmacies'); $('map-status').textContent = summary;
    try { const plotly = await loadPlotly(); if (id !== mapRequest || !$('map-dialog').open) return; await plotly.newPlot('pharmacy-map',data.figure.data,data.figure.layout,{ responsive:true, displayModeBar:false, displaylogo:false, scrollZoom:true }); }
    catch { if (id === mapRequest) $('map-status').textContent = summary + ' ' + t('mapOff'); }
  } catch (error) { if (id === mapRequest) $('map-status').textContent = error instanceof TypeError ? t('network') : error.message; }
}
function locate() {
  if (!navigator.geolocation) { $('map-status').textContent = t('locationOff'); return; }
  $('map-status').textContent = t('locating'); $('locate').disabled = true;
  navigator.geolocation.getCurrentPosition(position => {
    $('locate').disabled = false; sharedLocation = { lat: position.coords.latitude, lon: position.coords.longitude }; selectedCenter = { ...sharedLocation };
    $('map-city').querySelector('[value="position"]').hidden = false; $('map-city').value = 'position'; searchPharmacies();
  }, () => { $('locate').disabled = false; $('map-status').textContent = t('locationOff'); }, { timeout:10000, maximumAge:60000 });
}
$('message-form').onsubmit = event => { event.preventDefault(); submitText(); };
$('message').oninput = resizeComposer;
$('message').onkeydown = event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); submitText(); } };
$('attach').onclick = () => $('audio-file').click();
$('audio-file').onchange = () => { const file = $('audio-file').files[0]; $('audio-file').value = ''; if (file) sendAudio(file,file.name); };
$('record').onclick = toggleRecording;
$('language').onchange = applyLanguage;
$('new-chat').onclick = newConversation;
$('menu-button').onclick = () => { $('main-menu').hidden = !$('main-menu').hidden; $('menu-button').setAttribute('aria-expanded', String(!$('main-menu').hidden)); };
document.addEventListener('click', event => { if (!event.target.closest('.menu-wrap')) { $('main-menu').hidden = true; $('menu-button').setAttribute('aria-expanded','false'); } });
document.addEventListener('keydown', event => { if (event.key === 'Escape') { $('main-menu').hidden = true; $('menu-button').setAttribute('aria-expanded','false'); } });
for (const id of ['open-map','menu-map','suggest-map']) $(id).onclick = () => openMap();
$('privacy-button').onclick = () => { $('main-menu').hidden = true; $('menu-button').setAttribute('aria-expanded','false'); $('privacy-dialog').showModal(); };
for (const button of document.querySelectorAll('[data-close]')) button.onclick = () => $(button.dataset.close).close();
$('map-dialog').addEventListener('close', () => { mapRequest++; });
$('map-form').onsubmit = event => { event.preventDefault(); searchPharmacies(); };
$('locate').onclick = locate;
$('suggest-medication').onclick = () => { $('message').value = t('medicationPrompt'); resizeComposer(); $('message').focus(); };
$('suggest-price').onclick = () => { $('message').value = t('pricePrompt'); resizeComposer(); $('message').focus(); };
window.addEventListener('pagehide', () => { stopSpeaking(); activeRequest?.abort(); if (recording) { recording.cancelled = true; releaseRecording(recording); } });
window.addEventListener('focus', () => { if (!busy && !recording) checkVoice(); });
$('cancel-recording').onclick = () => {
  if (!recording) return;
  const session = recording; session.cancelled = true;
  if (session.recorder.state === 'recording') session.recorder.stop();
  releaseRecording(session); $('status').textContent = '';
};
$('retry-voice').onclick = checkVoice;
$('stop-speaking').onclick = stopSpeaking;
$('auto-speak').disabled = !window.speechSynthesis || !window.SpeechSynthesisUtterance;
$('auto-speak').onclick = () => { autoSpeak = !autoSpeak; $('auto-speak').setAttribute('aria-pressed', String(autoSpeak)); if (!autoSpeak) stopSpeaking(); };
$('demo-mode').onclick = () => {
  demoMode = !demoMode;
  newConversation();
  $('demo-mode').setAttribute('aria-pressed', String(demoMode));
  $('scenario-banner').hidden = !demoMode;
  $('demo-questions').replaceChildren(); $('demo-status').textContent = '';
  for (const id of ['open-map', 'menu-map', 'suggest-map']) $(id).disabled = demoMode;
  if ($('map-dialog').open) $('map-dialog').close();
};
$('open-demo').onclick = async () => {
  $('demo-dialog').showModal();
  if ($('demo-questions').childElementCount) return;
  try {
    const mode = demoMode;
    const response = await fetch(mode ? '/ui/jury-scenarios.json' : '/ui/demo-questions.json', { credentials: 'same-origin' });
    if (!response.ok) throw new Error();
    const items = await response.json(); if (mode !== demoMode) return;
    for (const item of items) {
      const button = document.createElement('button'); button.type = 'button';
      const title = document.createElement('strong'); title.textContent = item.title;
      const question = document.createElement('span'); question.textContent = item.text; question.dir = 'auto';
      button.append(title, question);
      button.onclick = () => { $('language').value = item.language_hint; applyLanguage(); $('message').value = item.text; resizeComposer(); $('demo-dialog').close(); $('message').focus(); };
      $('demo-questions').append(button);
    }
  } catch { $('demo-status').textContent = t('network'); }
};
applyLanguage(); checkVoice();
