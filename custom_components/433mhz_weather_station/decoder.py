"""Decoder for 433MHz weather station raw RF pulse data."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .const import PULSE_THRESHOLD_US, PROTOCOL_FINEOFFSET, PROTOCOL_NEXUS, PROTOCOL_PWM_GENERIC, PROTOCOL_PDM_GENERIC, PROTOCOL_AUTO

_LOGGER = logging.getLogger(__name__)


@dataclass
class DecodedData:
    """Holds the decoded weather station data."""

    protocol: str = ""
    device_id: int | None = None
    channel: int | None = None
    temperature_c: float | None = None
    humidity: int | None = None
    battery_ok: bool | None = None
    rain_total_mm: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: int | None = None
    raw_bytes: list[int] = field(default_factory=list)
    raw_bits: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return data as a dictionary."""
        return {
            "protocol": self.protocol,
            "device_id": self.device_id,
            "channel": self.channel,
            "temperature_c": self.temperature_c,
            "humidity": self.humidity,
            "battery_ok": self.battery_ok,
            "rain_total_mm": self.rain_total_mm,
            "wind_speed_ms": self.wind_speed_ms,
            "wind_direction_deg": self.wind_direction_deg,
            "raw_bytes": [f"{b:02X}" for b in self.raw_bytes],
            "raw_bits": self.raw_bits,
            **self.extra,
        }


