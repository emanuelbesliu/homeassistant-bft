"""Config flow for BFT Gate Automation.

Single-step flow: the user enters BFT cloud credentials.  All gates
(automations) found under the account are automatically discovered and
added as cover entities.  One config entry = one BFT account.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .bft_api import BftApiClient, BftAuthError, BftConnectionError
from .const import (
    CONF_RETRY_COUNT,
    CONF_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
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

REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class BftConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BFT.

    One config entry per BFT account.  All gates in the account are
    auto-discovered during setup and exposed as separate cover entities.
    """

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the credentials step.

        Validates credentials, discovers devices, and creates the entry.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass, verify_ssl=False)
            client = BftApiClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                timeout=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                retry_count=user_input.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
                session=session,
            )

            try:
                await client.authenticate()
                devices = await client.get_devices()
            except BftAuthError:
                errors["base"] = "invalid_auth"
            except BftConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during BFT setup")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    # Unique ID = username (one entry per account)
                    await self.async_set_unique_id(
                        user_input[CONF_USERNAME].lower()
                    )
                    self._abort_if_unique_id_configured()

                    device_names = [d.name for d in devices]
                    return self.async_create_entry(
                        title=f"BFT ({user_input[CONF_USERNAME]})",
                        data={
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_TIMEOUT: user_input.get(
                                CONF_TIMEOUT, DEFAULT_TIMEOUT
                            ),
                            CONF_RETRY_COUNT: user_input.get(
                                CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT
                            ),
                        },
                        description_placeholders={
                            "device_count": str(len(devices)),
                            "device_names": ", ".join(device_names),
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Re-authentication flow
    # ------------------------------------------------------------------

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication trigger."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass, verify_ssl=False)
            client = BftApiClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=session,
            )

            try:
                await client.authenticate()
            except BftAuthError:
                errors["base"] = "invalid_auth"
            except BftConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during BFT re-auth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
        )
