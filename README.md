# HA-433MHz Weather Station

A [HACS](https://hacs.xyz/) custom integration for Home Assistant that receives and decodes 433 MHz weather-station data captured by an [ESPHome](https://esphome.io/) device with a CC1101 (or similar OOK) radio and the `remote_receiver` component.

---

## Features

- Decodes raw RF pulse data published to an MQTT topic by ESPHome
- Supports multiple protocols:
  - **Auto-detect** – tries Fine Offset WH65B-compatible, then Nexus/Rubicson, then generic
  - **Fine Offset WH65B-compatible** – WH2, WH24, WH40, WH65 and OEM clones
  - **Nexus / Rubicson / Prologue** – common budget weather sensors
  - **Generic PWM / PDM** – outputs raw bytes for protocol debugging
- Creates Home Assistant sensor entities:
  - Temperature (°C)
  - Humidity (%)
  - Battery status
  - Channel
  - Device ID
  - Raw data (disabled by default, useful for debugging)
- Config flow UI – no YAML editing required

---

## Requirements

| Component | Details |
|---|---|
| Home Assistant | 2023.6 or newer |
| HACS | Any recent version |
| MQTT integration | Must be configured in HA before installing this integration |
| ESPHome device | ESP32 / ESP8266 with a CC1101 (or bare wire antenna) connected via `remote_receiver` |

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/zackcornelius/HA-433Mhz-weather-station` with category **Integration**
3. Search for *433MHz Weather Station* and install it
4. Restart Home Assistant

### Manual

Copy the `custom_components/433mhz_weather_station/` directory into your Home Assistant `config/custom_components/` folder, then restart.

---

## ESPHome Configuration

Flash your ESP32/ESP8266 with the example configuration in [`esphome/weather_station.yaml`](esphome/weather_station.yaml).

Key section – publishes raw pulse data to MQTT on every received RF burst:

```yaml
remote_receiver:
  pin: GPIO14       # adjust to your wiring
  dump: raw
  on_raw:
    then:
      - lambda: |-
          std::string payload;
          payload.reserve(x.size() * 7);
          for (size_t i = 0; i < x.size(); i++) {
            if (i > 0) payload += ',';
            payload += std::to_string(x[i]);
          }
          id(mqtt_client).publish("esphome/weather_station/raw", payload);
```

> **CC1101 wiring tip:** Connect the CC1101's GDO2 pin to the ESP GPIO configured in `remote_receiver`. Set `inverted: true` if the signal appears inverted (all pulses show as noise).

---

## Home Assistant Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for *433MHz Weather Station*
3. Enter:
   - **MQTT Topic** – the topic your ESPHome device publishes to (default: `esphome/weather_station/raw`)
   - **Protocol** – choose *Auto-detect* unless you know your station's protocol

The integration will create a device with sensor entities for Temperature, Humidity, Battery, Channel, Device ID, and Raw Data.

---

## Identifying Your Protocol

If *Auto-detect* does not produce correct values:

1. Enable the **Raw Data** sensor in HA (disabled by default)
2. Watch the ESPHome logs for received raw pulses
3. Use the table below to identify your protocol:

| Protocol | Short pulse | Long pulse | Total bits | Notes |
|---|---|---|---|---|
| Fine Offset WH65B | ~500 µs | ~1000 µs | 40 | Most cheap OEM stations |
| Nexus / Rubicson | ~500 µs | ~1000 µs | 36 | PDM encoded |
| Acurite 609 | ~400 µs | ~800 µs | 56 | Different preamble |

4. If none match, open an issue and paste your raw pulse data – new protocols can be added to `decoder.py`.

---

## Supported Weather Station Models

Because many stations share the same OEM PCB, the following (and their clones/rebrands) are expected to work:

- Fine Offset WH2, WH24, WH25, WH40, WH65, WH65B
- Ambient Weather WS-10, WH31E
- Froggit WH2, HP1000 sensors
- Digoo DG-R8H
- Nexus CH-320, Rubicson 49189, Prologue

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No data received | ESPHome not publishing | Check MQTT logs; ensure `mqtt_client` is defined in ESPHome YAML |
| Sensors always `Unknown` | Protocol mismatch | Enable Raw Data sensor; try a different protocol |
| Temperature/humidity wildly wrong | Protocol mismatch | Try `Fine Offset` or `Nexus` explicitly |
| Signal very noisy | Antenna or pin polarity | Add `inverted: true` to `remote_receiver.pin`; improve antenna |

---

## Contributing

Pull requests are welcome. To add a new protocol:

1. Add a new constant to `const.py`
2. Implement `_decode_yourprotocol(self, bits)` in `decoder.py`
3. Register it in `_decode_with()` and add it to `PROTOCOLS` in `const.py`

---

## License

MIT