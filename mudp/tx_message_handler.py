import random
import time
from typing import Callable

from meshtastic import portnums_pb2, mesh_pb2, telemetry_pb2, admin_pb2, BROADCAST_NUM
from mudp.encryption import generate_hash, encrypt_packet
from mudp.singleton import conn, node

message_id = random.getrandbits(32)


def create_payload(data, portnum: int, bitfield: int = 1, **kwargs) -> bytes:
    """Generalized function to create a payload."""
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnum
    encoded_message.payload = data.SerializeToString() if hasattr(data, "SerializeToString") else data
    encoded_message.want_response = kwargs.get("want_response", False)
    encoded_message.bitfield = bitfield
    return generate_mesh_packet(encoded_message, **kwargs)


def generate_mesh_packet(encoded_message: mesh_pb2.Data, **kwargs) -> bytes:
    """Generate the final mesh packet."""

    from_id = int(node.node_id.replace("!", ""), 16)
    destination = kwargs.get("to", BROADCAST_NUM)

    reserved_ids = [1, 2, 3, 4, 4294967295]
    if from_id in reserved_ids:
        raise ValueError(f"Node ID '{from_id}' is reserved and cannot be used. Please choose a different ID.")

    global message_id
    message_id = get_message_id(message_id)

    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id
    setattr(mesh_packet, "from", from_id)
    mesh_packet.to = int(destination)
    mesh_packet.want_ack = kwargs.get("want_ack", False)
    mesh_packet.channel = generate_hash(node.channel, node.key)
    hop_limit = kwargs.get("hop_limit", 3)
    hop_start = kwargs.get("hop_start", 3)
    if hop_limit > hop_start:
        hop_start = hop_limit
    mesh_packet.hop_limit = hop_limit
    mesh_packet.hop_start = hop_start

    if node.key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(node.channel, node.key, mesh_packet, encoded_message)

    return mesh_packet.SerializeToString()


def get_portnum_name(portnum: int) -> str:
    for name, number in portnums_pb2.PortNum.items():
        if number == portnum:
            return name
    return f"UNKNOWN_PORTNUM ({portnum})"


def publish_message(payload_function: Callable, portnum: int, **kwargs) -> None:
    """Send a message of any type, with logging."""

    try:
        payload = payload_function(portnum=portnum, **kwargs)
        print(f"\n[TX] Portnum = {get_portnum_name(portnum)} ({portnum})")

        print(f"     To: {kwargs.get('to', 'BROADCAST_NUM')}")
        for k, v in kwargs.items():
            if k not in ("use_config", "to", "channel", "key") and v is not None:
                print(f"     {k}: {v}")

        conn.sendto(payload, (conn.host, conn.port))

        print(f"\n[SENT] {payload}")

    except Exception as e:
        print(f"Error while sending message: {e}")


def get_message_id(rolling_message_id: int, max_message_id: int = 4294967295) -> int:
    """Increment the message ID with sequential wrapping and add a random upper bit component to prevent predictability."""
    rolling_message_id = (rolling_message_id + 1) % (max_message_id & 0x3FF + 1)
    random_bits = random.randint(0, (1 << 22) - 1) << 10
    message_id = rolling_message_id | random_bits
    return message_id


def send_nodeinfo(**kwargs) -> None:
    """Send node information including short/long names and hardware model."""

    if "node_id" not in kwargs:
        kwargs["node_id"] = node.node_id
    if "long_name" not in kwargs:
        kwargs["long_name"] = node.long_name
    if "short_name" not in kwargs:
        kwargs["short_name"] = node.short_name
    if "hw_model" not in kwargs:
        kwargs["hw_model"] = 255

    def create_nodeinfo_payload(portnum: int, **fields) -> bytes:
        nodeinfo = mesh_pb2.User(
            hw_model=fields.pop("hw_model", 255),
            id=fields.pop("node_id", node.node_id),
            long_name=fields.pop("long_name", node.long_name),
            short_name=fields.pop("short_name", node.short_name),
        )
        for k, v in fields.items():
            if v is not None and k in mesh_pb2.User.DESCRIPTOR.fields_by_name:
                setattr(nodeinfo, k, v)
        return create_payload(nodeinfo, portnum, **kwargs)

    publish_message(create_nodeinfo_payload, portnum=portnums_pb2.NODEINFO_APP, **kwargs)


