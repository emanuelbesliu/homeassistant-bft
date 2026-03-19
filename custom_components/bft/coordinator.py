"""DataUpdateCoordinator for BFT integration.

Implements a resilient polling strategy that:
- Preserves the last known gate state during transient cloud outages
- Uses exponential backoff when the cloud is unreachable
- Automatically recovers when connectivity returns
- Switches to fast polling while the gate is in motion
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .bft_api import (
    BftApiClient,
    BftAuthError,
    BftConnectionError,
    get_gate_state,
)
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FAILURE_BACKOFF_BASE,
    FAILURE_BACKOFF_MAX,
    MAX_CONSECUTIVE_FAILURES,
)

_LOGGER = logging.getLogger(__name__)


class BftGateStatus:
    """Parsed gate status data."""

    def __init__(
        self,
        raw: dict[str, Any],
        state: str | None = None,
        stale: bool = False,
    ) -> None:
        """Initialize from raw API response.

        Args:
            raw: The raw diagnosis response from the API.
            state: Overridden state (used when carrying forward last-known state).
            stale: True if this status is being carried forward from a previous poll.
        """
        self.raw = raw
        self.state = state if state is not None else get_gate_state(raw)
        self.stale = stale
        self.first_engine_pos = raw.get("first_engine_pos_int", 0)
        self.second_engine_pos = raw.get("second_engine_pos_int", 0)
        self.first_engine_vel = raw.get("first_engine_vel_int", 0)
        self.second_engine_vel = raw.get("second_engine_vel_int", 0)

    @property
    def is_moving(self) -> bool:
        """Return True if the gate is currently moving."""
        return self.state == "moving"


class BftCoordinator(DataUpdateCoordinator[BftGateStatus]):
    """Coordinator for polling BFT gate status.

    Resilience strategy:
    - On a successful poll, store the result as last-known-good state.
    - On a transient failure (cloud timeout, connection error):
      1. Increment the failure counter.
      2. If we have a last-known-good state AND we haven't exceeded
         MAX_CONSECUTIVE_FAILURES, return the stale state so the entity
         stays available.  The cover entity exposes a `stale` attribute
         so dashboards/automations can distinguish fresh from stale data.
      3. Apply exponential backoff to the poll interval so we don't
         hammer a down API.
      4. Only raise UpdateFailed (which sets entity unavailable) after
         MAX_CONSECUTIVE_FAILURES with no recovery.
    - On recovery, reset the failure counter and restore normal polling.
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: BftApiClient,
        device_uuid: str,
        device_name: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"BFT {device_name}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.device_uuid = device_uuid
        self.device_name = device_name
        self._consecutive_failures = 0
        self._fast_poll = False
        self._last_good_status: BftGateStatus | None = None
        self._normal_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    @property
    def consecutive_failures(self) -> int:
        """Return the number of consecutive polling failures."""
        return self._consecutive_failures

    @property
    def is_degraded(self) -> bool:
        """Return True if we are serving stale data due to cloud issues."""
        return self._consecutive_failures > 0 and self._last_good_status is not None

    # ------------------------------------------------------------------
    # Poll interval management
    # ------------------------------------------------------------------

    def set_fast_poll(self, enabled: bool) -> None:
        """Enable or disable fast polling (used when gate is moving)."""
        if enabled and not self._fast_poll:
            self._fast_poll = True
            self.update_interval = timedelta(seconds=5)
            _LOGGER.debug("Fast polling enabled for %s", self.device_name)
        elif not enabled and self._fast_poll:
            self._fast_poll = False
            self.update_interval = self._normal_interval
            _LOGGER.debug(
                "Normal polling restored for %s (%ss)",
                self.device_name,
                self._normal_interval.total_seconds(),
            )

    def _apply_backoff(self) -> None:
        """Slow down polling using exponential backoff after failures."""
        if self._fast_poll:
            # Don't backoff during fast-poll (gate may be mid-movement)
            return

        backoff_seconds = min(
            FAILURE_BACKOFF_BASE ** self._consecutive_failures,
            FAILURE_BACKOFF_MAX,
        )
        self.update_interval = timedelta(seconds=backoff_seconds)
        _LOGGER.debug(
            "Backoff for %s: next poll in %ds (failure #%d)",
            self.device_name,
            backoff_seconds,
            self._consecutive_failures,
        )

    def _restore_normal_interval(self) -> None:
        """Restore the normal (or fast) poll interval after recovery."""
        if self._fast_poll:
            self.update_interval = timedelta(seconds=5)
        else:
            self.update_interval = self._normal_interval

    # ------------------------------------------------------------------
    # Core update logic
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> BftGateStatus:
        """Fetch status from BFT cloud API."""
        try:
            raw_status = await self.client.get_status(self.device_uuid)
        except BftAuthError as err:
            # Auth failures are not transient -- trigger re-auth flow immediately
            raise ConfigEntryAuthFailed(
                "BFT authentication failed. Please re-authenticate."
            ) from err
        except BftConnectionError as err:
            return self._handle_transient_failure(err)

        return self._handle_success(raw_status)

    def _handle_success(self, raw_status: dict[str, Any]) -> BftGateStatus:
        """Process a successful API response."""
        status = BftGateStatus(raw_status)

        if status.state is not None:
            # Genuine success with parseable state
            if self._consecutive_failures > 0:
                _LOGGER.info(
                    "Device %s recovered after %d consecutive failures",
                    self.device_name,
                    self._consecutive_failures,
                )
            self._consecutive_failures = 0
            self._last_good_status = status
            self._restore_normal_interval()
            self.set_fast_poll(status.is_moving)
            return status

        # Got a 200 response but status couldn't be parsed (empty diagnosis).
        # Treat it like a transient failure.
        _LOGGER.warning(
            "Device %s: unparseable diagnosis response: %s",
            self.device_name,
            raw_status,
        )
        return self._handle_transient_failure(
            BftConnectionError(
                f"Unparseable diagnosis for {self.device_name}"
            )
        )

    def _handle_transient_failure(
        self, err: Exception
    ) -> BftGateStatus:
        """Handle a transient cloud failure.

        Returns the last-known-good status (marked stale) if available,
        or raises UpdateFailed if we've exhausted the grace period.
        """
        self._consecutive_failures += 1
        self._apply_backoff()

        if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            # Only log on the threshold crossing, then every 10th failure
            if (
                self._consecutive_failures == MAX_CONSECUTIVE_FAILURES
                or self._consecutive_failures % 10 == 0
            ):
                _LOGGER.warning(
                    "Device %s: %d consecutive failures -- marking unavailable. "
                    "Will keep retrying with backoff.",
                    self.device_name,
                    self._consecutive_failures,
                )
            raise UpdateFailed(
                f"BFT cloud unreachable for {self.device_name} "
                f"after {self._consecutive_failures} attempts: {err}"
            ) from err

        if self._last_good_status is not None:
            _LOGGER.debug(
                "Device %s: cloud error (failure #%d/%d), "
                "returning last known state '%s'",
                self.device_name,
                self._consecutive_failures,
                MAX_CONSECUTIVE_FAILURES,
                self._last_good_status.state,
            )
            return BftGateStatus(
                raw=self._last_good_status.raw,
                state=self._last_good_status.state,
                stale=True,
            )

        # No previous good state and not yet at the threshold -- this is
        # likely during initial setup.  Let the entity stay unavailable
        # by raising, but log at debug level since it's expected.
        _LOGGER.debug(
            "Device %s: cloud error (failure #%d/%d), no previous state",
            self.device_name,
            self._consecutive_failures,
            MAX_CONSECUTIVE_FAILURES,
        )
        raise UpdateFailed(
            f"BFT cloud unreachable for {self.device_name}: {err}"
        ) from err
