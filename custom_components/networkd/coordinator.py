import json
from datetime import timedelta
from dataclasses import dataclass, field

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.device_registry import format_mac, CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, LOGGER, CONF_INTERFACE

@dataclass
class NetworkdDHCPClient:
    interface: str
    ip_address: str
    mac_address: str


@dataclass
class NetworkdData:
    dhcp_clients: dict[str, NetworkdDHCPClient]


class NetworkdCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60)
        )
        self._hass = hass
        self._interface_name = entry.data[CONF_INTERFACE]
        self._dhcp_server = None
        self._description = None

    def device_info(self):
        interface_type = self._description['Type']
        mac_int = self._description.get('PermanentHardwareAddress')
        if mac_int is None:
            mac_int = self._description.get('HardwareAddress')

        connections = set()
        if mac_int is None:
            identifier = self._interface_name
            name = self._interface_name
        else:
            identifier = format_mac(':'.join(format(mac_part, 'X') for mac_part in mac_int))
            name = f'{self._interface_name} ({identifier})'
            if interface_type == 'vlan':
                identifier += f'@{self._interface_name}'
            else:
                connections = {(CONNECTION_NETWORK_MAC, identifier)}

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            connections=connections,
            manufacturer=self._description.get('Vendor'),
            model=self._description.get('Model'),
            name=name
        )

    async def _async_update_data(self):
        if self._dhcp_server is None:
            bus = self._hass.data[DOMAIN].bus
            interface = await self._hass.data[DOMAIN].manager.call_get_link_by_name(self._interface_name)
            link_introspection = await bus.introspect('org.freedesktop.network1', interface[1])
            link_obj = bus.get_proxy_object('org.freedesktop.network1', interface[1], link_introspection)
            self._dhcp_server = link_obj.get_interface('org.freedesktop.network1.DHCPServer')

            link_interface = link_obj.get_interface('org.freedesktop.network1.Link')
            description = await link_interface.call_describe()
            self._description = json.loads(description)

        networkd_data = NetworkdData({})

        leases = await self._dhcp_server.get_leases()
        for lease in leases:
            mac_address = format_mac(lease[4][0:6].hex(':'))
            ip_address = '.'.join(f'{part}' for part in lease[2])

            networkd_data.dhcp_clients[mac_address] = NetworkdDHCPClient(self._interface_name, ip_address, mac_address)

        return networkd_data
