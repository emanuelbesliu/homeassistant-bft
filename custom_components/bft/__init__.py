"""The BFT Gate Automation integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .bft_api import BftApiClient
from .const import CONF_RETRY_COUNT, CONF_TIMEOUT, DEFAULT_RETRY_COUNT, DEFAULT_TIMEOUT, DOMAIN
from .coordinator import BftCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER]

BftConfigEntry = ConfigEntry[BftCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BftConfigEntry) -> bool:
    """Set up BFT from a config entry."""
    session = async_get_clientsession(hass, verify_ssl=False)

    client = BftApiClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        timeout=entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        retry_count=entry.data.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
        session=session,
    )

    # Authenticate with BFT cloud
    await client.authenticate()

    device_uuid = entry.data["device_uuid"]
    device_name = entry.data.get("device_name", entry.title)

    coordinator = BftCoordinator(
        hass=hass,
        client=client,
        device_uuid=device_uuid,
        device_name=device_name,
    )

    # Perform initial data fetch -- raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BftConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
