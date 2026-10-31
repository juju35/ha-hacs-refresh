"""Render the HACS Refresh card with mock data and save the README screenshots.

Usage: python scripts/screenshots.py  (needs `pip install playwright` and `playwright install chromium`)
CHROMIUM_PATH=/path/to/chrome to use another browser. The clock is frozen so "3 hours ago" and "in 21 hours" stay the same.
Repository pictures are not fetched (the generic icon is shown), so the captures don't depend on the network.
Every capture keeps a 16 px frame of the theme background around the card.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CARD_JS = (ROOT / "custom_components/hacs_refresh/frontend/hacs-refresh-card.js").read_text()
NOW = datetime.fromisoformat("2026-10-31T14:00:00+01:00")
WIDTH = 460

THEMES = {
    "light": {
        "--primary-background-color": "#e8eaed",
        "--secondary-background-color": "#ececec",
        "--card-background-color": "#ffffff",
        "--primary-text-color": "#212121",
        "--secondary-text-color": "#727272",
        "--divider-color": "rgba(0,0,0,.12)",
    },
    "dark": {
        "--primary-background-color": "#111111",
        "--secondary-background-color": "#282828",
        "--card-background-color": "#1c1c1c",
        "--primary-text-color": "#e1e1e1",
        "--secondary-text-color": "#9b9b9b",
        "--divider-color": "rgba(225,225,225,.12)",
    },
}
COMMON = {
    "--primary-color": "#03a9f4",
    "--success-color": "#43a047",
    "--warning-color": "#ffa600",
    "--error-color": "#db4437",
    "--text-primary-color": "#ffffff",
}

# Material Design Icons paths used by the card (from @mdi/js).
ICONS = {
    "package-variant-closed-check": "M12 2C11.8 2 11.6 2.1 11.4 2.2L3.5 6.6C3.2 6.8 3 7.1 3 7.5V16.5C3 16.9 3.2 17.2 3.5 17.4L11.4 21.8C11.6 21.9 11.8 22 12 22S12.4 21.9 12.6 21.8L13.5 21.3C13.2 20.7 13.1 20 13 19.3V12.6L19 9.2V13C19.7 13 20.4 13.1 21 13.3V7.5C21 7.1 20.8 6.8 20.5 6.6L12.6 2.2C12.4 2.1 12.2 2 12 2M12 4.2L18 7.5L16 8.6L10.1 5.2L12 4.2M8.1 6.3L14 9.8L12 10.9L6 7.5L8.1 6.3M5 9.2L11 12.6V19.3L5 15.9V9.2M21.3 15.8L17.7 19.4L16.1 17.8L15 19L17.8 22L22.6 17.2L21.3 15.8Z",
    "package-up": "M20.54,5.23C20.83,5.57 21,6 21,6.5V19A2,2 0 0,1 19,21H5A2,2 0 0,1 3,19V6.5C3,6 3.17,5.57 3.46,5.23L4.84,3.55C5.12,3.21 5.53,3 6,3H18C18.47,3 18.88,3.21 19.15,3.55L20.54,5.23M5.12,5H18.87L17.93,4H5.93L5.12,5M12,9.5L6.5,15H10V17H14V15H17.5L12,9.5Z",
    "package-variant-closed-remove": "M13 12.6L19 9.2V13C19.7 13 20.4 13.1 21 13.4V7.5C21 7.1 20.8 6.8 20.5 6.6L12.6 2.2C12.4 2.1 12.2 2 12 2S11.6 2.1 11.4 2.2L3.5 6.6C3.2 6.8 3 7.1 3 7.5V16.5C3 16.9 3.2 17.2 3.5 17.4L11.4 21.8C11.6 21.9 11.8 22 12 22S12.4 21.9 12.6 21.8L13.5 21.3C13.2 20.7 13.1 20 13 19.3M12 4.2L18 7.5L16 8.6L10.1 5.2L12 4.2M11 19.3L5 15.9V9.2L11 12.6V19.3M12 10.8L6 7.5L8 6.3L14 9.8L12 10.8M16.9 15.5L19 17.6L21.1 15.5L22.5 16.9L20.4 19L22.5 21.1L21.1 22.5L19 20.4L16.9 22.5L15.5 21.1L17.6 19L15.5 16.9L16.9 15.5Z",
    "alert-circle-outline": "M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z",
    "package-variant-closed": "M21,16.5C21,16.88 20.79,17.21 20.47,17.38L12.57,21.82C12.41,21.94 12.21,22 12,22C11.79,22 11.59,21.94 11.43,21.82L3.53,17.38C3.21,17.21 3,16.88 3,16.5V7.5C3,7.12 3.21,6.79 3.53,6.62L11.43,2.18C11.59,2.06 11.79,2 12,2C12.21,2 12.41,2.06 12.57,2.18L20.47,6.62C20.79,6.79 21,7.12 21,7.5V16.5M12,4.15L10.11,5.22L16,8.61L17.96,7.5L12,4.15M6.04,7.5L12,10.85L13.96,9.75L8.08,6.35L6.04,7.5M5,15.91L11,19.29V12.58L5,9.21V15.91M19,15.91V9.21L13,12.58V19.29L19,15.91Z",
    "refresh": "M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z",
    "chevron-right": "M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",
    "alert-outline": "M12,2L1,21H23M12,6L19.53,19H4.47M11,10V14H13V10M11,16V18H13V16",
}

# Minimal stand-ins for Home Assistant's <ha-card> and <ha-icon>.
HA_ELEMENTS = (
    "const ICONS = "
    + json.dumps(ICONS)
    + ";"
    + """
