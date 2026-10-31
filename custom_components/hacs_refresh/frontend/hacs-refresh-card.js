/**
 * hacs-refresh-card — the HACS check of HACS Refresh: status and progress, the last and next check, the updates
 * available for the repositories downloaded with HACS, and the ones that couldn't be checked.
 * Served and added to the dashboard resources by the integration.
 * https://github.com/juju35/ha-hacs-refresh
 */
var HACS_REFRESH_CARD_VERSION = '0.7.0';

const HR_I18N = {
  en: {
    title: 'HACS updates',
    up_to_date: 'Up to date',
    updates_one: '{n} update',
    updates_many: '{n} updates',
    checking: 'Checking {done}/{total}',
    checking_short: 'Checking…',
    error: 'Error',
    failed_one: '{n} failed',
    failed_many: '{n} failed',
    not_loaded: 'HACS Refresh is not set up',
    never_checked: 'Not checked yet',
    checked: 'Checked {d}',
    next: 'next {d}',
    auto_off: 'automatic check off',
    check_now: 'Check for updates',
    updates_title: 'Updates available',
    no_updates: 'Every repository is up to date',
    failed_title: 'Could not be checked',
    error_title: 'The last check failed',
    version: '{from} → {to}',
    ed_entity: 'HACS Refresh sensor',
    ed_entity_helper: 'Status sensor; leave empty to find it automatically',
    ed_title: 'Title',
    ed_title_helper: 'Leave empty for “HACS updates”',
    ed_show_updates: 'Updates available',
    ed_show_updates_helper: 'The HACS repositories with an update, from their update entities',
    ed_show_failed: 'Repositories that could not be checked',
    ed_show_failed_helper: 'And the error of a check that failed',
    ed_check_button: '“Check for updates” button',
    ed_check_button_helper: 'Starts a check from the header',
    ed_hide_when_ok: 'Hide the card when everything is up to date',
    ed_hide_when_ok_helper: 'The card only appears while checking, or with an update or an error',
    ed_language: 'Language',
    ed_language_helper: 'Leave empty to follow Home Assistant',
  },
  fr: {
    title: 'Mises à jour HACS',
    up_to_date: 'À jour',
    updates_one: '{n} mise à jour',
    updates_many: '{n} mises à jour',
    checking: 'Vérification {done}/{total}',
    checking_short: 'Vérification…',
    error: 'Erreur',
    failed_one: '{n} en échec',
    failed_many: '{n} en échec',
    not_loaded: 'HACS Refresh n’est pas configuré',
    never_checked: 'Pas encore vérifié',
    checked: 'Vérifié {d}',
    next: 'prochaine {d}',
    auto_off: 'vérification automatique désactivée',
    check_now: 'Rechercher les mises à jour',
    updates_title: 'Mises à jour disponibles',
    no_updates: 'Tous les dépôts sont à jour',
    failed_title: 'Impossible à vérifier',
    error_title: 'La dernière vérification a échoué',
    version: '{from} → {to}',
    ed_entity: 'Capteur HACS Refresh',
    ed_entity_helper: 'Capteur de statut ; laisser vide pour le trouver automatiquement',
    ed_title: 'Titre',
    ed_title_helper: 'Laisser vide pour « Mises à jour HACS »',
    ed_show_updates: 'Mises à jour disponibles',
    ed_show_updates_helper: 'Les dépôts HACS avec une mise à jour, d’après leurs entités de mise à jour',
    ed_show_failed: 'Dépôts impossibles à vérifier',
    ed_show_failed_helper: 'Et l’erreur d’une vérification qui a échoué',
    ed_check_button: 'Bouton « Rechercher les mises à jour »',
    ed_check_button_helper: 'Lance une vérification depuis l’en-tête',
    ed_hide_when_ok: 'Masquer la carte quand tout est à jour',
    ed_hide_when_ok_helper: 'La carte n’apparaît que pendant une vérification, ou avec une mise à jour ou une erreur',
    ed_language: 'Langue',
    ed_language_helper: 'Laisser vide pour suivre Home Assistant',
  },
  de: {
    title: 'HACS-Updates',
    up_to_date: 'Aktuell',
    updates_one: '{n} Update',
    updates_many: '{n} Updates',
    checking: 'Prüfung {done}/{total}',
    checking_short: 'Prüfung läuft…',
    error: 'Fehler',
    failed_one: '{n} fehlgeschlagen',
    failed_many: '{n} fehlgeschlagen',
    not_loaded: 'HACS Refresh ist nicht eingerichtet',
    never_checked: 'Noch nicht geprüft',
    checked: 'Geprüft {d}',
    next: 'nächste {d}',
    auto_off: 'automatische Prüfung aus',
    check_now: 'Nach Updates suchen',
    updates_title: 'Verfügbare Updates',
    no_updates: 'Alle Repositorys sind aktuell',
    failed_title: 'Konnten nicht geprüft werden',
    error_title: 'Die letzte Prüfung ist fehlgeschlagen',
    version: '{from} → {to}',
    ed_entity: 'HACS-Refresh-Sensor',
    ed_entity_helper: 'Statussensor; leer lassen, um ihn automatisch zu finden',
    ed_title: 'Titel',
    ed_title_helper: 'Leer lassen für „HACS-Updates“',
    ed_show_updates: 'Verfügbare Updates',
    ed_show_updates_helper: 'Die HACS-Repositorys mit einem Update, aus ihren Update-Entitäten',
    ed_show_failed: 'Nicht prüfbare Repositorys',
    ed_show_failed_helper: 'Und der Fehler einer fehlgeschlagenen Prüfung',
    ed_check_button: 'Schaltfläche „Nach Updates suchen“',
    ed_check_button_helper: 'Startet eine Prüfung aus der Kopfzeile',
    ed_hide_when_ok: 'Karte ausblenden, wenn alles aktuell ist',
    ed_hide_when_ok_helper: 'Die Karte erscheint nur während einer Prüfung oder bei einem Update oder Fehler',
    ed_language: 'Sprache',
    ed_language_helper: 'Leer lassen, um Home Assistant zu folgen',
  },
  es: {
    title: 'Actualizaciones de HACS',
    up_to_date: 'Al día',
    updates_one: '{n} actualización',
    updates_many: '{n} actualizaciones',
    checking: 'Comprobando {done}/{total}',
    checking_short: 'Comprobando…',
    error: 'Error',
    failed_one: '{n} con error',
    failed_many: '{n} con error',
    not_loaded: 'HACS Refresh no está configurado',
    never_checked: 'Aún sin comprobar',
    checked: 'Comprobado {d}',
    next: 'próxima {d}',
    auto_off: 'comprobación automática desactivada',
    check_now: 'Buscar actualizaciones',
    updates_title: 'Actualizaciones disponibles',
    no_updates: 'Todos los repositorios están al día',
    failed_title: 'No se pudieron comprobar',
    error_title: 'La última comprobación falló',
    version: '{from} → {to}',
    ed_entity: 'Sensor de HACS Refresh',
    ed_entity_helper: 'Sensor de estado; déjalo vacío para encontrarlo automáticamente',
    ed_title: 'Título',
    ed_title_helper: 'Déjalo vacío para «Actualizaciones de HACS»',
    ed_show_updates: 'Actualizaciones disponibles',
    ed_show_updates_helper: 'Los repositorios de HACS con una actualización, según sus entidades de actualización',
    ed_show_failed: 'Repositorios que no se pudieron comprobar',
    ed_show_failed_helper: 'Y el error de una comprobación fallida',
    ed_check_button: 'Botón «Buscar actualizaciones»',
    ed_check_button_helper: 'Lanza una comprobación desde la cabecera',
    ed_hide_when_ok: 'Ocultar la tarjeta cuando todo esté al día',
    ed_hide_when_ok_helper: 'La tarjeta solo aparece durante una comprobación, o con una actualización o un error',
    ed_language: 'Idioma',
    ed_language_helper: 'Déjalo vacío para seguir a Home Assistant',
  },
};

