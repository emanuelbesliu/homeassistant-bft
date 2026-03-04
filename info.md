{% if installed %}
## 🎉 BFT Gate Automation Installed

Version: **{{ version_installed }}**
{% if version_available %}
### 🆕 Update Available: {{ version_available }}

[View Release Notes](https://github.com/emanuelbesliu/homeassistant-bft/releases/tag/v{{ version_available }})
{% endif %}
{% endif %}

## BFT Gate Automation Integration

Control your BFT garage doors and gates directly from Home Assistant via the BFT uControl Cloud API.

### Features

- ✅ **Full Cover Control** - Open, close, and stop operations
- ✅ **Real-time Status** - Monitor gate state (open, closed, moving, stopped)
- ✅ **Auto-recovery** - Handles temporary API failures gracefully
- ✅ **Configurable Timeouts** - Adjust retry logic for reliability
- ✅ **Async Architecture** - Non-blocking initialization for fast HA startup

### Quick Setup

1. **Install via HACS** (you're done with this step!)
2. **Add to configuration.yaml:**

```yaml
cover:
  - platform: bft
    covers:
      your_gate:
        device: YOUR_DEVICE_NAME
        username: your_email@example.com
        password: your_password
        name: garage_door
        skip_initial_update: true
        timeout: 30
        retry_count: 10
```

3. **Restart Home Assistant**
4. **Check entity:** `cover.garage_door` should appear

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `device` | Yes | - | Device name from BFT app (e.g., "GARAJ") |
| `username` | Yes | - | BFT account email |
| `password` | Yes | - | BFT account password |
| `name` | No | BFT | Friendly name for the cover entity |
| `skip_initial_update` | No | false | Skip update during startup for faster boot |
| `timeout` | No | 10 | Request timeout in seconds (recommend: 30) |
| `retry_count` | No | 3 | Number of retries on failure (recommend: 10) |

### Troubleshooting

**Entity shows "Unavailable":**
- Check credentials are correct
- Verify device name matches BFT app exactly
- Increase timeout to 30 seconds
- Check logs: `tail -f /config/home-assistant*.log | grep bft`

**SSL Certificate Errors:**
- Should be fixed in v1.0.3+ (SSL verification bypassed)
- Update to latest version if seeing SSL errors

**Slow startup:**
- Set `skip_initial_update: true` in configuration

### Support

- 📖 [Documentation](https://github.com/emanuelbesliu/homeassistant-bft)
- 🐛 [Report Issues](https://github.com/emanuelbesliu/homeassistant-bft/issues)
- 📝 [Changelog](https://github.com/emanuelbesliu/homeassistant-bft/blob/main/CHANGELOG.md)

### Recent Updates

See [Releases](https://github.com/emanuelbesliu/homeassistant-bft/releases) for full changelog.
