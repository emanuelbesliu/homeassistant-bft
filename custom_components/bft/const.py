"""Constants for the BFT integration."""

DOMAIN = "bft"

# API endpoints
PARTICLE_URL = "https://ucontrol-api.bft-automation.com"
DISPATCHER_API_URL = "https://ucontrol-dispatcher.bft-automation.com/automations"

# OAuth client credentials (hardcoded by BFT's API design)
OAUTH_CLIENT_ID = "particle"
OAUTH_CLIENT_SECRET = "particle"

# Configuration keys
CONF_DEVICE_NAME = "device_name"
CONF_TIMEOUT = "timeout"
CONF_RETRY_COUNT = "retry_count"

# Defaults
DEFAULT_NAME = "BFT"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY_COUNT = 3
DEFAULT_SCAN_INTERVAL = 30  # seconds between coordinator polls

# State constants
STATE_MOVING = "moving"
STATE_STOPPED = "stopped"

# Failure tracking
MAX_CONSECUTIVE_FAILURES = 10  # Failures before marking entity unavailable
FAILURE_BACKOFF_BASE = 2  # Exponential backoff base (seconds)
FAILURE_BACKOFF_MAX = 300  # Max backoff cap: 5 minutes
