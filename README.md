# Fallback Entity

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom integration that creates a virtual **switch** or **light** entity with automatic fallback logic. When the primary entity becomes unavailable, it transparently switches to the fallback entity — and switches back as soon as the primary recovers.

Designed for setups that use two integrations for the same physical device (e.g. **LocalTuya** as primary and **Tuya cloud** as fallback).

---

## How it works

| Primary state | Active entity |
|---|---|
| `on` / `off` | Primary |
| `unavailable` / `unknown` | Fallback |

The virtual entity is itself marked **unavailable** only if **both** primary and fallback are unavailable at the same time.

An `active_entity` attribute is exposed so you can see in the UI which source is currently being used.

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ menu → **Custom repositories**
2. Add the URL of this repository and select category **Integration**
3. Install **Fallback Entity** and restart Home Assistant

### Manual

Copy the `custom_components/fallback_entity` folder into your `<config>/custom_components/` directory and restart Home Assistant.

---

## Configuration

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Fallback Entity**
3. Select the entity type (`switch` or `light`)
4. Enter a name and pick the primary and fallback entities
5. Repeat for each device you want to protect with redundancy

---

## Supported entity types

| Type | Attributes proxied |
|---|---|
| `switch` | `on`/`off` |
| `light` | `on`/`off`, `brightness`, `color_mode`, `supported_color_modes` |

---

## License

MIT
