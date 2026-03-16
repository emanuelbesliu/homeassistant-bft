"""The BFT Gate Automation integration.

Supports multiple BFT gates per account.  A single config entry represents
one BFT cloud account.  All gates (automations) discovered under that account
are exposed as separate cover entities, each backed by its own coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .bft_api import BftApiClient, BftDevice
from .const import CONF_RETRY_COUNT, CONF_TIMEOUT, DEFAULT_RETRY_COUNT, DEFAULT_TIMEOUT, DOMAIN
from .coordinator import BftCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER]


@dataclass
class BftRuntimeData:
    """Runtime data for a BFT config entry (one account, multiple devices)."""

    client: BftApiClient
    devices: list[BftDevice]
    coordinators: dict[str, BftCoordinator] = field(default_factory=dict)


BftConfigEntry = ConfigEntry[BftRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: BftConfigEntry) -> bool:
    """Set up BFT from a config entry.

    Authenticates once with the BFT cloud, discovers all gates in the
    account, and creates a coordinator for each gate.
    """
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

    # Discover all gates in the account
    devices = await client.get_devices()
    _LOGGER.info(
        "BFT account %s: discovered %d device(s): %s",
        entry.data[CONF_USERNAME],
        len(devices),
        [d.name for d in devices],
    )

    # Create one coordinator per device
    coordinators: dict[str, BftCoordinator] = {}
    for device in devices:
        coordinator = BftCoordinator(
            hass=hass,
            client=client,
            device_uuid=device.uuid,
            device_name=device.name,
        )
        # Perform initial data fetch -- raises ConfigEntryNotReady on failure
        await coordinator.async_config_entry_first_refresh()
        coordinators[device.uuid] = coordinator

    entry.runtime_data = BftRuntimeData(
        client=client,
        devices=devices,
        coordinators=coordinators,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BftConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
