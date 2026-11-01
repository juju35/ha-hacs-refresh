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

test('the editor only offers the status sensor', () => {
  const editor = new HacsRefreshCardEditor();
  editor.appendChild = () => {};
  editor.setConfig({});
  editor.hass = makeHass();
  const entity = editor._form.schema.find((s) => s.name === 'entity');
  assert.deepEqual(JSON.parse(JSON.stringify(entity.selector.entity.filter)), {
    integration: 'hacs_refresh',
    domain: 'sensor',
    device_class: 'enum',
  });
});

test('any entity of the device as `entity` finds its status sensor', () => {
  const hass = makeHass({ state: 'error', updates: [], attrs: { error: 'rate limited', failed: ['someone/broken: 404'] } });
  const auto = html(render({}, hass));
  for (const entity of [STATUS, LAST_CHECK, BUTTON]) {
    const out = html(render({ entity }, hass));
    assert.equal(out, auto, entity);
  }
  assert.match(auto, /lvl-alert/);
  assert.match(auto, /Checked 3 hours ago/);
  assert.match(auto, /class="check"/);
});

test('an entity unknown to the registry is still read as the status sensor', () => {
  const hass = makeHass({ updates: [] });
  const out = html(render({ entity: 'sensor.renamed_status' }, { ...hass, states: { ...hass.states, 'sensor.renamed_status': hass.states[STATUS] } }));
  assert.match(out, /Up to date/);
});

test('status unavailable or unknown: never shown as up to date, never hidden', () => {
  for (const state of ['unavailable', 'unknown']) {
    const hass = makeHass({ updates: [] });
    for (const id of [STATUS, LAST_CHECK, BUTTON]) hass.states[id] = { state, attributes: {} };
    const card = render({ hide_when_ok: true }, hass);
    const out = html(card);
    assert.equal(card.style.display, '', state);
    assert.match(out, /lvl-na/, state);
    assert.match(out, /Unavailable/, state);
    assert.doesNotMatch(out, /Up to date|Not checked yet|Every repository is up to date/, state);
  }
  const fr = makeHass({ language: 'fr' });
  fr.states[STATUS] = { state: 'unavailable', attributes: {} };
  assert.match(html(render({}, fr)), /Indisponible/);
});

test('a next check already due is not shown in the past', () => {
  const hass = makeHass({ updates: [] });
  hass.states[LAST_CHECK] = { state: minutes(-27 * 60), attributes: { scan_interval: 24, next_check: minutes(-3 * 60) } };
  const out = html(render({}, hass));
  assert.match(out, /Checked 27 hours ago/);
  assert.doesNotMatch(out, /next|ago · /);
});

test("HACS' update entities unavailable or missing: the status sensor's count is used, never up to date", () => {
  for (const mode of ['unavailable', 'missing']) {
    const hass = makeHass({ updates: [], attrs: { updates: 2 } });
    for (const id of ['update.mushroom_update', 'update.card_mod_update', 'update.hacs_update']) {
      if (mode === 'missing') delete hass.states[id];
      else hass.states[id] = { entity_id: id, state: 'unavailable', attributes: {} };
    }
    const card = render({ hide_when_ok: true }, hass);
    const out = html(card);
    assert.equal(card.style.display, '', mode);
    assert.match(out, /lvl-info/, mode);
    assert.match(out, /2 updates/, mode);
    assert.doesNotMatch(out, /Up to date|Every repository is up to date/, mode);
    assert.match(out, /HACS isn’t loaded/, mode);
  }
});

test('one HACS update entity known is enough: the entities stay the truth', () => {
  const hass = makeHass({ updates: [], attrs: { updates: 2 } });
  hass.states['update.hacs_update'] = { entity_id: 'update.hacs_update', state: 'unavailable', attributes: {} };
  const out = html(render({}, hass));
  assert.match(out, /Up to date/);
});

test('update entities coming back re-render the card', () => {
  const hass = makeHass({ updates: [], attrs: { updates: 2 } });
  const ids = ['update.mushroom_update', 'update.card_mod_update', 'update.hacs_update'];
  const back = { ...hass.states };
  for (const id of ids) hass.states[id] = { entity_id: id, state: 'unavailable', attributes: {} };
  const card = render({}, hass);
  assert.match(html(card), /2 updates/);
  card.hass = { ...hass, states: back };
  assert.match(html(card), /Up to date/);
});

