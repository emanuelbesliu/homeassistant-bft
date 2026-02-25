"""Platform for the BFT cover component."""

from datetime import timedelta
import logging
import time
import requests
import voluptuous as vol
import asyncio
from functools import partial

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
    PLATFORM_SCHEMA,
)
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_COVERS,
    CONF_DEVICE,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_CLOSED,
    STATE_OPEN,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ATTR_AVAILABLE = "available"
ATTR_TIME_IN_STATE = "time_in_state"
DEFAULT_NAME = "BFT"
STATE_MOVING = "moving"
STATE_OFFLINE = "offline"
STATE_STOPPED = "stopped"

# Configuration options
CONF_TIMEOUT = "timeout"
CONF_RETRY_COUNT = "retry_count"
CONF_SKIP_INITIAL_UPDATE = "skip_initial_update"

DEFAULT_TIMEOUT = 10
DEFAULT_RETRY_COUNT = 3  # Increased due to common SSL errors with BFT API
DEFAULT_SKIP_INITIAL_UPDATE = False

STATES_MAP = {
    "open": STATE_OPEN,
    "moving": STATE_MOVING,
    "closed": STATE_CLOSED,
    "stopped": STATE_STOPPED,
}

COVER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ACCESS_TOKEN): cv.string,
        vol.Optional(CONF_DEVICE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_RETRY_COUNT, default=DEFAULT_RETRY_COUNT): cv.positive_int,
        vol.Optional(CONF_SKIP_INITIAL_UPDATE, default=DEFAULT_SKIP_INITIAL_UPDATE): cv.boolean,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_COVERS): cv.schema_with_slug_keys(COVER_SCHEMA)}
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the BFT covers asynchronously."""
    covers = []
    devices = config.get(CONF_COVERS)

    for device_name, device_config in devices.items():
        args = {
            "name": device_config.get(CONF_NAME),
            "device": device_config.get(CONF_DEVICE),
            "username": device_config.get(CONF_USERNAME),
            "password": device_config.get(CONF_PASSWORD),
            "access_token": device_config.get(CONF_ACCESS_TOKEN),
            "timeout": device_config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            "retry_count": device_config.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
            "skip_initial_update": device_config.get(CONF_SKIP_INITIAL_UPDATE, DEFAULT_SKIP_INITIAL_UPDATE),
        }
        
        cover = BftCover(hass, args)
        
        # Initialize the cover asynchronously without blocking startup
        if not args["skip_initial_update"]:
            # Schedule initialization in background to not block startup
            hass.async_create_task(cover.async_initialize())
        
        covers.append(cover)

    async_add_entities(covers, update_before_add=False)
    return True

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BFT covers (legacy sync method)."""
    covers = []
    devices = config.get(CONF_COVERS)
    skip_initial = DEFAULT_SKIP_INITIAL_UPDATE

    for device_name, device_config in devices.items():
        args = {
            "name": device_config.get(CONF_NAME),
            "device": device_config.get(CONF_DEVICE),
            "username": device_config.get(CONF_USERNAME),
            "password": device_config.get(CONF_PASSWORD),
            "access_token": device_config.get(CONF_ACCESS_TOKEN),
            "timeout": device_config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            "retry_count": device_config.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
            "skip_initial_update": device_config.get(CONF_SKIP_INITIAL_UPDATE, DEFAULT_SKIP_INITIAL_UPDATE),
        }
        skip_initial = args["skip_initial_update"]
        covers.append(BftCover(hass, args))

    add_entities(covers, update_before_add=not skip_initial)

def _get_gate_status(status):
    """Get gate status from position and velocity."""
    _LOGGER.debug("Current Status: %s", status)
    
    try:
        first_engine_pos_int = status.get("first_engine_pos_int", 0)
        second_engine_pos_int = status.get("second_engine_pos_int", 0)
        first_engine_vel_int = status.get("first_engine_vel_int", 0)
        second_engine_vel_int = status.get("second_engine_vel_int", 0)
    except (KeyError, TypeError, AttributeError) as ex:
        _LOGGER.warning("Invalid status format: %s - %s", status, ex)
        return None

    if (first_engine_pos_int == 100 and second_engine_pos_int == 100) and (
        first_engine_vel_int == 0 and second_engine_vel_int == 0
    ):
        _LOGGER.debug("Gate state: open")
        return STATES_MAP.get("open", None)
    if (first_engine_vel_int == 0 and second_engine_vel_int == 0) and (
        first_engine_pos_int > 0 or second_engine_pos_int > 0
    ):
        _LOGGER.debug("Gate state: stopped")
        return STATES_MAP.get("stopped", None)
    if (first_engine_pos_int == 0 and second_engine_pos_int == 0) and (
        first_engine_vel_int == 0 and second_engine_vel_int == 0
    ):
        _LOGGER.debug("Gate state: closed")
        return STATES_MAP.get("closed", None)
    if first_engine_vel_int > 0 or second_engine_vel_int > 0:
        _LOGGER.debug("Gate state: moving")
        return STATES_MAP.get("moving", None)
    
    return None

