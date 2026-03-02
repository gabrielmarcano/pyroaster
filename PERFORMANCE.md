# Performance Reference

Low-level timing and resource details for the ESP32 MicroPython roaster firmware.

## Async Architecture

The firmware runs 3 cooperative async tasks on a single core:

| Task | Purpose | Period |
|------|---------|--------|
| `logic_loop` | Sensor reads, motor control, LCD updates | 1s |
| `server_task` | Microdot HTTP + SSE | Event-driven |
| `wifi_manager_task` | Wi-Fi reconnection | 10s |

**Key rule**: Any blocking call in any task freezes *all* tasks. The event loop only yields at `await` points.

## MAX6675 Thermocouple

- **Measurement period**: 220ms (enforced by `read()` — returns cached value if called sooner)
- **SPI transfer**: ~30us software bit-bang for 16 bits
- **Non-blocking by design**: `read()` returns the cached temperature if the 220ms conversion hasn't elapsed
- **Error handling**: Raises `RuntimeError` if the thermocouple is disconnected (open bit set)

## AHT20 Humidity/Temperature Sensor

### Blocking path (old)

`relative_humidity` calls `_perform_measurement()`:
1. `_trigger_measurement()` — writes 3 bytes via I2C (~100us)
2. `_wait_for_idle()` — polls BUSY bit every 5ms (~80ms total)
3. `_read_to_buffer()` — reads 6 bytes (~150us)

**Total: ~80ms blocking the event loop every second.**

### Non-blocking path (current)

State machine in `read_sensor_data()`:
1. **On init**: trigger first measurement immediately
2. **Each call**: check `status` (single 6-byte I2C read, ~35-70us)
   - **Not busy**: compute humidity from `_buf[1:4]`, then trigger next measurement
   - **Busy**: return cached humidity, do nothing

Raw humidity formula (same as driver):
```
raw = (buf[1] << 12) | (buf[2] << 4) | (buf[3] >> 4)
humidity = (raw * 100) / 0x100000
```

**Important**: `_trigger_measurement()` overwrites `_buf[0:3]`, so humidity must be computed *before* triggering.

**Tradeoff**: Humidity lags by 1 loop iteration (1 second). Acceptable — humidity changes slowly during roasting.

**Error recovery**: On any exception, the `__aht_measurement_triggered` flag resets so the next call retries the trigger.

## I2C Buses

### Hardware vs Software I2C

| | SoftI2C | I2C (hardware) |
|---|---------|----------------|
| Implementation | CPU bit-bangs GPIO | ESP32 I2C peripheral (DMA) |
| Per-byte cost | ~50-100us CPU time | ~2.5us at 400kHz (idle CPU) |
| Pins | Any GPIO | Any GPIO (ESP32 matrix routing) |
| Peripheral ID | N/A | 0 or 1 |

### Pin Assignments

| Bus | ID | SDA | SCL | Devices |
|-----|----|-----|-----|---------|
| Sensors | `I2C(0)` | GPIO 17 | GPIO 16 | AHT20 (0x38) |
| LCD | `I2C(1)` | GPIO 21 | GPIO 22 | PCF8574 (0x27) |

### Savings

- LCD update (16 chars, 4-bit mode = 64 I2C writes): ~3-6ms saved per line
- AHT20 status read (6 bytes): ~150-500us saved per read

**Fallback**: If hardware I2C causes issues, revert to `SoftI2C` — one-line change per file.

## LCD HD44780 (via PCF8574 I2C expander)

- **Interface**: 4-bit mode over I2C
- **Per-character cost**: 4 I2C writes (2 nibbles x 2 strobes each) = ~200-400us per char at 400kHz hardware I2C
- **Per-line cost (16 chars)**: ~3-6ms
- **`clear()` command**: 5ms hardware delay (unavoidable, internal LCD timing)
- **Caching**: `show_data()` compares lines against `__last_line0`/`__last_line1` — skips I2C writes when content hasn't changed

## Garbage Collection

MicroPython uses **mark-and-sweep GC** (no generational collector). When the heap fills, GC triggers automatically, causing unpredictable 10-50ms pauses.

### Strategy

`gc.collect()` runs at the end of every `logic_loop()` iteration, outside the try/except block:
- Runs with a mostly-clean heap: ~5-15ms, predictable
- Absorbed into the 1s sleep period (GC runs before `await asyncio.sleep(1)`)
- Outside try/except: ensures GC runs even after error handling (which allocates strings)

### Allocation Hotspots

| Source | Allocations |
|--------|-------------|
| `get_json()` dicts | New dict every call |
| `json.dumps()` | String serialization |
| f-strings in `show_data()` | Each `f"..."` allocates a new string |
| `.ljust()` | New string if padding needed |
| Logger format strings | Each `logger.debug(...)` call |

## SSE (Server-Sent Events)

- Each event: `json.dumps(data)` + bytes concatenation
- **Change detection**: Events only sent when data differs from last sent (`!=` comparison on dicts)
- **Per-client cost**: Each connected client runs its own `handle_events` coroutine with independent change tracking
- **Sleep period**: 1s between checks per client

## MicroPython String Behavior

- Strings are **immutable** — every concatenation allocates a new string
- f-strings compile to concatenation: `f"T: {t}C"` creates multiple intermediate strings
- `.format()` has the same allocation behavior
- `.ljust()` returns a new string if padding is needed (same object if already the right length)
- For hot paths, pre-allocated `bytearray` + `memoryview` would avoid allocations, but the current per-second rate doesn't justify the complexity