class RFDecoder:
    """Decodes raw RF pulse data from ESPHome remote_receiver."""

    def __init__(self, protocol: str = PROTOCOL_AUTO, threshold: int = PULSE_THRESHOLD_US) -> None:
        """Initialize the decoder with the selected protocol."""
        self.protocol = protocol
        self.threshold = threshold

    def decode(self, raw: str) -> DecodedData | None:
        """Decode a comma-separated string of raw pulse values."""
        try:
            pulses = [int(v.strip()) for v in raw.split(",") if v.strip()]
        except ValueError:
            _LOGGER.warning("Invalid pulse data: %s", raw[:100])
            return None

        if len(pulses) < 20:
            _LOGGER.debug("Too few pulses to decode (%d)", len(pulses))
            return None

        # Split multiple messages at large inter-message gaps (> 2 ms)
        messages = self._split_messages(pulses)

        for msg in messages:
            result = self._try_decode(msg)
            if result is not None:
                return result

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_messages(self, pulses: list[int]) -> list[list[int]]:
        """Split pulse list at large gaps, returning each sub-message."""
        messages: list[list[int]] = []
        current: list[int] = []
        for p in pulses:
            if abs(p) > 2000:
                if current:
                    messages.append(current)
                current = []
            else:
                current.append(p)
        if current:
            messages.append(current)
        return messages

    def _strip_preamble(self, pulses: list[int]) -> list[int]:
        """Remove leading preamble (consecutive short mark + short space pairs)."""
        i = 0
        while i + 1 < len(pulses):
            mark = pulses[i]
            space = abs(pulses[i + 1])
            if mark > 0 and mark < self.threshold and space < self.threshold:
                i += 2
            else:
                break
        # Also skip a single trailing short mark that forms the sync transition
        if i < len(pulses) and 0 < pulses[i] < self.threshold:
            i += 1
        return pulses[i:]

    def _pwm_bits(self, pulses: list[int]) -> list[int]:
        """Extract bits using Pulse-Width Modulation (mark width = bit value)."""
        bits: list[int] = []
        for p in pulses:
            if p > 0:
                bits.append(1 if p >= self.threshold else 0)
        return bits

    def _pdm_bits(self, pulses: list[int]) -> list[int]:
        """Extract bits using Pulse-Distance Modulation (space width = bit value)."""
        bits: list[int] = []
        i = 0
        while i < len(pulses):
            if pulses[i] > 0 and i + 1 < len(pulses):
                space = abs(pulses[i + 1])
                bits.append(1 if space >= self.threshold else 0)
                i += 2
            else:
                i += 1
        return bits

    @staticmethod
    def _bits_to_bytes(bits: list[int]) -> list[int]:
        """Convert a list of bits (MSB first) to bytes."""
        result: list[int] = []
        for i in range(0, len(bits) - 7, 8):
            byte = 0
            for b in bits[i : i + 8]:
                byte = (byte << 1) | b
            result.append(byte)
        return result

    @staticmethod
    def _crc8(data: list[int]) -> int:
        """Simple XOR checksum."""
        crc = 0
        for b in data:
            crc ^= b
        return crc

    def _try_decode(self, pulses: list[int]) -> DecodedData | None:
        """Try to decode a single message using the configured protocol."""
        data = self._strip_preamble(pulses)
        if not data:
            return None

        pwm_bits = self._pwm_bits(data)
        pdm_bits = self._pdm_bits(data)

        protocol = self.protocol
        if protocol == PROTOCOL_AUTO:
            # Try Fine Offset first (most common), then Nexus, then generic
            for proto in (PROTOCOL_FINEOFFSET, PROTOCOL_NEXUS, PROTOCOL_PWM_GENERIC):
                result = self._decode_with(proto, pwm_bits, pdm_bits)
                if result is not None:
                    return result
            return None

        return self._decode_with(protocol, pwm_bits, pdm_bits)

    def _decode_with(self, protocol: str, pwm_bits: list[int], pdm_bits: list[int]) -> DecodedData | None:
        """Dispatch to the correct protocol decoder."""
        if protocol == PROTOCOL_FINEOFFSET:
            return self._decode_fineoffset(pwm_bits)
        if protocol == PROTOCOL_NEXUS:
            return self._decode_nexus(pdm_bits)
        if protocol == PROTOCOL_PWM_GENERIC:
            return self._decode_generic(pwm_bits, "Generic PWM")
        if protocol == PROTOCOL_PDM_GENERIC:
            return self._decode_generic(pdm_bits, "Generic PDM")
        return None

    # ------------------------------------------------------------------
    # Protocol: Fine Offset WH65B / WH2 / WH40 / WH24 compatible
    # ------------------------------------------------------------------

    def _decode_fineoffset(self, bits: list[int]) -> DecodedData | None:
        """Decode Fine Offset / WH65B-compatible sensors.

        Frame layout (40 bits minimum):
          Bits 0-7:   Device ID high byte
          Bits 8-11:  Device ID low nibble
          Bit 12:     Battery (0=OK, 1=Low)
          Bit 13:     Temperature sign (0=positive, 1=negative)
          Bits 14-23: Temperature raw (×0.1 °C)
          Bits 24-31: Humidity (%)
          Bits 32-39: CRC / checksum
        """
        # Need at least 40 bits; try with a 4-bit offset for the sync nibble
        for bit_offset in (0, 4):
            shifted = bits[bit_offset:]
            if len(shifted) < 40:
                continue
            data = self._bits_to_bytes(shifted)
            if len(data) < 5:
                continue

            device_id = (data[0] << 4) | (data[1] >> 4)
            battery_ok = not bool((data[1] >> 3) & 1)
            sign = (data[1] >> 2) & 1
            temp_raw = ((data[1] & 0x03) << 8) | data[2]
            if sign:
                temp_raw = -temp_raw
            temperature_c = temp_raw * 0.1
            humidity = data[3]

            if not self._fineoffset_sanity(temperature_c, humidity):
                continue

            return DecodedData(
                protocol="Fine Offset WH65B-compatible",
                device_id=device_id,
                battery_ok=battery_ok,
                temperature_c=round(temperature_c, 1),
                humidity=humidity,
                raw_bytes=data[:6],
                raw_bits="".join(str(b) for b in bits[:48]),
                extra={"bit_offset": bit_offset},
            )
        return None

    @staticmethod
    def _fineoffset_sanity(temperature_c: float, humidity: int) -> bool:
        """Return True when the decoded values are physically plausible."""
        return -40.0 <= temperature_c <= 60.0 and 0 < humidity <= 100

    # ------------------------------------------------------------------
    # Protocol: Nexus / Rubicson / Prologue / Digoo
    # ------------------------------------------------------------------

    def _decode_nexus(self, bits: list[int]) -> DecodedData | None:
        """Decode Nexus-TH / Rubicson / Prologue-compatible sensors.

        Frame layout (36 bits):
          Bits 0-7:   Device ID
          Bit 8:      Battery (1=OK, 0=Low)
          Bits 9-10:  Channel (1-3)
          Bits 11:    Constant 1
          Bits 12-23: Temperature raw (signed, ×0.1 °C)
          Bits 24-27: Constant 0000
          Bits 28-35: Humidity (%)
        """
        for bit_offset in (0, 1, 2):
            shifted = bits[bit_offset:]
            if len(shifted) < 36:
                continue
            data = self._bits_to_bytes(shifted)
            if len(data) < 5:
                continue

            device_id = data[0]
            battery_ok = bool((data[1] >> 7) & 1)
            channel = ((data[1] >> 5) & 0x03) + 1
            temp_raw = ((data[1] & 0x0F) << 8) | data[2]
            if temp_raw & 0x800:
                temp_raw -= 0x1000
            temperature_c = temp_raw * 0.1
            humidity = data[4] if len(data) > 4 else None

            if not (-40.0 <= temperature_c <= 60.0):
                continue
            if humidity is not None and not (0 < humidity <= 100):
                continue

            return DecodedData(
                protocol="Nexus/Rubicson-compatible",
                device_id=device_id,
                channel=channel,
                battery_ok=battery_ok,
                temperature_c=round(temperature_c, 1),
                humidity=humidity,
                raw_bytes=data[:5],
                raw_bits="".join(str(b) for b in bits[:40]),
                extra={"bit_offset": bit_offset},
            )
        return None

    # ------------------------------------------------------------------
    # Protocol: Generic (raw bytes for user inspection)
    # ------------------------------------------------------------------

    def _decode_generic(self, bits: list[int], name: str) -> DecodedData | None:
        """Return raw decoded bytes without protocol-specific interpretation."""
        if len(bits) < 16:
            return None
        data = self._bits_to_bytes(bits)
        return DecodedData(
            protocol=name,
            raw_bytes=data,
            raw_bits="".join(str(b) for b in bits),
        )
