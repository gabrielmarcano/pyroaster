# API

### GET /config

Returns the actual configuration.

Returns:

```json
{
  "mode": "cafe" | "cacao" | "mani",
  "starting_temperature": number,
  "timer": number
}
```

### PATCH /config

Change the configuration parameters.

Payload: (Not all required)

```json
{
  "mode": "cafe" | "cacao" | "mani",
  "starting_temperature": number,
  "timer": number
}
```

Returns:

```json
{
  "mode": "cafe" | "cacao" | "mani",
  "starting_temperature": number,
  "timer": number
}
```

### POST /controller

Perform an action in the controller.

Payload:

```json
{
  "action": "activate" | "deactivate" | "stop",
}
```

Returns:

```text
Controller activated
Controller deactivated
Controller stopped
```

### POST /time

Add or reduce 1 second to the timer controller.

Payload:

```json
{
  "action": "add" | "reduce"
}
```

Returns:

```json
{
  "total_time": number,
  "current_time": number
}
```

### POST /reset

Resets the esp32.

### GET /events

Main server sent event streaming endpoint.

Returns:

event: sensors

```json
{
  "temperature": number,
  "humidity": number
}
```

event: time

```json
{
  "total_time": number,
  "current_time": number
}
```

event: states

```json
{
  "motor_a": 0 | 1,
  "motor_b": 0 | 1,
  "motor_c": 0 | 1,
}
```

event: controller

```json
{
  "active": boolean,
  "mode": "cafe" | "cacao" | "mani" | None,
  "time": number,
  "starting_temperature": number
}
```
