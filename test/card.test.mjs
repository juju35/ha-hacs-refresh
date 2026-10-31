// Unit tests for the card: the card file is evaluated with stubs, no browser needed.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../custom_components/hacs_refresh/frontend/hacs-refresh-card.js', import.meta.url), 'utf8');

// Elements found in the rendered HTML by a selector: enough to click the check button.
const fakeNode = () => ({
  innerHTML: '',
  style: {},
  handlers: {},
  addEventListener(type, fn) {
    this.handlers[type] = fn;
  },
  appendChild() {},
  // An ha-form stand-in: what the user changes in the editor.
  dispatch(value) {
    this.handlers['value-changed']({ detail: { value } });
  },
  attachShadow() {
    const elements = {};
    this.shadowRoot = {
      innerHTML: '',
      querySelector: (sel) => {
        if (sel !== '.check' || !this.shadowRoot.innerHTML.includes('class="check"')) return null;
        elements[sel] ||= fakeNode();
        return elements[sel];
      },
      querySelectorAll: () => [],
    };
    return this.shadowRoot;
  },
});
const context = {
  HTMLElement: class {},
  customElements: { get: () => true, define() {} },
  window: {},
  document: { createElement: () => fakeNode() },
  Event: class {
    constructor(type) {
      this.type = type;
    }
  },
  CustomEvent: class {
    constructor(type, init) {
      this.type = type;
      this.detail = init?.detail;
    }
  },
  Intl,
  console,
  Date,
};
vm.createContext(context);
vm.runInContext(`${source}\nthis.hr = { HacsRefreshCard, HacsRefreshCardEditor, HR_I18N, hrEsc, hrLang, hrDevices, HR_DEFAULTS };`, context);
const { HacsRefreshCard, HacsRefreshCardEditor, HR_I18N, hrEsc, hrLang, hrDevices, HR_DEFAULTS } = context.hr;

const STATUS = 'sensor.hacs_refresh_status';
const LAST_CHECK = 'sensor.hacs_refresh_last_check';
const BUTTON = 'button.hacs_refresh_check_for_updates';
const minutes = (m) => new Date(Date.now() + m * 60000).toISOString();

const REGISTRY = {
  [STATUS]: { platform: 'hacs_refresh', device_id: 'd1', translation_key: 'status' },
  [LAST_CHECK]: { platform: 'hacs_refresh', device_id: 'd1', translation_key: 'last_check' },
  [BUTTON]: { platform: 'hacs_refresh', device_id: 'd1', translation_key: 'check_updates' },
  'update.mushroom_update': { platform: 'hacs' },
  'update.card_mod_update': { platform: 'hacs' },
  'update.hacs_update': { platform: 'hacs' },
  'update.core': { platform: 'hassio' },
};

function makeHass({ state = 'idle', attrs = {}, updates = ['update.mushroom_update'], interval = 24, button = 'unknown', language = 'en' } = {}) {
  const calls = [];
  const states = {
    [STATUS]: { state, attributes: { done: 0, total: 0, updates: updates.length, failed: [], error: null, ...attrs } },
    [LAST_CHECK]: {
      state: minutes(-180),
      attributes: { scan_interval: interval, next_check: interval ? minutes(21 * 60) : null },
    },
    [BUTTON]: { state: button, attributes: {} },
    'update.core': { entity_id: 'update.core', state: 'on', attributes: { title: 'Core' } },
  };
  for (const id of ['update.mushroom_update', 'update.card_mod_update', 'update.hacs_update']) {
    const on = updates.includes(id);
    states[id] = {
      entity_id: id,
      state: on ? 'on' : 'off',
      attributes: { title: id.split('.')[1].replace('_update', ''), installed_version: 'v1.0.0', latest_version: on ? 'v1.1.0' : 'v1.0.0' },
    };
  }
  return { calls, language, entities: REGISTRY, states, callService: (...args) => calls.push(args) };
}

function render(config, hass) {
  const card = new HacsRefreshCard();
  card.attachShadow = fakeNode().attachShadow;
  card.style = {};
  card.dispatchEvent = () => {};
  card.setConfig(config);
  card.hass = hass;
  return card;
}

const html = (card) => card.shadowRoot.innerHTML;

test('every language has the English keys', () => {
  const keys = Object.keys(HR_I18N.en).sort();
  for (const [lang, strings] of Object.entries(HR_I18N)) assert.deepEqual(Object.keys(strings).sort(), keys, lang);
});

test('language follows Home Assistant, then the config, with English as fallback', () => {
  assert.equal(hrLang({ language: 'fr-FR' }, {}), 'fr');
  assert.equal(hrLang({ language: 'fr' }, { language: 'es' }), 'es');
  assert.equal(hrLang({ language: 'ja' }, {}), 'en');
});

