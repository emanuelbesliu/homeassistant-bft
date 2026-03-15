"""Async API client for BFT uControl Cloud."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

import aiohttp

from .const import (
    DISPATCHER_API_URL,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    PARTICLE_URL,
)

_LOGGER = logging.getLogger(__name__)


class BftApiError(Exception):
    """Base exception for BFT API errors."""


class BftAuthError(BftApiError):
    """Authentication failed."""


class BftConnectionError(BftApiError):
    """Connection to BFT cloud failed."""


class BftDeviceNotFoundError(BftApiError):
    """Device not found in BFT cloud account."""


def _create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that skips certificate verification.

    The BFT uControl API has persistent certificate issues that require
    bypassing SSL verification.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class BftDevice:
    """Represents a BFT device discovered from the cloud."""

    def __init__(self, uuid: str, name: str) -> None:
        """Initialize a BFT device."""
        self.uuid = uuid
        self.name = name

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"BftDevice(uuid={self.uuid!r}, name={self.name!r})"


class BftApiClient:
    """Async client for the BFT uControl Cloud API."""

    def __init__(
        self,
        username: str,
        password: str,
        timeout: int = 10,
        retry_count: int = 3,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._retry_count = retry_count
        self._session = session
        self._access_token: str | None = None
        self._ssl_context = _create_ssl_context()
        self._owns_session = False

    @property
    def access_token(self) -> str | None:
        """Return the current access token."""
        return self._access_token

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the API client and clean up resources."""
        if self._access_token:
            try:
                await self.remove_token()
            except BftApiError:
                _LOGGER.debug("Error removing token during cleanup")
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def authenticate(self) -> str:
        """Authenticate with BFT cloud and return access token.

        Raises:
            BftAuthError: If authentication fails.
            BftConnectionError: If connection fails after retries.
        """
        url = f"{PARTICLE_URL}/oauth/token"
        data = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }
        auth = aiohttp.BasicAuth(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)
        session = await self._get_session()

        last_error: Exception | None = None
        for attempt in range(self._retry_count):
            try:
                _LOGGER.debug(
                    "Requesting access token (attempt %d/%d)",
                    attempt + 1,
                    self._retry_count,
                )
                async with session.post(
                    url,
                    data=data,
                    auth=auth,
                    timeout=self._timeout,
                    ssl=self._ssl_context,
                ) as resp:
                    if resp.status == 401:
                        raise BftAuthError("Invalid username or password")
                    if resp.status == 403:
                        raise BftAuthError("Account access denied")
                    resp.raise_for_status()
                    result = await resp.json()

                token = result.get("access_token")
                if not token:
                    raise BftAuthError(
                        f"No access token in API response: {result}"
                    )

                self._access_token = token
                _LOGGER.info("Successfully authenticated with BFT cloud")
                return token

            except (BftAuthError,):
                raise
            except asyncio.TimeoutError:
                last_error = BftConnectionError(
                    f"Timeout retrieving access token "
                    f"(attempt {attempt + 1}/{self._retry_count})"
                )
                _LOGGER.warning(str(last_error))
            except aiohttp.ClientError as ex:
                last_error = BftConnectionError(
                    f"Connection error retrieving access token "
                    f"(attempt {attempt + 1}/{self._retry_count}): {ex}"
                )
                _LOGGER.warning(str(last_error))

            if attempt < self._retry_count - 1:
                await asyncio.sleep(1)

        raise last_error or BftConnectionError("Failed to authenticate")

    async def get_devices(self) -> list[BftDevice]:
        """Discover all BFT devices associated with the account.

        Raises:
            BftConnectionError: If connection fails.
            BftApiError: If the API returns unexpected data.
        """
        if not self._access_token:
            raise BftApiError("Not authenticated. Call authenticate() first.")

        url = f"{PARTICLE_URL}/api/v1/users/?access_token={self._access_token}"
        session = await self._get_session()

        last_error: Exception | None = None
        for attempt in range(self._retry_count):
            try:
                async with session.get(
                    url, timeout=self._timeout, ssl=self._ssl_context
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.json()

                devices = []
                for automation in (
                    result.get("data", {}).get("automations", [])
                ):
                    info = automation.get("info", {})
                    name = info.get("name")
                    uuid = automation.get("uuid")
                    if name and uuid:
                        devices.append(BftDevice(uuid=uuid, name=name))

                _LOGGER.debug("Discovered %d BFT devices", len(devices))
                return devices

            except asyncio.TimeoutError:
                last_error = BftConnectionError(
                    f"Timeout discovering devices "
                    f"(attempt {attempt + 1}/{self._retry_count})"
                )
                _LOGGER.warning(str(last_error))
            except aiohttp.ClientError as ex:
                last_error = BftConnectionError(
                    f"Connection error discovering devices "
                    f"(attempt {attempt + 1}/{self._retry_count}): {ex}"
                )
                _LOGGER.warning(str(last_error))

            if attempt < self._retry_count - 1:
                await asyncio.sleep(1)

        raise last_error or BftConnectionError("Failed to discover devices")

    async def get_device_by_name(self, device_name: str) -> BftDevice:
        """Find a specific device by name.

        Raises:
            BftDeviceNotFoundError: If device not found.
            BftConnectionError: If connection fails.
        """
        devices = await self.get_devices()
        for device in devices:
            if device.name == device_name:
                return device

        available = [d.name for d in devices]
        raise BftDeviceNotFoundError(
            f"Device '{device_name}' not found. "
            f"Available devices: {available}"
        )

    async def execute_command(
        self, device_uuid: str, command: str
    ) -> dict[str, Any]:
        """Execute a command on a BFT device.

        Args:
            device_uuid: The UUID of the device.
            command: One of 'diagnosis', 'open', 'close', 'stop'.

        Returns:
            The JSON response from the API.

        Raises:
            BftConnectionError: If connection fails after retries.
            BftApiError: If the API returns an error.
        """
        if not self._access_token:
            raise BftApiError("Not authenticated. Call authenticate() first.")

        url = f"{DISPATCHER_API_URL}/{device_uuid}/execute/{command}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        session = await self._get_session()
        is_diagnosis = command == "diagnosis"

        last_error: Exception | None = None
        for attempt in range(self._retry_count):
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=self._timeout,
                    ssl=self._ssl_context,
                ) as resp:
                    if resp.status >= 500 and is_diagnosis:
                        if attempt < self._retry_count - 1:
                            _LOGGER.debug(
                                "Server error on diagnosis (HTTP %d, "
                                "attempt %d/%d), retrying...",
                                resp.status,
                                attempt + 1,
                                self._retry_count,
                            )
                            await asyncio.sleep(1)
                            continue
                        _LOGGER.warning(
                            "Server error on diagnosis (HTTP %d) "
                            "after %d attempts",
                            resp.status,
                            self._retry_count,
                        )
                        return {}

                    resp.raise_for_status()
                    return await resp.json()

            except asyncio.TimeoutError:
                last_error = BftConnectionError(
                    f"Timeout on {command} "
                    f"(attempt {attempt + 1}/{self._retry_count})"
                )
                _LOGGER.debug(str(last_error))
            except aiohttp.ClientError as ex:
                last_error = BftConnectionError(
                    f"Connection error on {command} "
                    f"(attempt {attempt + 1}/{self._retry_count}): {ex}"
                )
                _LOGGER.debug(str(last_error))

            if attempt < self._retry_count - 1:
                await asyncio.sleep(1)

        # For diagnosis, gracefully degrade instead of raising
        if is_diagnosis:
            _LOGGER.warning(
                "Failed diagnosis after %d attempts, returning empty status",
                self._retry_count,
            )
            return {}

        raise last_error or BftConnectionError(
            f"Failed to execute {command} after {self._retry_count} attempts"
        )

    async def get_status(self, device_uuid: str) -> dict[str, Any]:
        """Get the current status of a device (diagnosis command)."""
        return await self.execute_command(device_uuid, "diagnosis")

    async def open_gate(self, device_uuid: str) -> dict[str, Any]:
        """Open the gate."""
        return await self.execute_command(device_uuid, "open")

    async def close_gate(self, device_uuid: str) -> dict[str, Any]:
        """Close the gate."""
        return await self.execute_command(device_uuid, "close")

    async def stop_gate(self, device_uuid: str) -> dict[str, Any]:
        """Stop the gate."""
        return await self.execute_command(device_uuid, "stop")

    async def remove_token(self) -> None:
        """Remove the access token from the BFT cloud."""
        if not self._access_token:
            return

        url = f"{PARTICLE_URL}/v1/access_tokens/{self._access_token}"
        auth = aiohttp.BasicAuth(self._username, self._password)
        session = await self._get_session()

        try:
            async with session.delete(
                url,
                auth=auth,
                timeout=self._timeout,
                ssl=self._ssl_context,
            ) as resp:
                resp.raise_for_status()
                _LOGGER.debug("Successfully removed access token")
        except (aiohttp.ClientError, asyncio.TimeoutError) as ex:
            _LOGGER.warning("Unable to remove token: %s", ex)
        finally:
            self._access_token = None


def get_gate_state(status: dict[str, Any]) -> str | None:
    """Determine gate state from diagnosis status data.

    Returns:
        One of 'open', 'closed', 'moving', 'stopped', or None if
        the status data is invalid or empty.
    """
    if not status:
        return None

    try:
        first_pos = status.get("first_engine_pos_int", 0)
        second_pos = status.get("second_engine_pos_int", 0)
        first_vel = status.get("first_engine_vel_int", 0)
        second_vel = status.get("second_engine_vel_int", 0)
    except (TypeError, AttributeError):
        _LOGGER.warning("Invalid status format: %s", status)
        return None

    both_stopped = first_vel == 0 and second_vel == 0

    if both_stopped and first_pos == 100 and second_pos == 100:
        return "open"
    if both_stopped and first_pos == 0 and second_pos == 0:
        return "closed"
    if first_vel > 0 or second_vel > 0:
        return "moving"
    if both_stopped and (first_pos > 0 or second_pos > 0):
        return "stopped"

    return None
