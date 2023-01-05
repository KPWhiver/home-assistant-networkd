from dataclasses import dataclass

from dbus_fast import BusType
from dbus_fast.aio import MessageBus, ProxyInterface

from .coordinator import NetworkdCoordinator


@dataclass
class NetworkdState:
    bus: MessageBus
    manager: ProxyInterface
    tracked_dhcp_clients: set[str]
    coordinators: dict[str, NetworkdCoordinator]


async def create_networkd_state():
    bus = await MessageBus(bus_type = BusType.SYSTEM).connect()
    introspection = await bus.introspect('org.freedesktop.network1', '/org/freedesktop/network1')
    obj = bus.get_proxy_object('org.freedesktop.network1', '/org/freedesktop/network1', introspection)
    manager = obj.get_interface('org.freedesktop.network1.Manager')

    return NetworkdState(bus, manager, set(), {})


async def destroy_networkd_state(networkd_state):
    networkd_state.bus.disconnect()
    await networkd_state.bus.wait_for_disconnect()
