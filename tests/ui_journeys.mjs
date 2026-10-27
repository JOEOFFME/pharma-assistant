/** Run actual consumer UI code against DOM/network/media test doubles, no model calls. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const { Window } = await import(pathToFileURL(process.env.PHARMA_UI_TEST_MODULE || resolve(root, 'web/node_modules/happy-dom/lib/index.js')));
const window = new Window({ url: 'http://localhost:8000', settings: { disableCSSFileLoading: true, disableJavaScriptFileLoading: true } });
window.document.write(await readFile(resolve(root, 'web/index.html'), 'utf8'));
const $ = id => window.document.getElementById(id);
for (const dialog of window.document.querySelectorAll('dialog')) {
  dialog.showModal = () => { dialog.open = true; };
  dialog.close = () => { dialog.open = false; dialog.dispatchEvent(new window.Event('close')); };
}
const calls = [], plots = [], spoken = [];
let speechCancelled = 0;
window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
window.speechSynthesis = { getVoices: () => [{ lang: 'fr-FR' }, { lang: 'ar-MA' }], speak: utterance => spoken.push(utterance), cancel: () => speechCancelled++ };
const juryScenarios = JSON.parse(await readFile(resolve(root, 'web/assets/jury-scenarios.json'), 'utf8'));
const demoQuestions = JSON.parse(await readFile(resolve(root, 'web/assets/demo-questions.json'), 'utf8'));
let voiceOK = true, nextAnswer = 'Votre demande concerne Doliprane. Le stock reste à confirmer.', deferred, failStatus = 0, tracksStopped = 0, locationRequests = 0, actions = [];
const payload = () => ({ answer: nextAnswer, actions, transcript: null, analysis: { secret: 'MUST NEVER APPEAR' } });
window.fetch = async (url, options = {}) => {
  calls.push({ url, options });
  if (url === '/ui/jury-scenarios.json') return { ok: true, json: async () => juryScenarios };
  if (url.startsWith('/v1/demo/assistant/')) return { ok: true, json: async () => ({ ...payload(), synthetic: true, answer: 'Démonstration — données fictives. Panadol : 12 boîtes en stock simulé.', transcript: url.endsWith('/voice') ? juryScenarios[1].text : null }) };
  if (url === '/ui/demo-questions.json') return { ok: true, json: async () => demoQuestions };
  if (url === '/v1/voice/status') return { ok: true, json: async () => ({ ready: voiceOK, issues: ['SHOULD NOT APPEAR'] }) };
  if (url.startsWith('/v1/pharmacies/map')) return { ok: true, json: async () => ({ count: 1, radius_km: 5, pharmacies: [{ distance_km: .3, pharmacy: { name: '<script>untrusted</script>', phones_e164: [], opening_hours: null, latitude: 34, longitude: -6 } }], figure: { data: [], layout: {} } }) };
  if (deferred) return await new Promise(resolve => { deferred.resolve = resolve; });
  if (failStatus) return { ok: false, status: failStatus, json: async () => ({ error: { message: 'PRIVATE_BACKEND_FAILURE' } }) };
  if (url === '/v1/assistant/voice') return { ok: true, json: async () => ({ ...payload(), transcript: 'Wach kayn Doliprane ?' }) };
  return { ok: true, json: async () => payload() };
};
window.Plotly = { purge() {}, async newPlot(...args) { plots.push(args); } };
Object.defineProperty(window.navigator, 'mediaDevices', { value: { getUserMedia: async () => ({ getTracks: () => [{ stop: () => tracksStopped++ }] }) } });
Object.defineProperty(window.navigator, 'geolocation', { value: { getCurrentPosition(success) { locationRequests++; success({ coords: { latitude: 33.97, longitude: -6.86 } }); } } });
class Recorder {
  static isTypeSupported() { return true; }
  constructor(stream, options) { this.mimeType = options.mimeType; this.state = 'inactive'; }
  start() { this.state = 'recording'; }
  stop() { this.state = 'inactive'; this.ondataavailable({ data: new window.Blob(['test-only audio']) }); this.onstop(); }
}
window.MediaRecorder = Recorder;
window.eval(await readFile(resolve(root, 'web/assets/assistant.js'), 'utf8'));
const settle = async () => { for (let i=0;i<8;i++) await new Promise(resolve => setTimeout(resolve, 0)); };
const submit = text => { $('message').value = text; $('message-form').dispatchEvent(new window.Event('submit', { cancelable: true })); };
try {
  await settle();
  assert.equal($('record').disabled, false);
  assert.ok(window.document.body.textContent.includes('Pharma-AI'));
  assert.ok(!window.document.body.textContent.includes('Amine'));
  assert.equal(window.document.querySelector('pre'), null);
  assert.equal(window.document.querySelector('input[type="password"]'), null);
  // Sending preserves user evidence and shows readable replies without server internals.
  submit('Wach kayn Doliprane ?'); await settle();
  assert.equal(window.document.querySelectorAll('.message').length, 2);
  assert.equal(window.document.querySelector('.message.assistant .message-text').textContent, nextAnswer);
  assert.ok(!window.document.body.textContent.includes('MUST NEVER APPEAR'));
  assert.equal(JSON.parse(calls.find(c => c.url === '/v1/assistant/text').options.body).text, 'Wach kayn Doliprane ?');
  // User-initiated playback and automatic playback are separate controls.
  assert.equal(spoken.length, 0);
  window.document.querySelector('.playback-button').click();
  assert.equal(spoken.at(-1).text, nextAnswer);
  assert.equal(spoken.at(-1).lang, 'fr-FR');
  assert.equal($('stop-speaking').hidden, false);
  $('stop-speaking').click(); assert.equal($('stop-speaking').hidden, true);
  assert.ok(speechCancelled > 0);
  $('auto-speak').click(); assert.equal($('auto-speak').getAttribute('aria-pressed'), 'true');
  submit('salam'); await settle(); assert.equal(spoken.length, 2);
  $('auto-speak').click();
  // Demo choices fill a normal editable request; they never inject an answer.
  const requestsBefore = calls.filter(c => c.url === '/v1/assistant/text').length;
  $('open-demo').click(); await settle();
  const choices = [...window.document.querySelectorAll('#demo-questions button')];
  assert.equal(choices.length, 10);
  choices[2].click();
  assert.equal($('message').value, demoQuestions[2].text);
  assert.equal($('language').value, 'ar');
  assert.equal($('demo-dialog').open, false);
  assert.equal(calls.filter(c => c.url === '/v1/assistant/text').length, requestsBefore);
  submit($('message').value); await settle();
  window.document.querySelector('.message.assistant:last-child .playback-button').click();
  assert.equal(spoken.at(-1).lang, 'ar-MA');
  $('new-chat').click(); assert.equal($('stop-speaking').hidden, true);
  $('language').value = ''; $('language').dispatchEvent(new window.Event('change'));
  // A nearby-pharmacy reply offers consent actions without automatically locating.
  actions = [{ type:'find_pharmacy', label:'Voir les pharmacies', city:'Casablanca' }, { type:'share_location', label:'Partager ma position' }, { type:'untrusted_navigation', label:'Never execute' }];
  submit('3tini a9rab pharmacy lya'); await settle();
  assert.equal(locationRequests, 0);
  const actionButtons = [...window.document.querySelectorAll('.reply-actions button')];
  assert.equal(actionButtons.length, 2);
  actionButtons[0].click(); await settle();
  assert.equal($('map-city').value, 'Casablanca');
  assert.ok(calls.some(c => c.url.includes('lat=33.5731')));
  assert.equal(locationRequests, 0);
  $('map-dialog').close();
  actionButtons[1].click(); await settle();
  assert.equal(locationRequests, 1);
  assert.equal($('map-dialog').open, true);
  assert.ok(calls.some(c => c.url.includes('lat=33.97')));
  $('map-dialog').close(); actions = [];
  // Untrusted content remains text instead of being inserted as HTML.
  nextAnswer = '<img src=x onerror="alert(1)">'; submit('salam'); await settle();
  assert.equal(window.document.querySelector('.message img'), null);
  assert.ok(window.document.body.textContent.includes(nextAnswer));
  // Server messages never leak through consumer errors.
  failStatus = 503; submit('salam'); await settle(); failStatus = 0;
  assert.ok(!window.document.body.textContent.includes('PRIVATE_BACKEND_FAILURE'));
  // Arabic labels/direction, keyboard composition and clearing a conversation.
  $('language').value = 'ar'; $('language').dispatchEvent(new window.Event('change'));
  assert.equal(window.document.documentElement.dir, 'rtl');
  $('message').value = 'سلام'; $('message').dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Enter', isComposing: true, cancelable: true }));
  assert.equal($('message').value, 'سلام');
  $('new-chat').click(); assert.equal(window.document.querySelectorAll('.message').length, 0);
  assert.equal($('welcome').hidden, false);
  // Clearing during an in-flight request must suppress the stale response.
  deferred = {}; submit('سلام'); await settle(); $('new-chat').click();
  deferred.resolve({ ok: true, json: async () => payload() }); deferred = null; await settle();
  assert.equal(window.document.querySelectorAll('.message').length, 0);
  // Voice start/stop produces one upload, stops tracks and allows correcting evidence.
  $('record').click(); await settle(); assert.equal($('record').getAttribute('aria-pressed'), 'true');
  $('record').click(); await settle();
  assert.equal(tracksStopped, 1);
  assert.ok(calls.some(c => c.url === '/v1/assistant/voice'));
  const correction = window.document.querySelector('.message-action'); assert.ok(correction); correction.click();
  assert.equal($('message').value, 'Wach kayn Doliprane ?');
  // The map opens separately, uses city/radius controls and never inserts pharmacy markup.
  $('open-map').click(); await settle(); assert.equal($('map-dialog').open, true);
  assert.equal(window.document.querySelector('.pharmacy-card script'), null);
  assert.ok($('pharmacy-list').textContent.includes('<script>untrusted</script>'));
  assert.ok(plots.length > 0);
  $('locate').click(); await settle();
  assert.equal($('map-city').value, 'position');
  assert.ok(calls.some(c => c.url.includes('lat=33.97')));
  $('map-dialog').close();
  // Cancelling recording releases the microphone without uploading audio.
  const uploadsBefore = calls.filter(c => c.url === '/v1/assistant/voice').length;
  $('record').click(); await settle();
  assert.equal($('cancel-recording').hidden, false);
  $('cancel-recording').click(); await settle();
  assert.equal(calls.filter(c => c.url === '/v1/assistant/voice').length, uploadsBefore);
  assert.equal(tracksStopped, 2);
  assert.equal($('cancel-recording').hidden, true);
  // Voice unavailable is a consumer message and typing remains usable.
  voiceOK = false; window.dispatchEvent(new window.Event('focus')); await settle();
  assert.equal($('record').disabled, true); assert.equal($('send').disabled, false);
  assert.ok(!window.document.body.textContent.includes('SHOULD NOT APPEAR'));
  assert.ok(!window.document.body.textContent.includes('FFmpeg'));
  voiceOK = true; $('retry-voice').click(); await settle();
  assert.equal($('record').disabled, false);
  assert.equal($('retry-voice').hidden, true);
  $('language').value = ''; $('language').dispatchEvent(new window.Event('change'));
  // Fictional jury mode is explicit, resets history and uses isolated endpoints.
  assert.equal($('scenario-banner').hidden, true);
  $('demo-mode').click();
  assert.equal($('scenario-banner').hidden, false);
  assert.ok($('scenario-banner').textContent.includes('fictifs'));
  assert.equal(window.document.querySelectorAll('.message').length, 0);
  assert.equal($('open-map').disabled, true);
  $('open-demo').click(); await settle();
  const scenarioChoices = [...window.document.querySelectorAll('#demo-questions button')];
  assert.equal(scenarioChoices.length, 3);
  scenarioChoices[1].click(); submit($('message').value); await settle();
  assert.ok(calls.some(c => c.url === '/v1/demo/assistant/text'));
  assert.ok(window.document.querySelector('.message.assistant').textContent.includes('données fictives'));
  $('record').click(); await settle(); $('record').click(); await settle();
  assert.ok(calls.some(c => c.url === '/v1/demo/assistant/voice'));
  $('demo-mode').click();
  assert.equal($('scenario-banner').hidden, true);
  assert.equal($('open-map').disabled, false);
  assert.equal(window.document.querySelectorAll('.message').length, 0);
  submit('salam'); await settle();
  assert.equal(calls.at(-1).url, '/v1/assistant/text');
  console.log('PASS: consumer text, safe rendering, private errors, Arabic, composition, reset/race, voice/correction, map/location/consent and unavailable-voice journeys');
} finally { window.happyDOM.abort(); window.close(); }