def send_text_message(message: str = None, **kwargs) -> None:
    """Send a text message to the specified destination."""

    if "location_source" not in kwargs:
        kwargs["location_source"] = "LOC_MANUAL"

    def create_text_payload(portnum: int, message: str = None, **kwargs):
        data = message.encode("utf-8")
        return create_payload(data, portnum, **kwargs)

    publish_message(create_text_payload, portnums_pb2.TEXT_MESSAGE_APP, message=message, **kwargs)


def send_position(latitude: float = None, longitude: float = None, **kwargs) -> None:
    """Send current position with optional additional fields (e.g., ground_speed, fix_type, etc)."""

    if "location_source" not in kwargs:
        kwargs["location_source"] = "LOC_MANUAL"

    def create_position_payload(portnum: int, **fields):
        position_fields = {
            "latitude_i": int(latitude * 1e7) if latitude is not None else None,
            "longitude_i": int(longitude * 1e7) if longitude is not None else None,
            "time": int(time.time()),
        }

        # Filter out None values and remove keys we've already handled
        reserved_keys = {"latitude", "longitude"}
        data = {
            k: v
            for k, v in fields.items()
            if v is not None and k not in reserved_keys and k in mesh_pb2.Position.DESCRIPTOR.fields_by_name
        }
        position_fields.update(data)

        return create_payload(mesh_pb2.Position(**position_fields), portnum, **kwargs)

    publish_message(
        create_position_payload, portnums_pb2.POSITION_APP, latitude=latitude, longitude=longitude, **kwargs
    )


