from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from .const import DOMAIN, LOGGER


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN].coordinator
    registry = entity_registry.async_get(hass)

    new_entities = []
    for interface in coordinator.get_interfaces():
        if interface.dhcp_server is not None:
            new_entities.append(NetworkdDHCPUnknownClientCount(coordinator, interface, entry, registry))

    async_add_entities(new_entities)


class NetworkdDHCPUnknownClientCount(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, interface, entry, registry):
        super().__init__(coordinator)

        self._interface = interface
        self._entry = entry
        self._registry = registry
        self._count = 0

    @property
    def name(self):
        return 'Unknown DHCP client count'

    @property
    def device_info(self):
        return self._interface.device_info()

    @property
    def has_entity_name(self):
        return True

    @property
    def unique_id(self):
        return f'{list(self.device_info["identifiers"])[0][1]}_ducc'

    @property
    def native_value(self):
        return self._count

    @callback
    def _handle_coordinator_update(self):
        if self.available:
            entries = entity_registry.async_entries_for_config_entry(self._registry, self._entry.entry_id)

            disabled_dhcp_clients = list(map(lambda entry: entry.unique_id, filter(lambda entry: entry.domain == 'device_tracker' and entry.disabled, entries)))
            dhcp_clients = self._interface.dhcp_clients

            self._count = 0
            for dhcp_client in dhcp_clients:
                if dhcp_client.mac_address in disabled_dhcp_clients:
                    self._count += 1
        else:
            self._count = None

        super()._handle_coordinator_update()
