from types import MappingProxyType

from homeassistant.const import Platform

from .const import DOMAIN, CONF_INTERFACES
from .common import create_networkd_state, destroy_networkd_state
from .coordinator import create_networkd_coordinator


PLATFORMS = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass, entry):
    if entry.options:
        hass.config_entries.async_update_entry(entry, data=entry.options, options=MappingProxyType({}))

    hass.data.setdefault(DOMAIN, None)
    if hass.data[DOMAIN] is None:
        hass.data[DOMAIN] = await create_networkd_state()
        hass.data[DOMAIN].coordinator = await create_networkd_coordinator(hass, entry.data[CONF_INTERFACES])

    await hass.data[DOMAIN].coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await destroy_networkd_state(hass.data[DOMAIN])
        del hass.data[DOMAIN]

    return unload_ok