const hrLang = (hass, config) => {
  const raw = String(config?.language || hass?.locale?.language || hass?.language || 'en');
  if (HR_I18N[raw]) return raw;
  const l = raw.slice(0, 2);
  return HR_I18N[l] ? l : 'en';
};

const hrT = (lang, key, vars = {}) =>
  (HR_I18N[lang]?.[key] ?? HR_I18N.en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');

const hrEsc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const HR_DEFAULTS = { show_updates: true, show_failed: true, check_button: true, hide_when_ok: false };

// The integration's entities, from the entity registry: { device: { status, last_check, button } }.
// Each entity is told apart by its translation key, else by the end of its entity ID (renamed IDs keep the key).
const HR_KEYS = { status: '_status', last_check: '_last_check', check_updates: '_check_for_updates' };
function hrDevices(registry) {
  const devices = {};
  for (const [id, e] of Object.entries(registry || {})) {
    if (e?.platform !== 'hacs_refresh') continue;
    const d = (devices[e.device_id || ''] ||= {});
    const key = Object.keys(HR_KEYS).find((k) => e.translation_key === k) || Object.keys(HR_KEYS).find((k) => id.endsWith(HR_KEYS[k]));
    if (!key) continue;
    d[key === 'check_updates' ? 'button' : key] = id;
  }
  return devices;
}

// HACS' own update entities: one per downloaded repository.
const hrHacsUpdates = (registry) =>
  Object.keys(registry || {}).filter((id) => id.startsWith('update.') && registry[id]?.platform === 'hacs');

class HacsRefreshCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement('hacs-refresh-card-editor');
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = { ...HR_DEFAULTS, ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._sig = null;
    this._render();
  }

  set hass(hass) {
    const old = this._hass;
    this._hass = hass;
    // Nothing the card shows changed: the same state objects, registry, language and minute ("3 min ago").
    const watched = this._watched;
    if (
      old &&
      this._sig &&
      watched &&
      hass.entities === old.entities &&
      watched.every((id) => hass.states[id] === old.states[id]) &&
      hrLang(hass, this._config) === hrLang(old, this._config) &&
      Math.floor(Date.now() / 60000) === this._sigMinute
    ) {
      return;
    }
    this._render();
  }

  getCardSize() {
    return 2 + (this._rows || 0);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: 'auto' };
  }

  _t(key, vars) {
    return hrT(hrLang(this._hass, this._config), key, vars);
  }

  // "3 hours ago", "in 21 hours"… in the card's language.
  _relative(iso) {
    const t = new Date(iso).getTime();
    if (!Number.isFinite(t)) return '';
    const m = (t - Date.now()) / 60000;
    const lang = hrLang(this._hass, this._config);
    let rtf;
    try {
      rtf = new Intl.RelativeTimeFormat(lang, { numeric: 'auto' });
    } catch {
      return new Date(t).toISOString();
    }
    // Rounded to the nearest unit: a check due in 20 h 59 min reads "in 21 hours".
    const a = Math.abs(m);
    if (a < 1) return rtf.format(0, 'second');
    if (a < 59.5) return rtf.format(Math.round(m), 'minute');
    if (a < 2850) return rtf.format(Math.round(m / 60), 'hour');
    return rtf.format(Math.round(m / 1440), 'day');
  }

  _absolute(iso) {
    const d = new Date(iso);
    if (!Number.isFinite(d.getTime())) return '';
    try {
      return d.toLocaleString(hrLang(this._hass, this._config), { dateStyle: 'medium', timeStyle: 'short' });
    } catch {
      return d.toISOString();
    }
  }

  // The integration's entities (cached per registry object, never when empty) and HACS' update entities.
  _lookup() {
    const registry = this._hass.entities;
    if (!this._reg || this._reg.registry !== registry) {
      const devices = hrDevices(registry);
      this._reg = Object.keys(devices).length ? { registry, devices, updates: hrHacsUpdates(registry) } : null;
    }
    const devices = this._reg?.devices || {};
    const updates = this._reg?.updates || [];
    let status = this._config.entity;
    if (!status) status = Object.values(devices).map((d) => d.status).find((id) => this._hass.states[id]);
    if (!status) return { updates };
    const device = Object.values(devices).find((d) => d.status === status) || {};
    return { ...device, status, updates };
  }

  _render() {
    if (!this._config || !this._hass || !this.shadowRoot) return;
    const c = this._config;
    const ids = this._lookup();
    const states = this._hass.states;
    const st = ids.status && states[ids.status];
    const lastSt = ids.last_check && states[ids.last_check];
    const buttonSt = ids.button && states[ids.button];
    this._watched = [ids.status, ids.last_check, ids.button, ...ids.updates].filter(Boolean);
    this._ids = ids;

    const minute = Math.floor(Date.now() / 60000);
    this._sigMinute = minute;
    const updateStates = ids.updates.map((id) => states[id]).filter((s) => s?.state === 'on');
    const sig = JSON.stringify([c, hrLang(this._hass, c), ids, st, lastSt, buttonSt?.state, updateStates, minute]);
    if (sig === this._sig) return;
    this._sig = sig;

    const a = st?.attributes || {};
    const running = st?.state === 'running';
    const failed = Array.isArray(a.failed) ? a.failed : [];
    const error = st?.state === 'error' ? a.error || this._t('error') : null;
    // The update entities are the truth; the sensor's count is the fallback when HACS' entities aren't there.
    const updates = updateStates
      .map((s) => ({
        id: s.entity_id,
        title: s.attributes.title || s.attributes.friendly_name || s.entity_id,
        from: s.attributes.installed_version,
        to: s.attributes.latest_version,
        picture: s.attributes.entity_picture,
      }))
      .sort((x, y) => String(x.title).localeCompare(String(y.title)));
    const count = ids.updates.length ? updates.length : Number(a.updates) || 0;
    const level = !st ? 'na' : error ? 'alert' : failed.length ? 'warn' : running || count ? 'info' : 'ok';

    const hidden = c.hide_when_ok && st && level === 'ok';
    this.style.display = hidden ? 'none' : '';
    if (hidden) return;

    const shownUpdates = c.show_updates && st ? updates : [];
    this._rows = shownUpdates.length + (c.show_failed ? failed.length : 0);

    const last = lastSt && !['unknown', 'unavailable'].includes(lastSt.state) ? lastSt.state : null;
    const next = lastSt?.attributes?.next_check;
    const interval = lastSt?.attributes?.scan_interval;
    const subtitle = !st
      ? ''
      : [
          last ? this._t('checked', { d: this._relative(last) }) : this._t('never_checked'),
          interval === 0 ? this._t('auto_off') : next ? this._t('next', { d: this._relative(next) }) : '',
        ]
          .filter(Boolean)
          .join(' · ');
    const icon = { ok: 'mdi:package-variant-closed-check', info: 'mdi:package-up', warn: 'mdi:package-variant-closed-remove', alert: 'mdi:alert-circle-outline', na: 'mdi:package-variant-closed' }[level];
    const pct = running && a.total ? Math.round((100 * (a.done || 0)) / a.total) : 0;

    this.shadowRoot.innerHTML = `
      <style>${HacsRefreshCard.styles}</style>
      <ha-card class="lvl-${level}">
        <div class="head">
          <div class="badge"><ha-icon icon="${icon}"></ha-icon></div>
          <div class="heading">
            <div class="title">${hrEsc(c.title || this._t('title'))}</div>
            ${subtitle ? `<div class="subtitle" title="${hrEsc(last ? this._absolute(last) : '')}">${hrEsc(subtitle)}</div>` : ''}
          </div>
          ${this._checkButton(running || buttonSt?.state === 'unavailable')}
          <div class="pill">${hrEsc(this._status(st, running, a, count, failed, error))}</div>
        </div>
        ${running ? `<div class="progress" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><span style="width:${pct}%"></span></div>` : ''}
        ${c.show_failed && error ? `<div class="error"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span><b>${hrEsc(this._t('error_title'))}</b><br>${hrEsc(error)}</span></div>` : ''}
        ${
          c.show_updates && st
            ? this._section(
                'updates_title',
                shownUpdates.length
                  ? shownUpdates.map((u) => this._updateRow(u)).join('')
                  : `<div class="empty">${hrEsc(this._t('no_updates'))}</div>`,
              )
            : ''
        }
        ${c.show_failed && failed.length ? this._section('failed_title', failed.map((f) => this._failedRow(f)).join('')) : ''}
      </ha-card>`;

    this.shadowRoot.querySelector('.check')?.addEventListener('click', () => this._check());
    for (const el of this.shadowRoot.querySelectorAll('.row[data-id]')) {
      el.addEventListener('click', () => this._moreInfo(el.dataset.id));
    }
    // A repository picture that doesn't load falls back to the generic icon.
    for (const img of this.shadowRoot.querySelectorAll('img.pic')) {
      img.addEventListener('error', () => img.parentElement?.classList.add('nopic'), { once: true });
    }
  }

  _status(st, running, a, count, failed, error) {
    if (!st) return this._t('not_loaded');
    if (running) return a.total ? this._t('checking', { done: a.done || 0, total: a.total }) : this._t('checking_short');
    if (error) return this._t('error');
    const parts = [];
    if (count) parts.push(this._t(count > 1 ? 'updates_many' : 'updates_one', { n: count }));
    if (failed.length) parts.push(this._t(failed.length > 1 ? 'failed_many' : 'failed_one', { n: failed.length }));
    return parts.length ? parts.join(' · ') : this._t('up_to_date');
  }

  _checkButton(busy) {
    if (!this._config.check_button || !this._ids.button) return '';
    const label = hrEsc(this._t('check_now'));
    return `<button class="check" title="${label}" aria-label="${label}"${busy ? ' disabled' : ''}><ha-icon icon="mdi:refresh"></ha-icon></button>`;
  }

  _check() {
    if (this._ids.button) this._hass.callService('button', 'press', { entity_id: this._ids.button });
  }

  _moreInfo(entityId) {
    const ev = new Event('hass-more-info', { bubbles: true, composed: true });
    ev.detail = { entityId };
    this.dispatchEvent(ev);
  }

  _section(key, body) {
    return `<div class="section"><div class="stitle">${hrEsc(this._t(key))}</div><div class="list">${body}</div></div>`;
  }

  _updateRow(u) {
    const version = u.from && u.to ? this._t('version', { from: u.from, to: u.to }) : u.to || '';
    const pic = u.picture ? `<img class="pic" src="${hrEsc(u.picture)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : '';
    return `
          <button class="row upd" data-id="${hrEsc(u.id)}" title="${hrEsc(u.title)}">
            <span class="ic${pic ? '' : ' nopic'}">${pic}<ha-icon icon="mdi:package-up"></ha-icon></span>
            <span class="txt">
              <span class="name">${hrEsc(u.title)}</span>
              ${version ? `<span class="sub">${hrEsc(version)}</span>` : ''}
            </span>
            <ha-icon class="chev" icon="mdi:chevron-right"></ha-icon>
          </button>`;
  }

  // "owner/repo" or "owner/repo: the error".
  _failedRow(f) {
    const text = String(f);
    const i = text.indexOf(': ');
    const name = i > 0 ? text.slice(0, i) : text;
    const why = i > 0 ? text.slice(i + 2) : '';
    return `
          <div class="row warn" title="${hrEsc(text)}">
            <span class="ic nopic"><ha-icon icon="mdi:alert-outline"></ha-icon></span>
            <span class="txt">
              <span class="name">${hrEsc(name)}</span>
              ${why ? `<span class="sub">${hrEsc(why)}</span>` : ''}
            </span>
          </div>`;
  }

  static get styles() {
    return `
      :host {
        --hr-ok: var(--success-color, #43a047);
        --hr-info: var(--info-color, #039be5);
        --hr-warn: var(--warning-color, #ffa600);
        --hr-alert: var(--error-color, #db4437);
        --hr-na: var(--disabled-color, #9e9e9e);
      }
      ha-card { padding: 12px; overflow: hidden; }
      ha-card.lvl-ok    { --c: var(--hr-ok); }
      ha-card.lvl-info  { --c: var(--hr-info); }
      ha-card.lvl-warn  { --c: var(--hr-warn); }
      ha-card.lvl-alert { --c: var(--hr-alert); }
      ha-card.lvl-na    { --c: var(--hr-na); }

      .head { display: flex; align-items: center; gap: 10px; }
      .badge { flex: none; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center;
               background: color-mix(in srgb, var(--c) 16%, transparent); color: var(--c); }
      .badge ha-icon { --mdc-icon-size: 24px; }
      .heading { flex: 1; min-width: 0; display: flex; flex-direction: column; }
      .title { font-size: 16px; font-weight: 500; line-height: 1.25; color: var(--primary-text-color);
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .subtitle { font-size: 12px; line-height: 1.3; color: var(--secondary-text-color);
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .pill { flex: none; font-size: 11px; font-weight: 500; padding: 1px 8px; border-radius: 999px;
              color: var(--c); background: color-mix(in srgb, var(--c) 14%, transparent); font-variant-numeric: tabular-nums; }
      .check { all: unset; cursor: pointer; flex: none; width: 26px; height: 26px; border-radius: 50%;
               display: grid; place-items: center; color: var(--secondary-text-color); }
      .check:hover { background: color-mix(in srgb, var(--secondary-text-color) 14%, transparent); color: var(--primary-text-color); }
      .check:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .check[disabled] { cursor: default; opacity: .4; background: none; }
      .check ha-icon { --mdc-icon-size: 16px; }

      .progress { height: 4px; margin-top: 10px; border-radius: 2px; overflow: hidden;
                  background: color-mix(in srgb, var(--secondary-text-color) 22%, transparent); }
      .progress span { display: block; height: 100%; border-radius: 2px; background: var(--c); }

      .error { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; padding: 8px 10px; border-radius: 10px;
               font-size: 12px; line-height: 1.35; color: var(--primary-text-color);
               background: color-mix(in srgb, var(--hr-alert) 12%, var(--secondary-background-color, transparent)); }
      .error ha-icon { --mdc-icon-size: 18px; color: var(--hr-alert); flex: none; }
      .error b { font-weight: 500; color: var(--hr-alert); }
      .error span { min-width: 0; overflow-wrap: anywhere; }

      .section { margin-top: 12px; }
      .stitle { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); margin: 0 2px 6px;
                text-transform: uppercase; letter-spacing: .04em; }
      .list { display: flex; flex-direction: column; gap: 6px; }
      .empty { font-size: 13px; color: var(--secondary-text-color); padding: 8px 10px; border-radius: 10px;
               background: var(--secondary-background-color, rgba(127,127,127,.08)); }
      .row { --t: var(--hr-info); all: unset; box-sizing: border-box; min-width: 0;
             display: flex; align-items: center; gap: 8px; padding: 5px 8px 5px 5px; border-radius: 10px;
             background: var(--secondary-background-color, rgba(127,127,127,.08)); }
      .row.warn { --t: var(--hr-warn); background: color-mix(in srgb, var(--t) 12%, var(--secondary-background-color, transparent)); }
      button.row { cursor: pointer; }
      button.row:hover { background: color-mix(in srgb, var(--t) 14%, var(--secondary-background-color, transparent)); }
      .row:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      .ic { position: relative; flex: none; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
            color: var(--t); background: color-mix(in srgb, var(--t) 18%, transparent); overflow: hidden; }
      .ic ha-icon { --mdc-icon-size: 16px; }
      .ic img.pic { position: absolute; inset: 5px; width: 18px; height: 18px; object-fit: contain; }
      .ic:not(.nopic) img.pic + ha-icon { visibility: hidden; }
      .ic.nopic img.pic { display: none; }
      .txt { flex: 1; display: flex; flex-direction: column; min-width: 0; }
      .name { font-size: 13px; font-weight: 500; line-height: 1.2; color: var(--primary-text-color);
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .sub { font-size: 11px; line-height: 1.2; color: var(--secondary-text-color); font-variant-numeric: tabular-nums;
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .row.warn .sub { color: var(--t); }
      .chev { flex: none; --mdc-icon-size: 18px; color: var(--secondary-text-color); }
    `;
  }
}

// ── Editor ───────────────────────────────────────────────────────────────────
const HR_HELPERS = ['entity', 'title', 'show_updates', 'show_failed', 'check_button', 'hide_when_ok', 'language'];

class HacsRefreshCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _update() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement('ha-form');
      const t = (key) => hrT(hrLang(this._hass, this._config), key);
      this._form.computeLabel = (s) => t(`ed_${s.name}`);
      this._form.computeHelper = (s) => (HR_HELPERS.includes(s.name) ? t(`ed_${s.name}_helper`) : undefined);
      this._form.addEventListener('value-changed', (ev) => {
        const config = { ...ev.detail.value };
        // Options left at their default are not written to the YAML.
        for (const k of Object.keys(config)) {
          if (config[k] === '' || config[k] == null || HR_DEFAULTS[k] === config[k]) delete config[k];
        }
        this.dispatchEvent(new CustomEvent('config-changed', { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    const c = this._config;
    const lang = hrLang(this._hass, c);
    // Reassigning the schema at every Home Assistant update would re-render ha-form while the user is typing.
    if (this._deps && this._deps.config === c && this._deps.lang === lang) return;
    this._deps = { config: c, lang };
    this._form.data = { ...HR_DEFAULTS, ...c };
    this._form.schema = [
      { name: 'entity', selector: { entity: { filter: { integration: 'hacs_refresh', domain: 'sensor' } } } },
      { name: 'title', selector: { text: {} } },
      { name: 'show_updates', selector: { boolean: {} } },
      { name: 'show_failed', selector: { boolean: {} } },
      { name: 'check_button', selector: { boolean: {} } },
      { name: 'hide_when_ok', selector: { boolean: {} } },
      {
        name: 'language',
        selector: {
          select: {
            mode: 'dropdown',
            options: [
              { value: 'en', label: 'English' },
              { value: 'fr', label: 'Français' },
              { value: 'de', label: 'Deutsch' },
              { value: 'es', label: 'Español' },
            ],
          },
        },
      },
    ];
  }
}

if (!customElements.get('hacs-refresh-card')) {
  customElements.define('hacs-refresh-card', HacsRefreshCard);
  customElements.define('hacs-refresh-card-editor', HacsRefreshCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'hacs-refresh-card',
    name: 'HACS Refresh Card',
    description: 'The HACS check of HACS Refresh: status, last and next check, updates available and failed repositories',
    preview: true,
    documentationURL: 'https://github.com/juju35/ha-hacs-refresh',
  });
  console.info(`%c HACS-REFRESH-CARD %c v${HACS_REFRESH_CARD_VERSION} `, 'background:#14b8a6;color:#fff;font-weight:700', '');
}
