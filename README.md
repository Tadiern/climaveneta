# Climaveneta iMXW / iLife2 — Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub release](https://img.shields.io/github/v/release/Tadiern/climaveneta)](https://github.com/Tadiern/climaveneta/releases/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Tadiern/climaveneta/actions/workflows/ci.yml/badge.svg)](https://github.com/Tadiern/climaveneta/actions/workflows/ci.yml)

Custom integration for [Home Assistant](https://www.home-assistant.io/) to control **Mitsubishi-Climaveneta** fancoils via Modbus RTU (RS-485).

## Supported models

| Brand | Model | Protocol | Config type | Status |
|-------|-------|----------|-------------|--------|
| [Climaveneta](https://www.climaveneta.com/) | **i-MXW** | Modbus RTU | i-MXW | Tested ✓ |
| [Climaveneta](https://www.climaveneta.com/) | **iLife2** | Modbus RTU | iLife2 | Tested ✓ |
| [Sabiana](https://www.sabiana.it/) | **Carisma Fly** | Modbus RTU | i-MXW | Not tested — likely compatible |
| [Innova](https://www.innovaenergie.com/) | **AirLeaf** | Modbus RTU | iLife2 | Not tested — likely compatible |

### OEM compatibility note

Sabiana and Innova appear to use the same control boards and Modbus protocol as Climaveneta (OEM relationship). The Sabiana **Carisma Fly** series shares the same i-MXW controller board, while the Innova **AirLeaf** series shares the same iLife2 controller board.

This integration has only been tested on Climaveneta hardware. However, since the electronics and protocol are identical, it should work on Sabiana and Innova units as well. If you have one of these devices and can confirm compatibility, please [open an issue](https://github.com/Tadiern/climaveneta/issues) to let us know!

## Hardware requirements

- RS-485 adapter (e.g. USB-to-RS485 or Raspberry Pi HAT)
- Wired connection to the fancoil Modbus bus
- Each fancoil must have a unique Modbus slave ID

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click **Integrations** → **⋮** → **Custom repositories**
3. Add `https://github.com/Tadiern/climaveneta` as **Integration**
4. Search for "Climaveneta" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/climaveneta` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Climaveneta**
3. Enter:
   - **Serial device path** (e.g. `/dev/ttyAMA0`)
   - **Modbus slave ID** (1–255)
   - **Fancoil model** (i-MXW or iLife2)
   - **Name** for the device

## Exposed entities

### Climate

- HVAC modes: Off, Heat, Cool, Heat/Cool (iLife2), Fan Only (i-MXW)
- Fan modes: Auto, Low, Medium, High
- Preset modes (i-MXW only): None, Eco, Away

### Sensors

| Sensor | i-MXW | iLife2 | Unit |
|--------|:-----:|:------:|------|
| Actual Temperature | ✓ | ✓ | °C |
| Water Temperature | ✓ | ✓ | °C |
| Real Setpoint | | ✓ | °C |
| Motor Speed Set | | ✓ | — |
| Min/Max Fan Voltage (winter/summer) | ✓ | | V |
| Min/Max Water Temperature | ✓ | ✓ | °C |
| Setpoint Hysteresis | ✓ | | °C |
| Dead Zone Center/Range | ✓ | | °C |
| T1 Compensation Delta | ✓ | | °C |
| T1 Compensation Base (summer/winter) | ✓ | | °C |
| Anti-stratification Wait Time | ✓ | | min |
| Anti-stratification Time (summer/winter) | ✓ | | sec |
| Modbus Address | | ✓ | — |

### Binary sensors

| Sensor | i-MXW | iLife2 | Description |
|--------|:-----:|:------:|-------------|
| Pump Relay | ✓ | ✓ | Water pump request |
| Alarm flags | | ✓ | Communication, Air, H2, H4, Filter, Motor, etc. |

### Services

| Service | Description |
|---------|-------------|
| `climaveneta.set_actual_temperature` | Send an external temperature reading to the i-MXW (for external thermostat compensation) |

## Development

```bash
python -m pip install -r requirements_dev.txt
python -m pytest -q
python -m ruff check .
```

## License

[MIT](LICENSE)

