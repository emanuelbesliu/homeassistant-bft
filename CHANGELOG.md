# Changelog

All notable changes to the BFT Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-02-25

### Added
- **Unique ID support**: Entity now has a unique identifier, enabling UI-based configuration and customization
- Unique ID is based on device UUID when available, or device name as fallback
- Enables renaming entities, changing icons, and other UI customizations

### Fixed
- Resolved "entity does not have a unique ID" warning in Home Assistant UI
- Entity settings can now be managed from the UI

## [1.0.1] - 2026-02-25

### Fixed
- **Resilient error handling for diagnosis endpoint failures**: Integration now gracefully handles HTTP 500, SSL, connection, and request errors from BFT API's diagnosis endpoint
- When diagnosis fails, integration returns empty status instead of crashing, allowing it to load and mark entity as "unavailable" temporarily
- Integration automatically recovers when API becomes available again
- Prevents setup failures due to temporary BFT cloud service issues

### Changed
- Improved logging for diagnosis failures - now uses WARNING level instead of ERROR for recoverable issues
- Better error messages that clarify the integration will retry automatically

## [1.0.0] - 2026-02-25

### Added
- Initial release of BFT Home Assistant Integration
- Support for BFT gate/cover control via uControl Cloud API
- OAuth 2.0 authentication with BFT cloud services
- Cover entity with open, close, and stop operations
- Real-time status monitoring (open, closed, moving, stopped)
- Configurable timeout and retry settings
- `skip_initial_update` option for faster Home Assistant startup
- HACS compatibility
- Comprehensive documentation and installation instructions

### Features
- Cloud polling integration with BFT API
- Automatic token management
- Robust error handling with exponential retry logic
- Connection failure tracking with automatic recovery
- Device discovery by name
- State throttling (5-second minimum between updates)
