# BFT Gate Automation - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Custom Home Assistant integration for BFT gate/cover automation systems via BFT uControl Cloud API.

## Features

- 🚪 Control BFT gates (open, close, stop)
- 📊 Real-time status monitoring
- 🔄 Automatic state detection (open, closed, moving, stopped)
- 🛡️ Robust error handling with retry logic
- 🌐 SSL/Connection failure resilience
- ⚡ Async initialization (non-blocking startup)

## Installation

### HACS (Recommended - Coming Soon)

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

Add to your `configuration.yaml`:

```yaml
cover:
  - platform: bft
    covers:
      driveway_gate:                    # Unique identifier
        device: YOUR_DEVICE_NAME        # BFT device name from app
        username: !secret bft_username  # BFT account email
        password: !secret bft_password  # BFT account password
        name: Driveway Gate            # Friendly name (optional)
        timeout: 20                    # Request timeout (optional, default: 10)
        retry_count: 10                # Retries (optional, default: 3)
        skip_initial_update: true      # Skip initial check (optional, default: false)
```

Add to your `secrets.yaml`:

```yaml
bft_username: your@email.com
bft_password: your_password
```

### Configuration Options

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `device` | Yes | - | Device name as shown in BFT app |
| `username` | Yes | - | BFT account email |
| `password` | Yes | - | BFT account password |
| `name` | No | BFT | Friendly name for the gate |
| `timeout` | No | 10 | API request timeout (seconds) |
| `retry_count` | No | 3 | Number of retry attempts |
| `skip_initial_update` | No | false | Skip initial state fetch |

### Multiple Gates

```yaml
cover:
  - platform: bft
    covers:
      front_gate:
        device: FRONT_GATE
        username: !secret bft_username
        password: !secret bft_password
        name: Front Gate
      
      back_gate:
        device: BACK_GATE
        username: !secret bft_username
        password: !secret bft_password
        name: Back Gate
```

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

## Troubleshooting

### Integration Not Loading

1. Check logs: `Settings → System → Logs` (search for "bft")
2. Verify file structure:
   ```bash
   ls -la /config/custom_components/bft/
   # Should show: __init__.py, cover.py, manifest.json
   ```
3. Restart Home Assistant

### Gate Not Responding

1. **Check credentials:** Verify in BFT mobile app
2. **Check device name:** Must match exactly (case-sensitive)
3. **Network issues:** Increase `timeout` to 20-30 seconds
4. **SSL errors:** Increase `retry_count` to 5-10

### Entity Shows "Unavailable"

- Integration marks entity unavailable after 5 consecutive failures
- Check logs for specific errors
- Verify internet connection to BFT cloud API
- Try reloading integration or restarting HA

### Enable Debug Logging

```yaml
logger:
  default: info
  logs:
    custom_components.bft: debug
```

## Known Issues

1. **BFT API Reliability:** The BFT cloud API can experience SSL errors and timeouts. The integration includes robust retry logic.
2. **Initial Status Delay:** First update may take 10-30 seconds after restart.
3. **State Updates:** Polling occurs every 5 seconds minimum (throttled).

## Development

### Testing Authentication

Run the included test script:

```bash
cd custom_components/bft
python3 test_auth.py
```

### File Structure

```
custom_components/bft/
├── __init__.py       # Component setup
├── cover.py          # Main platform implementation
├── manifest.json     # Integration metadata
└── test_auth.py      # Authentication test script
```

## Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/emanuelbesliu/homeassistant-bft/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/emanuelbesliu/homeassistant-bft/discussions)

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

## Disclaimer

This integration is not affiliated with, endorsed by, or supported by BFT. Use at your own risk.