class BftCover(CoverEntity):
    """Representation of a BFT cover."""

    def __init__(self, hass, args):
        """Initialize the cover."""
        self.particle_url = "https://ucontrol-api.bft-automation.com"
        self.dispatcher_api_url = (
            "https://ucontrol-dispatcher.bft-automation.com/automations"
        )
        self.hass = hass
        self._name = args["name"]
        self.device_name = args["device"]
        self.device_id = None
        self.access_token = args["access_token"]
        self._obtained_token = False
        self._username = args["username"]
        self._password = args["password"]
        self._timeout = args.get("timeout", DEFAULT_TIMEOUT)
        self._retry_count = args.get("retry_count", DEFAULT_RETRY_COUNT)
        self._skip_initial_update = args.get("skip_initial_update", DEFAULT_SKIP_INITIAL_UPDATE)
        self._state = None
        self.time_in_state = None
        self._unsub_listener_cover = None
        self._available = False  # Start as unavailable until first successful update
        self._initialization_failed = False
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        self._attr_device_class = CoverDeviceClass.GATE
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

        _LOGGER.info(
            "Initializing BFT cover '%s' (device: %s, timeout: %ss, retries: %d, skip_initial: %s)",
            self._name, self.device_name, self._timeout, self._retry_count, self._skip_initial_update
        )

    async def async_initialize(self):
        """Initialize the cover asynchronously (non-blocking)."""
        _LOGGER.debug("Starting async initialization for %s", self._name)
        
        try:
            # Get token if not provided
            if self.access_token is None:
                self.access_token = await self.hass.async_add_executor_job(
                    self.get_token
                )
                self._obtained_token = True

            if self.access_token is None:
                _LOGGER.error(
                    "Failed to obtain access token for %s. Check username and password. "
                    "Device will be unavailable until manually reloaded.",
                    self._name
                )
                self._initialization_failed = True
                return

            # Get device ID
            if self.device_id is None:
                self.device_id = await self.hass.async_add_executor_job(
                    self.get_device_id
                )

            if self.device_id is None:
                _LOGGER.error(
                    "Failed to obtain device ID for %s. Check device name '%s'. "
                    "Device will be unavailable until manually reloaded.",
                    self._name, self.device_name
                )
                self._initialization_failed = True
                return

            # Perform initial update with extended timeout
            _LOGGER.debug("Performing initial status update for %s", self._name)
            await self.hass.async_add_executor_job(self.update)
            
            _LOGGER.info("Successfully initialized BFT cover '%s'", self._name)
            
        except Exception as ex:
            _LOGGER.error(
                "Error during initialization of %s: %s. Device will retry on next update.",
                self._name, ex
            )
            self._initialization_failed = True

    def __del__(self):
        """Try to remove token."""
        if self._obtained_token and self.access_token is not None:
            try:
                self.remove_token()
            except Exception as ex:
                _LOGGER.debug("Error removing token during cleanup: %s", ex)

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def should_poll(self):
        """Enable polling for status updates."""
        return True

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        if self.time_in_state is not None:
            data[ATTR_TIME_IN_STATE] = self.time_in_state
        if self.device_id is not None:
            data["device_id"] = self.device_id
        data["consecutive_failures"] = self._consecutive_failures
        data["initialization_failed"] = self._initialization_failed
        return data

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._state is None:
            return None
        return self._state == STATE_CLOSED

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return CoverDeviceClass.GATE

    @property
    def supported_features(self):
        """Flag supported features."""
        return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    def get_token(self):
        """Get new token for usage during this session."""
        args = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }
        url = f"{self.particle_url}/oauth/token"
        
        for attempt in range(self._retry_count):
            try:
                _LOGGER.debug("Requesting access token (attempt %d/%d)", attempt + 1, self._retry_count)
                ret = requests.post(
                    url, 
                    auth=("particle", "particle"), 
                    data=args, 
                    timeout=self._timeout
                )
                ret.raise_for_status()
                response_json = ret.json()
                token = response_json.get("access_token")
                if not token:
                    _LOGGER.error("No access token in API response: %s", response_json)
                    return None
                _LOGGER.info("Successfully retrieved access token")
                return token
            except requests.exceptions.Timeout:
                _LOGGER.warning(
                    "Timeout retrieving access token (attempt %d/%d, timeout=%ds)",
                    attempt + 1, self._retry_count, self._timeout
                )
                if attempt < self._retry_count - 1:
                    continue
            except requests.exceptions.RequestException as ex:
                _LOGGER.error("Failed to retrieve access token (attempt %d/%d): %s", attempt + 1, self._retry_count, ex)
                if attempt < self._retry_count - 1:
                    continue
            except ValueError as ex:
                _LOGGER.error("Invalid JSON response from token endpoint: %s", ex)
                return None
        
        return None

    def get_device_id(self):
        """Get device id from name."""
        if not self.access_token:
            _LOGGER.error("Cannot retrieve device ID: No access token available")
            return None
        
        url = f"{self.particle_url}/api/v1/users/?access_token={self.access_token}"
        
        for attempt in range(self._retry_count):
            try:
                _LOGGER.debug("Requesting device ID (attempt %d/%d)", attempt + 1, self._retry_count)
                ret = requests.get(url, timeout=self._timeout)
                ret.raise_for_status()
                response_json = ret.json()
                for automations in response_json.get("data", {}).get("automations", []):
                    if automations.get("info", {}).get("name") == self.device_name:
                        device_uuid = automations["uuid"]
                        _LOGGER.info(
                            "Found device '%s' with UUID: %s", 
                            self.device_name, device_uuid
                        )
                        return device_uuid
                _LOGGER.warning("Device '%s' not found in API response", self.device_name)
                return None
            except requests.exceptions.Timeout:
                _LOGGER.warning(
                    "Timeout retrieving device ID (attempt %d/%d, timeout=%ds)",
                    attempt + 1, self._retry_count, self._timeout
                )
                if attempt < self._retry_count - 1:
                    continue
            except requests.exceptions.RequestException as ex:
                _LOGGER.error("Failed to retrieve device ID (attempt %d/%d): %s", attempt + 1, self._retry_count, ex)
                if attempt < self._retry_count - 1:
                    continue
            except (ValueError, KeyError) as ex:
                _LOGGER.error("Invalid response format for device ID: %s", ex)
                return None
        
        return None

    def remove_token(self):
        """Remove authorization token from API."""
        if not self.access_token:
            _LOGGER.debug("No access token to remove")
            return None
        url = f"{self.particle_url}/v1/access_tokens/{self.access_token}"
        try:
            ret = requests.delete(url, auth=(self._username, self._password), timeout=self._timeout)
            ret.raise_for_status()
            _LOGGER.debug("Successfully removed access token")
            return ret.text
        except requests.exceptions.RequestException as ex:
            _LOGGER.warning("Unable to remove token: %s", ex)
            return None

    def _start_watcher(self, command):
        """Start watcher."""
        _LOGGER.debug("Starting Watcher for command: %s", command)
        if self._unsub_listener_cover is None:
            self._unsub_listener_cover = track_utc_time_change(
                self.hass, self._check_state
            )

    def _check_state(self, now):
        """Check the state of the service during an operation."""
        self.schedule_update_ha_state(True)

    def close_cover(self, **kwargs):
        """Close the cover."""
        try:
            if self._state != STATE_CLOSED:
                ret = self._get_command("close")
                self._start_watcher("close")
                return ret.get("status") == "done"
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error("Unable to connect to server during close: %s", ex)
            self._handle_connection_failure()
        except requests.exceptions.ReadTimeout as ex:
            _LOGGER.error("Timeout connecting to server during close: %s", ex)
            self._handle_connection_failure()
        except (KeyError, ValueError) as ex:
            _LOGGER.warning(
                "BFT device %s returned invalid data during close: %s", self.device_id, ex
            )
            self._handle_connection_failure()
        return False

    def open_cover(self, **kwargs):
        """Open the cover."""
        try:
            if self._state != STATE_OPEN:
                ret = self._get_command("open")
                self._start_watcher("open")
                return ret.get("status") == "done"
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error("Unable to connect to server during open: %s", ex)
            self._handle_connection_failure()
        except requests.exceptions.ReadTimeout as ex:
            _LOGGER.error("Timeout connecting to server during open: %s", ex)
            self._handle_connection_failure()
        except (KeyError, ValueError) as ex:
            _LOGGER.warning(
                "BFT device %s returned invalid data during open: %s", self.device_id, ex
            )
            self._handle_connection_failure()
        return False

    def stop_cover(self, **kwargs):
        """Stop the cover where it is."""
        try:
            if self._state != STATE_STOPPED:
                ret = self._get_command("stop")
                self._start_watcher("stop")
                return ret.get("status") == "done"
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error("Unable to connect to server during stop: %s", ex)
            self._handle_connection_failure()
        except requests.exceptions.ReadTimeout as ex:
            _LOGGER.error("Timeout connecting to server during stop: %s", ex)
            self._handle_connection_failure()
        except (KeyError, ValueError) as ex:
            _LOGGER.warning(
                "BFT device %s returned invalid data during stop: %s", self.device_id, ex
            )
            self._handle_connection_failure()
        return False

    def _handle_connection_failure(self):
        """Handle connection failures with exponential backoff logic."""
        self._consecutive_failures += 1
        
        if self._consecutive_failures >= self._max_consecutive_failures:
            _LOGGER.warning(
                "Device %s marked unavailable after %d consecutive failures. "
                "Will retry on next update cycle.",
                self._name, self._consecutive_failures
            )
            self._available = False
        
        # Don't set state to offline immediately - preserve last known state
        # This prevents UI flicker on temporary network issues

    def _handle_connection_success(self):
        """Handle successful connection - reset failure counter."""
        if self._consecutive_failures > 0:
            _LOGGER.info(
                "Device %s recovered after %d failures",
                self._name, self._consecutive_failures
            )
        self._consecutive_failures = 0
        self._available = True

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get updated status from API."""
        # Skip update if initialization failed and not enough time has passed
        if self._initialization_failed:
            _LOGGER.debug("Skipping update for %s - initialization failed", self._name)
            return
        
        if not self.access_token or not self.device_id:
            _LOGGER.debug("Cannot update %s: Missing access token or device ID", self._name)
            self._available = False
            return
        
        try:
            status = self._get_command("diagnosis")
            new_state = _get_gate_status(status)
            
            if new_state is not None:
                self._state = new_state
                _LOGGER.debug("Updated state for %s: %s", self._name, self._state)
                self._handle_connection_success()
            else:
                _LOGGER.warning("Could not determine state for %s from status: %s", self._name, status)
                self._handle_connection_failure()
                
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.warning("Unable to connect to server for %s: %s (keeping last state)", self._name, ex)
            self._handle_connection_failure()
        except requests.exceptions.ReadTimeout as ex:
            _LOGGER.warning("Timeout connecting to server for %s: %s (keeping last state)", self._name, ex)
            self._handle_connection_failure()
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code >= 500:
                _LOGGER.warning(
                    "BFT server error for %s (HTTP %d): %s (keeping last state)",
                    self._name, ex.response.status_code, ex
                )
            else:
                _LOGGER.error(
                    "BFT client error for %s (HTTP %d): %s",
                    self._name, ex.response.status_code, ex
                )
            self._handle_connection_failure()
        except (KeyError, ValueError, TypeError) as ex:
            _LOGGER.warning(
                "BFT device %s returned invalid data: %s (keeping last state)", 
                self._name, ex
            )
            self._handle_connection_failure()

        # Stop watcher if not moving
        if self._state not in [STATE_MOVING] and self._unsub_listener_cover is not None:
            self._unsub_listener_cover()
            self._unsub_listener_cover = None

    def _get_command(self, func):
        """Get latest status or execute command."""
        if not self.access_token:
            _LOGGER.error("Cannot execute command %s: No access token available", func)
            raise ValueError("No access token available")
        
        api_call_headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.dispatcher_api_url}/{self.device_id}/execute/{func}"
        
        _LOGGER.debug("API call to %s: %s", self._name, url)
        
        for attempt in range(self._retry_count):
            try:
                ret = requests.get(url, timeout=self._timeout, headers=api_call_headers)
                ret.raise_for_status()
                return ret.json()
            except requests.exceptions.Timeout:
                if attempt < self._retry_count - 1:
                    _LOGGER.debug(
                        "Timeout on command %s for %s (attempt %d/%d, timeout=%ds), retrying...",
                        func, self._name, attempt + 1, self._retry_count, self._timeout
                    )
                    continue
                else:
                    _LOGGER.error(
                        "Failed to execute command %s for %s: Timeout after %d attempts",
                        func, self._name, self._retry_count
                    )
                    raise requests.exceptions.ReadTimeout(
                        f"Timeout after {self._retry_count} attempts"
                    )
            except requests.exceptions.HTTPError as ex:
                # For diagnosis calls with 500 errors, retry (server issues are often temporary)
                # For action commands or client errors (4xx), fail immediately
                if func == "diagnosis" and ex.response.status_code >= 500:
                    if attempt < self._retry_count - 1:
                        _LOGGER.debug(
                            "BFT server error on diagnosis for %s (HTTP %d, attempt %d/%d), retrying...",
                            self._name, ex.response.status_code, attempt + 1, self._retry_count
                        )
                        continue
                    else:
                        _LOGGER.warning(
                            "BFT server error on diagnosis for %s (HTTP %d) after %d attempts, returning empty status",
                            self._name, ex.response.status_code, self._retry_count
                        )
                        # Return empty dict instead of raising - let update() handle it gracefully
                        return {}
                else:
                    # For critical commands (open/close/stop) or client errors, don't retry
                    _LOGGER.error("Failed to execute command %s for %s: %s", func, self._name, ex)
                    raise
            except requests.exceptions.SSLError as ex:
                # SSL errors (connection drops, handshake failures) are common with BFT API
                if attempt < self._retry_count - 1:
                    if func == "diagnosis":
                        _LOGGER.debug(
                            "SSL error on diagnosis for %s (attempt %d/%d): %s, retrying in 1s...",
                            self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    else:
                        _LOGGER.warning(
                            "SSL error on command %s for %s (attempt %d/%d): %s, retrying in 1s...",
                            func, self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    time.sleep(1)  # Brief delay before retry to let connection reset
                    continue
                else:
                    # After all retries, log appropriately based on command type
                    if func == "diagnosis":
                        _LOGGER.warning(
                            "SSL error on diagnosis for %s after %d attempts, returning empty status",
                            self._name, self._retry_count
                        )
                        return {}
                    else:
                        _LOGGER.error(
                            "Failed to execute command %s for %s: SSL error after %d attempts",
                            func, self._name, self._retry_count
                        )
                    raise
            except requests.exceptions.ConnectionError as ex:
                # Connection errors (DNS, network unreachable, connection refused)
                if attempt < self._retry_count - 1:
                    if func == "diagnosis":
                        _LOGGER.debug(
                            "Connection error on diagnosis for %s (attempt %d/%d): %s, retrying in 1s...",
                            self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    else:
                        _LOGGER.warning(
                            "Connection error on command %s for %s (attempt %d/%d): %s, retrying in 1s...",
                            func, self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    if func == "diagnosis":
                        _LOGGER.warning(
                            "Connection error on diagnosis for %s after %d attempts, returning empty status",
                            self._name, self._retry_count
                        )
                        return {}
                    else:
                        _LOGGER.error(
                            "Failed to execute command %s for %s: Connection error after %d attempts",
                            func, self._name, self._retry_count
                        )
                    raise
            except requests.exceptions.RequestException as ex:
                # Other request errors
                if attempt < self._retry_count - 1:
                    if func == "diagnosis":
                        _LOGGER.debug(
                            "Request error on diagnosis for %s (attempt %d/%d): %s, retrying...",
                            self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    else:
                        _LOGGER.warning(
                            "Request error on command %s for %s (attempt %d/%d): %s, retrying...",
                            func, self._name, attempt + 1, self._retry_count, str(ex)[:100]
                        )
                    continue
                else:
                    if func == "diagnosis":
                        _LOGGER.warning(
                            "Request error on diagnosis for %s after %d attempts, returning empty status",
                            self._name, self._retry_count
                        )
                        return {}
                    else:
                        _LOGGER.error(
                            "Failed to execute command %s for %s after %d attempts: %s",
                            func, self._name, self._retry_count, ex
                        )
                    raise
            except ValueError as ex:
                _LOGGER.error("Invalid JSON response for command %s on %s: %s", func, self._name, ex)
                raise
        
        # Should not reach here, but just in case
        raise requests.exceptions.RequestException(f"Failed to execute {func} after {self._retry_count} attempts")

