"""Cover platform for BFT Gate Automation.

Creates one cover entity per BFT gate discovered in the account.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BftConfigEntry
from .const import DOMAIN
from .coordinator import BftCoordinator, BftGateStatus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BftConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BFT cover entities from a config entry.

    Creates one BftGateCover entity for each gate discovered in the account.
    """
    runtime_data = entry.runtime_data
    entities = [
        BftGateCover(coordinator, entry)
        for coordinator in runtime_data.coordinators.values()
    ]
    _LOGGER.info(
        "Adding %d BFT gate cover entities for account entry %s",
        len(entities),
        entry.title,
    )
    async_add_entities(entities)


class BftGateCover(CoordinatorEntity[BftCoordinator], CoverEntity):
    """Representation of a BFT gate cover."""

    _attr_device_class = CoverDeviceClass.GATE
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )
    _attr_has_entity_name = True
    _attr_name = None  # Use device name as entity name

    def __init__(
        self,
        coordinator: BftCoordinator,
        entry: BftConfigEntry,
    ) -> None:
        """Initialize the cover entity."""
        super().__init__(coordinator)

        self._attr_unique_id = f"bft_{coordinator.device_uuid}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_uuid)},
            name=coordinator.device_name,
            manufacturer="BFT",
            model="uControl Gate",
            configuration_url="https://ucontrol.bft-automation.com",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        The entity stays available as long as the coordinator has data,
        even if the data is stale (last-known-state during cloud outage).
        It only goes unavailable when the coordinator itself reports a
        failure via UpdateFailed (after MAX_CONSECUTIVE_FAILURES).
        """
        return self.coordinator.last_update_success and self._status is not None

    @property
    def _status(self) -> BftGateStatus | None:
        """Return the current gate status from coordinator data."""
        return self.coordinator.data

    @property
    def is_closed(self) -> bool | None:
        """Return True if the gate is closed."""
        if self._status is None or self._status.state is None:
            return None
        return self._status.state == "closed"

    @property
    def is_closing(self) -> bool | None:
        """Return True if the gate is closing."""
        # BFT API doesn't distinguish open/close direction during movement
        return None

    @property
    def is_opening(self) -> bool | None:
        """Return True if the gate is opening."""
        # BFT API doesn't distinguish open/close direction during movement
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for diagnostics."""
        attrs: dict[str, Any] = {
            "consecutive_failures": self.coordinator.consecutive_failures,
        }

        if self._status is not None:
            attrs["stale_data"] = self._status.stale
            if self._status.raw:
                attrs["first_engine_pos"] = self._status.first_engine_pos
                attrs["second_engine_pos"] = self._status.second_engine_pos
                attrs["first_engine_vel"] = self._status.first_engine_vel
                attrs["second_engine_vel"] = self._status.second_engine_vel

        if self.coordinator.device_uuid:
            attrs["device_uuid"] = self.coordinator.device_uuid

        return attrs

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the gate."""
        if self._status and self._status.state == "open":
            _LOGGER.debug("Gate %s already open, ignoring open command", self.coordinator.device_name)
            return

        await self.coordinator.client.open_gate(self.coordinator.device_uuid)
        self.coordinator.set_fast_poll(True)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the gate."""
        if self._status and self._status.state == "closed":
            _LOGGER.debug("Gate %s already closed, ignoring close command", self.coordinator.device_name)
            return

        await self.coordinator.client.close_gate(self.coordinator.device_uuid)
        self.coordinator.set_fast_poll(True)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the gate."""
        await self.coordinator.client.stop_gate(self.coordinator.device_uuid)
        await self.coordinator.async_request_refresh()
