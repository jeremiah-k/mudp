# MUDP - Meshtastic UDP Proxy

This library provides UDP-based broadcasting of Meshtastic-compatible packets.

## Development Status
- Working on admin message implementation

# Installation

```bash
pip install mudp
```

# Command Line

To view all Meshtastic udp activity on your LAN:
```bash
mudp
```

# Functions (see examples for further information):

```python
from mudp import (
    conn,
    node,
    send_nodeinfo,
    send_text_message,
    send_device_telemetry,
    send_position,
    send_environment_metrics,
    send_power_metrics,
    send_health_metrics,
    # Admin functions for remote device management
    send_reboot,
    send_shutdown,
    send_factory_reset,
    send_remove_node,
    send_set_time,
    send_get_device_metadata,
)

MCAST_GRP = "224.0.0.69"
MCAST_PORT = 4403

node.node_id = "!deadbeef"
node.long_name = "UDP Test"
node.short_name = "UDP"
node.channel = "LongFast"
node.key = "1PG7OiApB1nwvP+rz05pAQ=="
conn.setup_multicast(MCAST_GRP, MCAST_PORT)

send_nodeinfo(keys=values...)
send_device_telemetry(keys=values...)
send_position(latitude, longitude, keys=values...)
send_environment_metrics(keys=values...)
send_power_metrics(keys=values...)
send_health_metrics(keys=values...)
send_text_message("text", keys=values...)
```

Optional Arguments for all message types:

- to=INT
- hop_limit=INT
- hop_start=INT
- want_ack=BOOL
- want_response=BOOL

Example:
```python
send_text_message("Happy New Year", to=12345678, hop_limit=5)
```

## Admin Functions

MUDP now supports admin messages for remote device management:

```python
# Device control
send_reboot(seconds=10, to=12345678)           # Reboot device in 10 seconds
send_shutdown(seconds=30, to=12345678)         # Shutdown device in 30 seconds
send_factory_reset(full_device=False, to=12345678)  # Reset config only
send_factory_reset(full_device=True, to=12345678)   # Full device reset

# Node management
send_remove_node(node_id=87654321, to=12345678)     # Remove node from NodeDB
send_set_favorite_node(node_id=87654321, to=12345678)  # Set node as favorite
send_reset_nodedb(to=12345678)                      # Clear entire NodeDB

# Configuration
send_set_time(to=12345678)                          # Set current time
send_set_fixed_position(37.7749, -122.4194, to=12345678)  # Set fixed GPS position
send_get_device_metadata(to=12345678)               # Request device info
```

**Note**: Admin functions require the target device to have admin access enabled and may require authentication depending on device configuration.

Supported keyword arguments for nodeinfo:

- node_id
- long_name
- short_name
- hw_model
- is_licensed
- role
- public_key

Supported keyword arguments for device metrics:

 - battery_level
 - voltage
 - channel_utilization
 - air_util_tx
 - uptime_seconds

Supported keyword arguments for position metrics:

- latitude (required)
- longitude (required)
- latitude_i
- longitude_i
- altitude
- precision_bits
- HDOP
- PDOP
- VDOP
- altitude_geoidal_separation
- altitude_hae
- altitude_source
- fix_quality
- fix_type
- gps_accuracy
- ground_speed
- ground_track
- next_update
- sats_in_view
- sensor_id
- seq_number
- timestamp
- timestamp_millis_adjust

Supported keyword arguments for environment metrics:

- temperature
- relative_humidity
- barometric_pressure
- gas_resistance
- voltage
- current
- iaq
- distance
- ir_lux
- lux
- radiation
- rainfall_1h
- rainfall_24h
- soil_moisture
- soil_temperature
- uv_lux
- weight
- white_lux
- wind_direction
- wind_gust
- wind_lull
- wind_speed

Supported keyword arguments for power metrics:

 - ch1_voltage
 - ch1_current
 - ch2_voltage
 - ch2_current
 - ch3_voltage
 - ch3_current

Supported keyword arguments for health metrics:
 
 - heart_bpm
 - spO2
 - temperature



## Install in development (editable) mode:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```