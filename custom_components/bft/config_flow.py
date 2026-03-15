"""Config flow for BFT Gate Automation integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .bft_api import (
    BftApiClient,
    BftAuthError,
    BftConnectionError,
    BftDeviceNotFoundError,
)
from .const import (
    CONF_DEVICE_NAME,
    CONF_RETRY_COUNT,
    CONF_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            int, vol.Range(min=5, max=60)
        ),
        vol.Optional(CONF_RETRY_COUNT, default=DEFAULT_RETRY_COUNT): vol.All(
            int, vol.Range(min=1, max=20)
        ),
    }
)


class BftConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BFT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._timeout: int = DEFAULT_TIMEOUT
        self._retry_count: int = DEFAULT_RETRY_COUNT
        self._devices: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            self._retry_count = user_input.get(
                CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT
            )

            session = async_get_clientsession(self.hass, verify_ssl=False)
            client = BftApiClient(
                username=self._username,
                password=self._password,
                timeout=self._timeout,
                retry_count=self._retry_count,
                session=session,
            )

            try:
                await client.authenticate()
                devices = await client.get_devices()

                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self._devices = [
                        {"uuid": d.uuid, "name": d.name} for d in devices
                    ]
                    return await self.async_step_device()

            except BftAuthError:
                errors["base"] = "invalid_auth"
            except BftConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during BFT setup")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_name = user_input[CONF_DEVICE_NAME]

            # Find the device UUID
            device_uuid = None
            for dev in self._devices:
                if dev["name"] == device_name:
                    device_uuid = dev["uuid"]
                    break

            if device_uuid is None:
                errors["base"] = "device_not_found"
            else:
                # Check if this device is already configured
                await self.async_set_unique_id(f"bft_{device_uuid}")
                self._abort_if_unique_id_configured()

                name = user_input.get(CONF_NAME, device_name)

                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        CONF_DEVICE_NAME: device_name,
                        CONF_TIMEOUT: self._timeout,
                        CONF_RETRY_COUNT: self._retry_count,
                        "device_uuid": device_uuid,
                    },
                )

        # Build device selection schema
        device_names = [d["name"] for d in self._devices]
        device_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME): vol.In(device_names),
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="device",
            data_schema=device_schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication if credentials become invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-auth credential input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass, verify_ssl=False)
            client = BftApiClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                timeout=DEFAULT_TIMEOUT,
                retry_count=DEFAULT_RETRY_COUNT,
                session=session,
            )

            try:
                await client.authenticate()

                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
            except BftAuthError:
                errors["base"] = "invalid_auth"
            except BftConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during BFT re-auth")
                errors["base"] = "unknown"

        reauth_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=reauth_schema,
            errors=errors,
        )
