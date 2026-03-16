# BFT Gate Automation - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/v/release/emanuelbesliu/homeassistant-bft)](https://github.com/emanuelbesliu/homeassistant-bft/releases/latest)
[![License](https://img.shields.io/github/license/emanuelbesliu/homeassistant-bft)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/emanuelbesliu)

Custom Home Assistant integration for BFT gate/cover automation systems via the BFT uControl Cloud API.

## Features

- **Multi-gate support** -- automatically discovers and adds all gates in your BFT account
- Control BFT gates (open, close, stop) from Home Assistant
- UI-based setup via config flow -- no YAML editing required
- Real-time status monitoring (open, closed, moving, stopped)
- Cloud-resilient polling with last-known-state preservation during outages
- Exponential backoff on cloud failures to avoid hammering a down API
- Automatic recovery when cloud connectivity returns
- Fast polling (5s) while the gate is moving, normal polling (30s) at rest
- Device registry integration with proper device info per gate
- Re-authentication flow when credentials expire
- Diagnostics support for troubleshooting

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3-dot menu and select "Custom repositories"
4. Add `https://github.com/emanuelbesliu/homeassistant-bft` as an Integration
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/bft` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/bft/
   ```
3. Restart Home Assistant

## Configuration

### Setup via UI

1. Go to **Settings > Devices & Services**
2. Click **Add Integration**
3. Search for **BFT Gate Automation**
4. Enter your BFT uControl cloud credentials (email and password)

All gates in your BFT account are automatically discovered and added as separate cover entities. No manual device selection is needed.

### Advanced Options

During setup you can configure:

| Option | Default | Description |
|--------|---------|-------------|
| Timeout | 10s | API request timeout per attempt |
| Retry count | 3 | Number of retry attempts per API call |

### Upgrading from v1.x (YAML configuration)

Version 2.0 replaces `configuration.yaml` setup with UI-based config flow. To upgrade:

1. Remove the old `cover:` platform entry from your `configuration.yaml`
2. Restart Home Assistant
3. Add the integration via **Settings > Devices & Services > Add Integration**
4. The entity ID will be preserved if you use the same name

### Upgrading from v2.0.x (single-device per entry)

Version 2.1 changes the config entry to represent an entire BFT account instead of a single device. All gates in the account are now auto-discovered. To upgrade:

1. Remove the existing BFT integration entries from **Settings > Devices & Services**
2. Restart Home Assistant
3. Re-add the integration -- all gates will be discovered automatically

## Usage

### Lovelace UI

The gate appears as a standard Home Assistant cover entity with open/close/stop controls.

### Automations

```yaml
automation:
  - alias: "Open gate when arriving home"
    trigger:
      - platform: zone
        entity_id: person.john
        zone: zone.home
        event: enter
    action:
      - service: cover.open_cover
        target:
          entity_id: cover.driveway_gate
```

### Services

Standard Home Assistant cover services:

- `cover.open_cover` - Open the gate
- `cover.close_cover` - Close the gate
- `cover.stop_cover` - Stop gate movement

### Entity Attributes

| Attribute | Description |
|-----------|-------------|
| `consecutive_failures` | Number of consecutive cloud polling failures |
| `stale_data` | `true` if the displayed state is from the last successful poll (cloud currently unreachable) |
| `device_uuid` | The BFT device UUID |
| `first_engine_pos` / `second_engine_pos` | Engine position percentage (0-100) |
| `first_engine_vel` / `second_engine_vel` | Engine velocity |

## Cloud Resilience

The BFT cloud API can be unreliable. This integration handles that with several strategies:

1. **Last-known-state preservation** - During transient outages the entity stays available showing its last known state. The `stale_data` attribute indicates when data is not fresh.
2. **Grace period** - The entity is only marked unavailable after 10 consecutive polling failures, not on the first error.
3. **Exponential backoff** - When the cloud is down, polling interval increases (2s, 4s, 8s... up to 5 minutes) to avoid unnecessary requests.
4. **Automatic recovery** - When the cloud comes back, normal polling resumes automatically with no reload needed.
5. **Re-authentication** - If your credentials expire or become invalid, Home Assistant prompts you to re-authenticate via the UI.

## Troubleshooting

### Integration Not Loading

1. Check logs: **Settings > System > Logs** (filter for "bft")
2. Verify the file structure:
   ```
   /config/custom_components/bft/
       __init__.py
       bft_api.py
       config_flow.py
       const.py
       coordinator.py
       cover.py
       diagnostics.py
       manifest.json
       strings.json
       translations/en.json
   ```
3. Restart Home Assistant

### Setup Fails with "Cannot Connect"

- Verify your internet connection
- The BFT cloud API may be temporarily down -- try again later
- Increase the timeout value during setup

### Setup Fails with "Invalid Auth"

- Verify your credentials work in the BFT mobile app
- Check for typos in email/password

### Entity Shows "Unavailable"

- This means 10 consecutive polls have failed
- Check **Settings > System > Logs** for specific errors
- Verify your internet connection to the BFT cloud
- The integration will automatically recover when the cloud comes back -- no reload needed
- Download diagnostics: **Settings > Devices & Services > BFT > (device) > Download Diagnostics**

### Enable Debug Logging

```yaml
logger:
  default: info
  logs:
    custom_components.bft: debug
```

## Development

### File Structure

```
custom_components/bft/
    __init__.py       # Integration setup (async_setup_entry / async_unload_entry)
    bft_api.py        # Async API client (aiohttp)
    config_flow.py    # UI-based configuration flow
    const.py          # Shared constants
    coordinator.py    # DataUpdateCoordinator with resilience logic
    cover.py          # Cover entity (CoordinatorEntity)
    diagnostics.py    # Diagnostics data export
    manifest.json     # Integration metadata
    strings.json      # UI strings
    translations/
        en.json       # English translations
    test_auth.py      # Standalone authentication test script
```

### Testing Authentication

```bash
cd custom_components/bft
BFT_USERNAME=your@email.com BFT_PASSWORD=yourpass BFT_DEVICE=DEVICE_NAME python3 test_auth.py
```

## Support

- [GitHub Issues](https://github.com/emanuelbesliu/homeassistant-bft/issues)
- [GitHub Discussions](https://github.com/emanuelbesliu/homeassistant-bft/discussions)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - Copyright (c) 2024 Emanuel Besliu

See [LICENSE](LICENSE) for details.

## Credits

Developed by Emanuel Besliu ([@emanuelbesliu](https://github.com/emanuelbesliu))

## ☕ Support the Developer

If you find this project useful, consider buying me a coffee!

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/emanuelbesliu)

## Disclaimer

This integration is not affiliated with, endorsed by, or supported by BFT. Use at your own risk.
