"""Translations of the integration: every language has the English keys and placeholders."""

import json
import re
from pathlib import Path

import pytest

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "hacs_refresh" / "translations"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
# Proper nouns and brands, kept in Latin script in the Cyrillic translation.
NAMES = re.compile(r"HACS|Refresh|Home Assistant")


def _load(lang: str) -> dict:
    return json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8"))


def _flatten(data: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, path))
        else:
            out[path] = value
    return out


LANGUAGES = sorted(p.stem for p in TRANSLATIONS.glob("*.json") if p.stem != "en")


def test_every_language_exists() -> None:
    """Same languages as the card."""
    assert set(LANGUAGES) == {"de", "es", "fr", "it", "nl", "pl", "pt", "sr", "sr-Latn"}


def test_serbian_files_exist() -> None:
    """Home Assistant uses sr for Cyrillic and sr-Latn for Latin."""
    assert {"sr", "sr-Latn"} <= set(LANGUAGES)


@pytest.mark.parametrize("lang", LANGUAGES)
def test_same_keys_and_placeholders_as_english(lang: str) -> None:
    """Same key paths as en.json, and the same placeholders in each string."""
    en = _flatten(_load("en"))
    other = _flatten(_load(lang))
    assert sorted(other) == sorted(en)
    for path, text in en.items():
        assert sorted(PLACEHOLDER.findall(other[path])) == sorted(PLACEHOLDER.findall(text)), path
        assert isinstance(other[path], str) and other[path].strip(), f"{lang} {path} is empty"


def test_serbian_scripts() -> None:
    """No Latin letter in sr (apart from names and placeholders), no Cyrillic in sr-Latn."""
    for path, text in _flatten(_load("sr")).items():
        assert not re.search(r"[A-Za-z]", NAMES.sub("", PLACEHOLDER.sub("", text))), f"sr {path}: {text}"
    for path, text in _flatten(_load("sr-Latn")).items():
        assert not re.search(r"[Ѐ-ӿ]", text), f"sr-Latn {path}: {text}"
