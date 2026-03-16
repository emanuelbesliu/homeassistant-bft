{% if installed %}
## BFT Gate Automation Installed

Version: **{{ version_installed }}**
{% if version_available %}
### Update Available: {{ version_available }}

[View Release Notes](https://github.com/emanuelbesliu/homeassistant-bft/releases/tag/v{{ version_available }})
{% endif %}
{% endif %}

## BFT Gate Automation Integration

Control your BFT garage doors and gates directly from Home Assistant via the BFT uControl Cloud API.

### Features

- **Multi-gate support** -- automatically discovers and adds all gates in your BFT account
- Full cover control (open, close, stop)
- UI-based setup -- no YAML editing required
- Real-time gate status monitoring (open, closed, moving, stopped)
- Cloud-resilient: preserves last known state during outages
- Exponential backoff on cloud failures
- Automatic recovery when connectivity returns
- Device registry integration
- Diagnostics support for troubleshooting
- Re-authentication flow for expired credentials

### Quick Setup

1. **Install via HACS** (you're done with this step!)
2. Go to **Settings > Devices & Services**
3. Click **Add Integration** and search for **BFT Gate Automation**
4. Enter your BFT uControl cloud credentials
5. All gates in your account are automatically discovered and added

### Upgrading from v1.x

Version 2.0 replaces `configuration.yaml` setup with a UI-based config flow:

1. Remove the old `cover:` platform entry from `configuration.yaml`
2. Restart Home Assistant
3. Add the integration via **Settings > Devices & Services > Add Integration**

### Upgrading from v2.0.x

Version 2.1 auto-discovers all gates per account (no manual device selection):

1. Remove existing BFT integration entries
2. Restart Home Assistant
3. Re-add the integration -- all gates appear automatically

### Cloud Resilience

The BFT cloud API can be unreliable. This integration handles that:

- Entity stays available with last-known state during transient outages (check the `stale_data` attribute)
- Only marks unavailable after 10 consecutive failures
- Exponential backoff avoids hammering a down API
- Automatic recovery when cloud returns -- no reload needed

### Troubleshooting

**Setup fails:**
- Verify credentials work in the BFT mobile app
- Check internet connectivity to BFT cloud
- Try increasing the timeout during setup

**Entity shows "Unavailable":**
- Check logs: **Settings > System > Logs** (filter for "bft")
- Download diagnostics from the device page
- The integration will auto-recover when the cloud comes back

### Support

- [Documentation](https://github.com/emanuelbesliu/homeassistant-bft)
- [Report Issues](https://github.com/emanuelbesliu/homeassistant-bft/issues)
- [Changelog](https://github.com/emanuelbesliu/homeassistant-bft/blob/main/CHANGELOG.md)

### Recent Updates

See [Releases](https://github.com/emanuelbesliu/homeassistant-bft/releases) for full changelog.
