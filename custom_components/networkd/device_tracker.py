from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry
from homeassistant.components.device_tracker import SourceType, ScannerEntity
from homeassistant.core import callback

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN].coordinators[entry.entry_id]
    tracked_dhcp_clients = hass.data[DOMAIN].tracked_dhcp_clients

    # Add entities currently connected
    @callback
    def process_data():
        new_entities = []
        for dhcp_client in coordinator.data.dhcp_clients.values():
            if dhcp_client.mac_address not in tracked_dhcp_clients:
                tracked_dhcp_clients.add(dhcp_client.mac_address)
                new_entities.append(NetworkdDevice(coordinator, dhcp_client, dhcp_client.mac_address))
        async_add_entities(new_entities)

    process_data()
    entry.async_on_unload(coordinator.async_add_listener(process_data))

    # Add entities previously connected
    registry = entity_registry.async_get(hass)
    entry_entries = entity_registry.async_entries_for_config_entry(registry, entry.entry_id)
    registered_dhcp_clients = filter(lambda entry: entry.domain == 'device_tracker' and entry.unique_id not in tracked_dhcp_clients, entry_entries)

    new_entities = []
    for dhcp_client in registered_dhcp_clients:
        if dhcp_client.disabled:
            registry.async_remove(dhcp_client.entity_id)
        else:
            tracked_dhcp_clients.add(dhcp_client.unique_id)
            new_entities.append(NetworkdDevice(coordinator, None, dhcp_client.unique_id))
    async_add_entities(new_entities)


class NetworkdDevice(CoordinatorEntity, ScannerEntity):
    def __init__(self, coordinator, dhcp_client, mac_address):
        super().__init__(coordinator)
        self._dhcp_client = dhcp_client
        self._mac_address = mac_address

    @callback
    def _handle_coordinator_update(self):
        if self.available:
            self._dhcp_client = self.coordinator.data.dhcp_clients.get(self._mac_address)
        else:
            self._dhcp_client = None

        super()._handle_coordinator_update()

    @property
    def source_type(self):
        return SourceType.ROUTER

    @property
    def is_connected(self):
        return self._dhcp_client is not None

    @property
    def ip_address(self):
        if self._dhcp_client is None:
            return None
        return self._dhcp_client.ip_address

    @property
    def mac_address(self):
        return self._mac_address
