# Changelog

All notable changes to the BFT Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.2](https://github.com/emanuelbesliu/homeassistant-bft/compare/v2.1.1...v2.1.2) (2026-03-19)


### Bug Fixes

* remove blocking SSL call, add 401 re-auth on diagnosis, reduce log noise ([746d619](https://github.com/emanuelbesliu/homeassistant-bft/commit/746d6193b9b9c4223d8170ba2b8eb0fe76d9e386))

## [2.1.1](https://github.com/emanuelbesliu/homeassistant-bft/compare/v2.1.0...v2.1.1) (2026-03-16)


### Bug Fixes

* add async_migrate_entry to handle v1 -&gt; v2 config entry migration ([71a9ed7](https://github.com/emanuelbesliu/homeassistant-bft/commit/71a9ed7f3e9717473f2664b345b3c928f3a608c7))
* bump version to 2.1.1 for migration handler release ([d318807](https://github.com/emanuelbesliu/homeassistant-bft/commit/d318807b36828589c24ed9c006a720f561bca1b4))

## [2.1.0](https://github.com/emanuelbesliu/homeassistant-bft/compare/v2.0.1...v2.1.0) (2026-03-16)


### Features

* support multiple gates per BFT account with auto-discovery ([5c2f188](https://github.com/emanuelbesliu/homeassistant-bft/commit/5c2f1884dabab73d123482f985e989186e799eab))

## [2.0.1](https://github.com/emanuelbesliu/homeassistant-bft/compare/v2.0.0...v2.0.1) (2026-03-15)


### Bug Fixes

* bump version to 2.0.1 for HACS default submission ([659a541](https://github.com/emanuelbesliu/homeassistant-bft/commit/659a541cda745613aeddbbbda3c84ad47bbbcdac))

## [2.0.0](https://github.com/emanuelbesliu/homeassistant-bft/compare/v1.0.7...v2.0.0) (2026-03-15)


### ⚠ BREAKING CHANGES

* Remove configuration.yaml setup in favor of UI-based config flow.

### Features

* transform to standalone integration with config flow and cloud resilience ([a6d5f6a](https://github.com/emanuelbesliu/homeassistant-bft/commit/a6d5f6ade00fd624dbf949ab096e5be76e252c67))


### Documentation

* update README and HACS info for v2.0 config flow setup ([fa71ad3](https://github.com/emanuelbesliu/homeassistant-bft/commit/fa71ad329a1668a1aaa8dc2ee51e2370a0eb7dfa))

## [1.0.5] - 2026-03-04

### Changed
- Bump requests from 2.31.0 to 2.32.0 (#7)
- Dependency updates from Dependabot

## [1.0.4] - 2026-03-04

### Changed
- ci(deps): bump actions/checkout from 4 to 6 (#1)
- Dependency updates from Dependabot

## [1.0.3] - 2026-02-25

### Fixed
- **SSL certificate verification bypass**: Disabled SSL verification for BFT API to fix certificate validation errors
- Resolves "SSL: CERTIFICATE_VERIFY_FAILED" errors preventing authentication
- Suppressed urllib3 InsecureRequestWarning to reduce log noise

### Changed
- All API requests now bypass SSL verification (`verify=False`)
- This is safe as we only connect to official BFT servers at `ucontrol-api.bft-automation.com` and `ucontrol-dispatcher.bft-automation.com`

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
