"""Diagnostics support for BFT integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from . import BftConfigEntry

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, "access_token", "device_uuid"}


async def async_get_config_entry_diagnostics(
    hass: Any,
    entry: BftConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = entry.runtime_data

    devices_diag: list[dict[str, Any]] = []
    for device_uuid, coordinator in runtime_data.coordinators.items():
        device_info: dict[str, Any] = {
            "device_name": coordinator.device_name,
            "device_uuid": "**REDACTED**",
            "consecutive_failures": coordinator.consecutive_failures,
            "is_degraded": coordinator.is_degraded,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "last_update_success": coordinator.last_update_success,
        }

        if coordinator.data is not None:
            device_info["gate_status"] = {
                "state": coordinator.data.state,
                "stale": coordinator.data.stale,
                "first_engine_pos": coordinator.data.first_engine_pos,
                "second_engine_pos": coordinator.data.second_engine_pos,
                "first_engine_vel": coordinator.data.first_engine_vel,
                "second_engine_vel": coordinator.data.second_engine_vel,
                "raw_response": coordinator.data.raw,
            }

        devices_diag.append(device_info)

    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "device_count": len(runtime_data.devices),
        "devices": devices_diag,
    }