customElements.define("ha-card", class extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" }).innerHTML =
      "<style>:host{display:block;background:var(--card-background-color);border-radius:12px;" +
      "border:1px solid var(--divider-color);color:var(--primary-text-color);overflow:hidden}</style><slot></slot>";
  }
});
customElements.define("ha-icon", class extends HTMLElement {
  static get observedAttributes() { return ["icon"]; }
  connectedCallback() { this._draw(); }
  attributeChangedCallback() { this._draw(); }
  _draw() {
    const path = ICONS[(this.getAttribute("icon") || "").replace("mdi:", "")] || "";
    this.style.display = "inline-flex";
    this.innerHTML = '<svg viewBox="0 0 24 24" style="width:var(--mdc-icon-size,24px);height:var(--mdc-icon-size,24px);fill:currentColor"><path d="' + path + '"/></svg>';
  }
});"""
)

STATUS = "sensor.hacs_refresh_status"
LAST_CHECK = "sensor.hacs_refresh_last_check"
BUTTON = "button.hacs_refresh_check_for_updates"


def at(**delta) -> str:
    return (NOW + timedelta(**delta)).isoformat()


# Mock HACS repositories: (update entity, title, installed, latest).
REPOSITORIES = [
    ("update.mushroom_update", "Mushroom", "v4.4.0", "v4.5.0"),
    ("update.card_mod_update", "card-mod", "v3.4.4", "v3.4.5"),
    ("update.auto_entities_update", "auto-entities", "v1.13.0", "v1.14.1"),
    ("update.button_card_update", "button-card", "v4.3.0", "v4.3.0"),
    ("update.hacs_update", "HACS", "2.0.5", "2.0.5"),
]


def mock_hass(status, attrs, with_updates):
    platform = {"platform": "hacs_refresh", "device_id": "hacs_refresh"}
    states = {
        STATUS: {
            "entity_id": STATUS,
            "state": status,
            "attributes": {"done": 0, "total": 0, "updates": 0, "failed": [], "error": None, **attrs},
        },
        LAST_CHECK: {
            "entity_id": LAST_CHECK,
            "state": at(hours=-3),
            "attributes": {"scan_interval": 24, "next_check": at(hours=21)},
        },
        BUTTON: {"entity_id": BUTTON, "state": "unknown", "attributes": {}},
    }
    entities = {
        STATUS: {**platform, "translation_key": "status"},
        LAST_CHECK: {**platform, "translation_key": "last_check"},
        BUTTON: {**platform, "translation_key": "check_updates"},
    }
    for entity_id, title, installed, latest in REPOSITORIES:
        update = with_updates and installed != latest
        states[entity_id] = {
            "entity_id": entity_id,
            "state": "on" if update else "off",
            "attributes": {
                "title": title,
                "installed_version": installed,
                "latest_version": latest if update else installed,
                "entity_picture": f"https://brands.home-assistant.io/_/{entity_id}/icon.png",
            },
        }
        entities[entity_id] = {"platform": "hacs"}
    return {"states": states, "entities": entities, "language": "en", "locale": {"language": "en"}}


UPDATES = ("idle", {"updates": 3, "failed": ["someone/abandoned-card: 404 Not Found"]}, True)
CHECKING = ("running", {"done": 31, "total": 48}, True)
UP_TO_DATE = ("idle", {}, False)
SHOTS = [
    {"file": "card", "theme": "light", "hass": UPDATES},
    {"file": "card-dark", "theme": "dark", "hass": UPDATES},
    {"file": "card-checking", "theme": "light", "hass": CHECKING},
    {"file": "card-checking-dark", "theme": "dark", "hass": CHECKING},
    {"file": "card-ok", "theme": "light", "hass": UP_TO_DATE},
    {"file": "card-ok-dark", "theme": "dark", "hass": UP_TO_DATE},
]


def page_html(theme):
    variables = "".join(f"{k}:{v};" for k, v in {**THEMES[theme], **COMMON}.items())
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ {variables} }}
body {{ margin: 0; padding: 16px; background: var(--primary-background-color);
       font-family: Roboto, "Segoe UI", Helvetica, Arial, sans-serif; width: {WIDTH}px; }}
</style></head><body><div id="root"></div></body></html>"""


MOUNT = """([hass, dark]) => {
    const el = document.createElement("hacs-refresh-card");
    el.setConfig({ type: "custom:hacs-refresh-card" });
    el.hass = { ...hass, themes: { darkMode: dark }, callService: async () => {} };
    document.getElementById("root").appendChild(el);
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        for shot in SHOTS:
            page = browser.new_page(device_scale_factor=2, viewport={"width": 1000, "height": 1600})
            page.on("pageerror", lambda err, name=shot["file"]: print(f"{name}: page error: {err}"))
            # No repository picture: the generic icon, the same on every machine.
            page.route("https://brands.home-assistant.io/**", lambda route: route.abort())
            page.clock.set_fixed_time(NOW.isoformat())
            page.set_content(page_html(shot["theme"]))
            page.add_script_tag(content=HA_ELEMENTS)
            page.add_script_tag(content=CARD_JS)
            page.evaluate(MOUNT, [mock_hass(*shot["hass"]), shot["theme"] == "dark"])
            page.wait_for_timeout(400)
            box = page.locator("#root").bounding_box()
            clip = {"x": 0, "y": 0, "width": WIDTH + 32, "height": int(box["height"] + 0.999) + 32}
            path = ROOT / "screenshots" / f"{shot['file']}.png"
            path.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(path), clip=clip, animations="disabled")
            print(path.relative_to(ROOT))
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