test('a re-render keeps the keyboard focus on the check button and on an update row', () => {
  const card = render({}, makeHass());
  const check = card.shadowRoot.querySelector('.check');
  let focused = null;
  check.focus = () => {
    focused = 'check';
  };
  card.shadowRoot.activeElement = { classList: { contains: (c) => c === 'check' }, dataset: {} };
  // Pressing it starts a check: the button is busy, but stays focusable and ignores presses.
  const hass = makeHass({ state: 'running', attrs: { done: 1, total: 4 } });
  card.hass = hass;
  assert.equal(focused, 'check');
  assert.match(html(card), /class="check"[^>]*aria-disabled="true"/);
  assert.doesNotMatch(html(card), /class="check"[^>]*\sdisabled/);
  check.handlers.click();
  assert.equal(hass.calls.length, 0);

  const row = { dataset: { id: 'update.mushroom_update' }, addEventListener() {}, focus: () => (focused = row.dataset.id) };
  card.shadowRoot.querySelectorAll = (sel) => (sel === '.row[data-id]' ? [row] : []);
  card.shadowRoot.activeElement = { classList: { contains: () => false }, dataset: { id: 'update.mushroom_update' } };
  card.hass = makeHass({ updates: ['update.mushroom_update', 'update.hacs_update'] });
  assert.equal(focused, 'update.mushroom_update');
});

// WCAG contrast of the coloured text and status icons, with Home Assistant's default light and dark themes.
test('coloured text reaches 4.5:1 and status icons 3:1, light and dark', () => {
  const hex = (h) => [1, 3, 5].map((i) => Number.parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, p) => a.map((v, i) => v * p + b[i] * (1 - p));
  const lum = (c) => {
    const [r, g, b] = c.map((v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  };
  const css = HacsRefreshCard.styles.replace(/\s+/g, ' ');
  // The `color` of a rule: a state colour, or a color-mix of it with the text colour.
  const colorOf = (selector, state, text) => {
    const body = css.slice(css.indexOf(`${selector} {`)).match(/\{([^}]*)\}/)[1];
    const value = body.match(/(?:^|;)\s*color:\s*([^;]+)/)[1].trim();
    const m = value.match(/^color-mix\(in srgb, var\(--[\w-]+\) (\d+)%, var\(--primary-text-color, #\w+\)\)$/);
    if (m) return mix(hex(state), hex(text), Number(m[1]) / 100);
    assert.match(value, /^var\(--[\w-]+\)$/, selector);
    return hex(state);
  };
  const themes = { light: { card: '#ffffff', text: '#212121', sec: '#e5e5e5' }, dark: { card: '#1c1c1c', text: '#e1e1e1', sec: '#282828' } };
  const states = { ok: '#43a047', info: '#039be5', warn: '#ffa600', alert: '#db4437', na: '#9e9e9e' };
  for (const [name, t] of Object.entries(themes)) {
    const card = hex(t.card);
    for (const [lvl, c] of Object.entries(states)) {
      assert.ok(ratio(colorOf('.pill', c, t.text), mix(hex(c), card, 0.14)) >= 4.5, `${name} pill ${lvl}`);
      assert.ok(ratio(colorOf('.badge', c, t.text), mix(hex(c), card, 0.16)) >= 3, `${name} badge ${lvl}`);
    }
    const warnRow = mix(hex(states.warn), hex(t.sec), 0.12);
    assert.ok(ratio(colorOf('.row.warn .sub', states.warn, t.text), warnRow) >= 4.5, `${name} failed row`);
    assert.ok(ratio(colorOf('.ic', states.warn, t.text), mix(hex(states.warn), warnRow, 0.18)) >= 3, `${name} failed icon`);
    assert.ok(ratio(colorOf('.ic', states.info, t.text), mix(hex(states.info), hex(t.sec), 0.18)) >= 3, `${name} update icon`);
    const errorBg = mix(hex(states.alert), hex(t.sec), 0.12);
    assert.ok(ratio(colorOf('.error b', states.alert, t.text), errorBg) >= 4.5, `${name} error title`);
  }
});
