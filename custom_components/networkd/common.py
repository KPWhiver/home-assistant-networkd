from dataclasses import dataclass

from dbus_fast import BusType
from dbus_fast.aio import MessageBus, ProxyInterface

from .coordinator import NetworkdCoordinator


@dataclass
class NetworkdState:
    bus: MessageBus
    manager: ProxyInterface
    interfaces: dict
    tracked_dhcp_clients: set[str]
    coordinator: NetworkdCoordinator


async def create_networkd_state():
    bus = await MessageBus(bus_type = BusType.SYSTEM).connect()
    try:
        introspection = await bus.introspect('org.freedesktop.network1', '/org/freedesktop/network1')
        obj = bus.get_proxy_object('org.freedesktop.network1', '/org/freedesktop/network1', introspection)
        manager = obj.get_interface('org.freedesktop.network1.Manager')
    except:
        bus.disconnect()
        await bus.wait_for_disconnect()
        raise

    return NetworkdState(bus, manager, {}, set(), None)


async def destroy_networkd_state(networkd_state):
    networkd_state.bus.disconnect()
    await networkd_state.bus.wait_for_disconnect()
