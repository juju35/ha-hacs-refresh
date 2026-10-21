"""Fixtures for HACS Refresh tests: a stand-in for HACS' internal object."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


def make_repo(full_name: str, category: str = "integration", pending: bool = False, fail: bool = False):
    repo = SimpleNamespace(
        data=SimpleNamespace(full_name=full_name, category=category),
        pending_update=pending,
        update_repository=AsyncMock(side_effect=RuntimeError("GitHub down") if fail else None),
    )
    return repo


@pytest.fixture
def fake_hacs(hass):
    """hass.data["hacs"] with the attributes HACS Refresh uses, and HACS marked as loaded."""
    repos = [
        make_repo("hacs/integration"),
        make_repo("juju35/ha-parcel", pending=True),
        make_repo("piitaya/lovelace-mushroom", category="plugin"),
    ]
    hacs = SimpleNamespace(
        repositories=SimpleNamespace(list_downloaded=repos),
        data=SimpleNamespace(async_write=AsyncMock()),
        coordinators={"integration": MagicMock(), "plugin": MagicMock()},
        system=SimpleNamespace(disabled=False, disabled_reason=None),
        common=SimpleNamespace(categories={"integration", "plugin", "theme"}),
    )
    hass.data["hacs"] = hacs
    hass.config.components.add("hacs")
    return hacs
