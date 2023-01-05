from homeassistant.const import Platform

from .const import DOMAIN
from .common import create_networkd_state, destroy_networkd_state
from .coordinator import NetworkdCoordinator


PLATFORMS = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, None)
    if hass.data[DOMAIN] is None:
        hass.data[DOMAIN] = await create_networkd_state()

    coordinator = NetworkdCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN].coordinators[entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    del hass.data[DOMAIN].coordinators[entry.entry_id]

    if hass.data[DOMAIN].coordinators == {}:
        await destroy_networkd_state(hass.data[DOMAIN])
        del hass.data[DOMAIN]