test('entities found by translation key, or by entity ID when it is missing', () => {
  assert.deepEqual(JSON.parse(JSON.stringify(hrDevices(REGISTRY).d1)), { status: STATUS, last_check: LAST_CHECK, button: BUTTON });
  const noKeys = Object.fromEntries(Object.entries(REGISTRY).map(([id, e]) => [id, { ...e, translation_key: undefined }]));
  assert.equal(hrDevices(noKeys).d1.button, BUTTON);
});

test('updates from the HACS update entities only, with their versions', () => {
  const out = html(render({}, makeHass({ updates: ['update.mushroom_update', 'update.card_mod_update'] })));
  assert.match(out, /lvl-info/);
  assert.match(out, /2 updates/);
  assert.match(out, /card_mod/);
  assert.match(out, /v1\.0\.0 → v1\.1\.0/);
  assert.doesNotMatch(out, />Core</);
  // Sorted by name.
  assert.ok(out.indexOf('card_mod') < out.indexOf('mushroom'));
});

test('up to date: ok, last and next check', () => {
  const out = html(render({}, makeHass({ updates: [] })));
  assert.match(out, /lvl-ok/);
  assert.match(out, /Up to date/);
  assert.match(out, /Checked 3 hours ago · next in 21 hours/);
  assert.match(out, /Every repository is up to date/);
});

test('automatic check off is said so', () => {
  assert.match(html(render({}, makeHass({ interval: 0 }))), /automatic check off/);
});

test('running: progress and disabled button', () => {
  const out = html(render({}, makeHass({ state: 'running', attrs: { done: 12, total: 48 } })));
  assert.match(out, /Checking 12\/48/);
  assert.match(out, /aria-valuenow="25"/);
  assert.match(out, /class="check"[^>]*disabled/);
});

test('failed repositories and a failed check', () => {
  const failed = html(render({}, makeHass({ updates: [], attrs: { failed: ['someone/broken: 404 Not Found'] } })));
  assert.match(failed, /lvl-warn/);
  assert.match(failed, /1 failed/);
  assert.match(failed, /someone\/broken/);
  assert.match(failed, /404 Not Found/);
  const error = html(render({}, makeHass({ state: 'error', attrs: { error: 'rate limited' } })));
  assert.match(error, /lvl-alert/);
  assert.match(error, /The last check failed/);
  assert.match(error, /rate limited/);
  assert.doesNotMatch(html(render({ show_failed: false }, makeHass({ state: 'error', attrs: { error: 'x' } }))), /The last check failed/);
});

test('hide_when_ok hides the card only while everything is up to date', () => {
  const card = render({ hide_when_ok: true }, makeHass({ updates: [] }));
  assert.equal(card.style.display, 'none');
  card.hass = makeHass();
  assert.equal(card.style.display, '');
});

test('check button presses the button', () => {
  const hass = makeHass();
  const card = render({}, hass);
  card.shadowRoot.querySelector('.check').handlers.click();
  assert.equal(JSON.stringify(hass.calls), JSON.stringify([['button', 'press', { entity_id: BUTTON }]]));
  assert.doesNotMatch(html(render({ check_button: false }, makeHass())), /class="check"/);
});

test('not set up: tells so', () => {
  const out = html(render({}, { ...makeHass(), entities: {}, states: {} }));
  assert.match(out, /lvl-na/);
  assert.match(out, /HACS Refresh is not set up/);
});

test('names are escaped', () => {
  const out = html(render({ title: '"><img>' }, makeHass({ updates: [], attrs: { failed: ['<b>x</b>'] } })));
  assert.doesNotMatch(out, /<b>x<\/b>/);
  assert.doesNotMatch(out, /"><img>/);
  assert.equal(hrEsc(`<&>"'`), '&lt;&amp;&gt;&quot;&#39;');
});

test('French', () => {
  const out = html(render({}, makeHass({ language: 'fr', updates: ['update.mushroom_update', 'update.hacs_update'] })));
  assert.match(out, /2 mises à jour/);
  assert.match(out, /Mises à jour disponibles/);
});

test('no re-render while nothing changed', () => {
  const hass = makeHass();
  const card = render({}, hass);
  card.shadowRoot.innerHTML = 'kept';
  card.hass = { ...hass };
  assert.equal(card.shadowRoot.innerHTML, 'kept');
});

test('editor leaves the defaults out of the YAML', () => {
  const editor = new HacsRefreshCardEditor();
  editor.appendChild = () => {};
  const sent = [];
  editor.dispatchEvent = (ev) => sent.push(ev.detail.config);
  editor.setConfig({});
  editor.hass = makeHass();
  editor._form.dispatch({ ...HR_DEFAULTS, title: '', show_failed: false });
  assert.deepEqual(JSON.parse(JSON.stringify(sent.at(-1))), { show_failed: false });
});
