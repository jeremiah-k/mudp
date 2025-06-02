#!/usr/bin/env python3
"""
MUDP Admin Example

This example demonstrates how to use MUDP's admin message functionality
to remotely manage Meshtastic devices.

WARNING: Admin functions can reboot, shutdown, or reset devices.
Use with caution and only on devices you own or have permission to manage.
"""

import time
from mudp import (
    conn,
    node,
    send_nodeinfo,
    send_reboot,
    send_shutdown,
    send_factory_reset,
    send_remove_node,
    send_set_favorite_node,
    send_reset_nodedb,
    send_set_time,
    send_get_device_metadata,
    send_set_fixed_position,
    send_remove_fixed_position,
)

MCAST_GRP = "224.0.0.69"
MCAST_PORT = 4403

# Target device node ID (replace with actual device ID)
TARGET_NODE_ID = 0x12345678  # Example: !12345678


def setup_node():
    """Configure the local node settings."""
    node.node_id = "!deadbeef"
    node.long_name = "Admin Controller"
    node.short_name = "ADMIN"
    node.channel = "LongFast"
    node.key = "AQ=="  # Default key - change for your network
    conn.setup_multicast(MCAST_GRP, MCAST_PORT)


def demo_device_control():
    """Demonstrate device control admin functions."""
    print("\n=== Device Control Demo ===")
    
    # Send nodeinfo first to announce ourselves
    print("Sending nodeinfo...")
    send_nodeinfo()
    time.sleep(2)
    
    # Request device metadata
    print(f"Requesting device metadata from {TARGET_NODE_ID:08x}...")
    send_get_device_metadata(to=TARGET_NODE_ID)
    time.sleep(3)
    
    # Set device time to current time
    print(f"Setting time on device {TARGET_NODE_ID:08x}...")
    send_set_time(to=TARGET_NODE_ID)
    time.sleep(2)
    
    # CAUTION: Uncomment these only if you want to actually reboot/shutdown
    # print(f"Scheduling reboot of device {TARGET_NODE_ID:08x} in 60 seconds...")
    # send_reboot(seconds=60, to=TARGET_NODE_ID)
    # time.sleep(2)
    
    # print(f"Scheduling shutdown of device {TARGET_NODE_ID:08x} in 120 seconds...")
    # send_shutdown(seconds=120, to=TARGET_NODE_ID)


def demo_node_management():
    """Demonstrate node management admin functions."""
    print("\n=== Node Management Demo ===")
    
    # Example node to manage (replace with actual node ID)
    example_node = 0x87654321
    
    # Set a node as favorite
    print(f"Setting node {example_node:08x} as favorite on device {TARGET_NODE_ID:08x}...")
    send_set_favorite_node(node_id=example_node, to=TARGET_NODE_ID)
    time.sleep(2)
    
    # Remove a node from favorites (same node for demo)
    print(f"Removing node {example_node:08x} from favorites on device {TARGET_NODE_ID:08x}...")
    send_remove_favorite_node(node_id=example_node, to=TARGET_NODE_ID)
    time.sleep(2)
    
    # CAUTION: This will remove a node from the device's database
    # print(f"Removing node {example_node:08x} from NodeDB on device {TARGET_NODE_ID:08x}...")
    # send_remove_node(node_id=example_node, to=TARGET_NODE_ID)
    
    # CAUTION: This will clear the entire NodeDB
    # print(f"Resetting NodeDB on device {TARGET_NODE_ID:08x}...")
    # send_reset_nodedb(to=TARGET_NODE_ID)


def demo_position_management():
    """Demonstrate position management admin functions."""
    print("\n=== Position Management Demo ===")
    
    # Set a fixed position (San Francisco coordinates)
    latitude = 37.7749
    longitude = -122.4194
    altitude = 50  # meters
    
    print(f"Setting fixed position on device {TARGET_NODE_ID:08x}...")
    print(f"  Latitude: {latitude}")
    print(f"  Longitude: {longitude}")
    print(f"  Altitude: {altitude}m")
    send_set_fixed_position(latitude, longitude, altitude, to=TARGET_NODE_ID)
    time.sleep(3)
    
    # Remove fixed position
    print(f"Removing fixed position from device {TARGET_NODE_ID:08x}...")
    send_remove_fixed_position(to=TARGET_NODE_ID)


def demo_factory_reset():
    """Demonstrate factory reset (DANGEROUS - commented out for safety)."""
    print("\n=== Factory Reset Demo (DISABLED FOR SAFETY) ===")
    print("Factory reset functions are commented out for safety.")
    print("Uncomment the lines below only if you really want to reset a device.")
    
    # DANGER: These will reset the device configuration
    # print(f"Performing config-only factory reset on device {TARGET_NODE_ID:08x}...")
    # send_factory_reset(full_device=False, to=TARGET_NODE_ID)
    
    # EXTREME DANGER: This will completely reset the device
    # print(f"Performing full device factory reset on device {TARGET_NODE_ID:08x}...")
    # send_factory_reset(full_device=True, to=TARGET_NODE_ID)


def main():
    """Main demo function."""
    print("MUDP Admin Functions Demo")
    print("=" * 40)
    print(f"Target device: !{TARGET_NODE_ID:08x}")
    print("\nWARNING: This demo sends admin commands to real devices.")
    print("Make sure you have permission to manage the target device!")
    
    # Setup our node
    setup_node()
    
    # Run demos
    demo_device_control()
    demo_node_management()
    demo_position_management()
    demo_factory_reset()
    
    print("\nDemo completed!")
    print("\nNote: Some admin commands may require authentication")
    print("depending on the target device's security configuration.")


if __name__ == "__main__":
    main()
