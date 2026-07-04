# HA-433MHz Weather Station

A [HACS](https://hacs.xyz/) custom integration for Home Assistant that receives
pre-decoded 433 MHz weather-station data from an [ESPHome](https://esphome.io/)
device running the **RTL_433** decoder component.

---

## How it works

```
433 MHz sensor → ESP32 (CC1101 + RTL_433 ESPHome component)
               → fires  esphome.rf_message_received  HA event
               → this integration auto-discovers each sensor
               → creates sensor entities per (model, id) pair
```

The RTL_433 component on the ESP32 handles all RF decoding and fires a standard
Home Assistant event for every received message.  This integration listens for
those events, detects new sensors automatically, and asks you to confirm adding
each one.

---

## Features

- **Zero-configuration discovery** – new sensors appear in the HA notification
  area as soon as the ESPHome device receives their first transmission.
- One **device** per unique sensor (model + hardware ID).
- Entities created per sensor depend on what the sensor actually reports:
  - Temperature (°C or °F)
  - Humidity (%)
  - Battery status (OK / Low)
  - Rain total (mm) and rain rate (mm/h)
  - Wind speed, wind gust (m/s) and wind direction (°)
  - Atmospheric pressure (hPa)
  - UV index, illuminance (lx)
- Supports **any** model that RTL_433 can decode (200+ protocols).

---

## Requirements

| Component | Details |
|---|---|
| Home Assistant | 2023.6 or newer |
| HACS | Any recent version |
| ESPHome device | ESP32 with CC1101 and the `rtl433` external component |

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/zackcornelius/HA-433Mhz-weather-station` with
   category **Integration**
3. Search for *433MHz Weather Station* and install it
4. Restart Home Assistant

### Manual

Copy `custom_components/433mhz_weather_station/` into your Home Assistant
`config/custom_components/` folder, then restart.

---

## ESPHome Configuration

Flash your ESP32 with a configuration that includes the `rtl433` external
component.  A minimal example is provided in
[`esphome/weather_station.yaml`](esphome/weather_station.yaml).

```yaml
external_components:
  - source: github://NorthernMan54/esphome-rtl_433

rtl_433:
  frequency: 433920000

cc1101:
  # CC1101 wired via SPI – adjust pins to match your board
  mosi_pin: GPIO23
  miso_pin: GPIO19
  sck_pin:  GPIO18
  cs_pin:   GPIO5
  gdo0_pin: GPIO21
  gdo2_pin: GPIO22
```

The component automatically fires `esphome.rf_message_received` HA events
containing a JSON-encoded `message` field – no extra MQTT or lambda code needed.

> **CC1101 tip:** if you see only noise, check that the `gdo0`/`gdo2` pins match
> your physical wiring.  See the ESPHome component docs for power and SPI
> wiring details.

---

## Home Assistant Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for *433MHz Weather Station* and click it
3. Click **Submit** on the activation screen – the listener is now running

From this point on, every new 433 MHz sensor that your ESPHome device receives
will show up as a **discovered device** notification in Home Assistant.  Click
the notification, give the device a name, and its sensor entities are created
automatically.

---

## Sensor Entities

Entities are created only for the fields actually present in the sensor's first
received message, so a temperature/humidity-only sensor won't show wind or rain
entities.

| RTL_433 field | Entity | Unit |
|---|---|---|
| `temperature_C` / `temperature_F` | Temperature | °C / °F |
| `humidity` | Humidity | % |
| `battery_ok` | Battery | OK / Low |
| `rain_mm` | Rain Total | mm |
| `rain_rate_mm_h` | Rain Rate | mm/h |
| `wind_avg_m_s` | Wind Speed | m/s |
| `wind_max_m_s` | Wind Gust | m/s |
| `wind_dir_deg` | Wind Direction | ° |
| `pressure_hPa` | Pressure | hPa |
| `uv` | UV Index | – |
| `lux` / `light_lux` | Illuminance | lx |

Any field not in the table above but present in the message is still exposed as
a generic sensor with a title-cased name.

---

## Supported Models

Any model supported by RTL_433 will work.  Common weather stations include:

- Fine Offset WH2, WH24, WH25, WH40, WH65, WH65B and OEM clones
- Ambient Weather WS-10, WH31E
- Froggit WH2, HP1000 sensors
- Digoo DG-R8H
- Nexus CH-320, Rubicson 49189, Prologue
- Cotech 36-7959 / SwitchDocLabs FT020T
- … and 200+ more

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No devices discovered | ESPHome not firing events | Check ESPHome logs; ensure the `rtl433` component is loaded and the CC1101 is receiving |
| Sensor appears then disappears | Duplicate or noisy RF bursts | Adjust CC1101 antenna or `frequency` setting |
| Wrong values | RTL_433 picked the wrong protocol | Check the `protocol` field in the HA event; override in the ESPHome component config if supported |
| Entities show Unknown after restart | No new RF burst received yet | Values update on the next transmission from the sensor |

---

## Contributing

Pull requests are welcome.  The integration creates sensors dynamically from the
RTL_433 field map in `const.py`.  To support a new field:

1. Add an entry to `RTL433_FIELD_MAP` in `const.py` with the appropriate
   `SensorDeviceClass`, `SensorStateClass`, unit, and optional `value_fn`.

---

## License

MIT