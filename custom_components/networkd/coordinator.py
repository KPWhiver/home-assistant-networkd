import json
from datetime import timedelta
from dataclasses import dataclass, field
from dbus_fast import InterfaceNotFoundError
from dbus_fast.aio import ProxyInterface

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import format_mac, CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, LOGGER


@dataclass
class NetworkdInterface:
    interface_name: str
    dhcp_server: ProxyInterface
    description: dict
    dhcp_clients: list

    def device_info(self):
        interface_type = self.description['Type']
        mac_int = self.description.get('PermanentHardwareAddress')
        if mac_int is None:
            mac_int = self.description.get('HardwareAddress')

        connections = set()
        if mac_int is None:
            identifier = self.interface_name
            name = self.interface_name
        else:
            identifier = format_mac(':'.join(format(mac_part, 'X') for mac_part in mac_int))
            name = f'{self.interface_name} ({identifier})'
            if interface_type == 'vlan':
                identifier += f'@{self.interface_name}'
            else:
                connections = {(CONNECTION_NETWORK_MAC, identifier)}

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            connections=connections,
            manufacturer=self.description.get('Vendor'),
            model=self.description.get('Model'),
            name=name
        )


@dataclass
class NetworkdDHCPClient:
    interface: NetworkdInterface
    ip_address: str
    mac_address: str


@dataclass
class NetworkdData:
    dhcp_clients: dict[str, NetworkdDHCPClient]


async def create_networkd_coordinator(hass, interface_names):
    interfaces = []
    for interface_name in interface_names:
        interface = await hass.data[DOMAIN].manager.call_get_link_by_name(interface_name)
        link_introspection = await hass.data[DOMAIN].bus.introspect('org.freedesktop.network1', interface[1])
        link_obj = hass.data[DOMAIN].bus.get_proxy_object('org.freedesktop.network1', interface[1], link_introspection)
        try:
            dhcp_server = link_obj.get_interface('org.freedesktop.network1.DHCPServer')
        except InterfaceNotFoundError:
            dhcp_server = None
        link_interface = link_obj.get_interface('org.freedesktop.network1.Link')
        description = await link_interface.call_describe()

        interfaces.append(NetworkdInterface(interface_name, dhcp_server, json.loads(description), []))

    return NetworkdCoordinator(hass, interfaces)


class NetworkdCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, interfaces):
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60)
        )
        self._hass = hass
        self._interfaces = interfaces

    def get_interfaces(self):
        return self._interfaces

    async def _async_update_data(self):
        networkd_data = NetworkdData({})

        for interface in self._interfaces:
            interface.dhcp_clients = []

            if interface.dhcp_server is not None:
                leases = await interface.dhcp_server.get_leases()
                for lease in leases:
                    mac_address = format_mac(lease[4][0:6].hex(':'))
                    ip_address = '.'.join(f'{part}' for part in lease[2])

                    dhcp_client = NetworkdDHCPClient(interface, ip_address, mac_address)
                    interface.dhcp_clients.append(dhcp_client)
                    networkd_data.dhcp_clients[mac_address] = dhcp_client

        return networkd_data
