from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from .const import DOMAIN, CONF_INTERFACE, LOGGER


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN].coordinators[entry.entry_id]
    registry = entity_registry.async_get(hass)
    async_add_entities([NetworkdInterface(coordinator, entry, registry)])


class NetworkdInterface(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, registry):
        super().__init__(coordinator)

        self._entry = entry
        self._registry = registry
        self._count = 0
        self.entry_id = f'{self._entry.data[CONF_INTERFACE]}_unknown_dhcp_client_count'

    @property
    def name(self):
        return 'Unknown DHCP client count'

    @property
    def device_info(self):
        return self.coordinator.device_info()

    @property
    def has_entity_name(self):
        return True

    @property
    def unique_id(self):
        return self._entry.entry_id

    @property
    def native_value(self):
        return self._count

    @callback
    def _handle_coordinator_update(self):
        if self.available:
            entries = entity_registry.async_entries_for_config_entry(self._registry, self._entry.entry_id)

            disabled_dhcp_clients = list(map(lambda entry: entry.unique_id, filter(lambda entry: entry.domain == 'device_tracker' and entry.disabled, entries)))
            dhcp_clients = self.coordinator.data.dhcp_clients.keys()

            self._count = 0
            for dhcp_client in dhcp_clients:
                if dhcp_client in disabled_dhcp_clients:
                    self._count += 1
        else:
            self._count = None

        super()._handle_coordinator_update()