def send_device_telemetry(**kwargs) -> None:
    """Send telemetry packet including battery, voltage, channel usage, and uptime."""

    def create_telemetry_payload(portnum: int, **_):
        metrics_kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None and k in telemetry_pb2.DeviceMetrics.DESCRIPTOR.fields_by_name
        }
        metrics = telemetry_pb2.DeviceMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), device_metrics=metrics)
        return create_payload(data, portnum, **kwargs)

    publish_message(create_telemetry_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_power_metrics(**kwargs) -> None:
    """Send power metrics including voltage and current for three channels."""

    def create_power_metrics_payload(portnum: int, **_):
        metrics_kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None and k in telemetry_pb2.PowerMetrics.DESCRIPTOR.fields_by_name
        }
        metrics = telemetry_pb2.PowerMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), power_metrics=metrics)
        return create_payload(data, portnum, **kwargs)

    publish_message(create_power_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_environment_metrics(**kwargs) -> None:
    """Send environment metrics including temperature, humidity, pressure, and gas resistance."""

    def create_environment_metrics_payload(portnum: int, **_):
        # Filter out None values from kwargs
        metrics_kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None and k in telemetry_pb2.EnvironmentMetrics.DESCRIPTOR.fields_by_name
        }
        metrics = telemetry_pb2.EnvironmentMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), environment_metrics=metrics)
        return create_payload(data, portnum, **kwargs)

    publish_message(create_environment_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_health_metrics(**kwargs) -> None:
    """Send health metrics including heart rate, SpO2, and body temperature."""

    def create_health_metrics_payload(portnum: int, **_):
        metrics_kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None and k in telemetry_pb2.HealthMetrics.DESCRIPTOR.fields_by_name
        }
        metrics = telemetry_pb2.HealthMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), health_metrics=metrics)
        return create_payload(data, portnum, **kwargs)

    publish_message(create_health_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


# Admin Message Functions

def send_admin_message(admin_message: admin_pb2.AdminMessage, **kwargs) -> None:
    """Send an admin message to control remote devices."""

    def create_admin_payload(portnum: int, **_):
        return create_payload(admin_message, portnum, **kwargs)

    publish_message(create_admin_payload, portnums_pb2.ADMIN_APP, **kwargs)


def send_reboot(seconds: int = 10, **kwargs) -> None:
    """Tell the destination node to reboot after specified seconds."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.reboot_seconds = seconds
    send_admin_message(admin_msg, **kwargs)


def send_shutdown(seconds: int = 10, **kwargs) -> None:
    """Tell the destination node to shutdown after specified seconds."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.shutdown_seconds = seconds
    send_admin_message(admin_msg, **kwargs)


def send_factory_reset(full_device: bool = False, **kwargs) -> None:
    """Tell the destination node to factory reset.

    Args:
        full_device: If True, performs full device reset (clears BLE bonds & PKI keys).
                    If False, only resets config (preserves BLE bonds & PKI keys).
    """
    admin_msg = admin_pb2.AdminMessage()
    if full_device:
        admin_msg.factory_reset_device = True
    else:
        admin_msg.factory_reset_config = True
    send_admin_message(admin_msg, **kwargs)


def send_reboot_ota(seconds: int = 10, **kwargs) -> None:
    """Tell the destination node to reboot into factory firmware (ESP32)."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.reboot_ota_seconds = seconds
    send_admin_message(admin_msg, **kwargs)


def send_enter_dfu_mode(**kwargs) -> None:
    """Tell the destination node to enter DFU mode (NRF52)."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.enter_dfu_mode_request = True
    send_admin_message(admin_msg, **kwargs)


def send_remove_node(node_id: int, **kwargs) -> None:
    """Tell the destination node to remove a specific node from its NodeDB."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.remove_by_nodenum = node_id
    send_admin_message(admin_msg, **kwargs)


def send_set_favorite_node(node_id: int, **kwargs) -> None:
    """Tell the destination node to set the specified node as favorite."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.set_favorite_node = node_id
    send_admin_message(admin_msg, **kwargs)


def send_remove_favorite_node(node_id: int, **kwargs) -> None:
    """Tell the destination node to remove the specified node from favorites."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.remove_favorite_node = node_id
    send_admin_message(admin_msg, **kwargs)


def send_set_ignored_node(node_id: int, **kwargs) -> None:
    """Tell the destination node to ignore the specified node."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.set_ignored_node = node_id
    send_admin_message(admin_msg, **kwargs)


def send_remove_ignored_node(node_id: int, **kwargs) -> None:
    """Tell the destination node to stop ignoring the specified node."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.remove_ignored_node = node_id
    send_admin_message(admin_msg, **kwargs)


def send_reset_nodedb(**kwargs) -> None:
    """Tell the destination node to clear its list of nodes."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.nodedb_reset = True
    send_admin_message(admin_msg, **kwargs)


def send_set_time(timestamp: int = None, **kwargs) -> None:
    """Tell the destination node to set its time.

    Args:
        timestamp: Unix timestamp. If None or 0, uses current system time.
    """
    if timestamp is None or timestamp == 0:
        timestamp = int(time.time())

    admin_msg = admin_pb2.AdminMessage()
    admin_msg.set_time_only = timestamp
    send_admin_message(admin_msg, **kwargs)


def send_get_device_metadata(**kwargs) -> None:
    """Request device metadata from the destination node."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.get_device_metadata_request = True
    send_admin_message(admin_msg, **kwargs)


def send_set_fixed_position(latitude: float, longitude: float, altitude: int = 0, **kwargs) -> None:
    """Tell the destination node to set a fixed position.

    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        altitude: Altitude in meters
    """
    position = mesh_pb2.Position()
    position.latitude_i = int(latitude * 1e7)
    position.longitude_i = int(longitude * 1e7)
    position.altitude = altitude

    admin_msg = admin_pb2.AdminMessage()
    admin_msg.set_fixed_position.CopyFrom(position)
    send_admin_message(admin_msg, **kwargs)


def send_remove_fixed_position(**kwargs) -> None:
    """Tell the destination node to remove its fixed position."""
    admin_msg = admin_pb2.AdminMessage()
    admin_msg.remove_fixed_position = True
    send_admin_message(admin_msg, **kwargs)
