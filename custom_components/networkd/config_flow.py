import voluptuous as vol

from dbus_fast import BusType
from dbus_fast.aio import MessageBus, ProxyInterface

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import DOMAIN, CONF_INTERFACES, LOGGER
from .common import create_networkd_state, destroy_networkd_state


async def get_link_names():
    networkd_state = await create_networkd_state()
    links = await networkd_state.manager.call_list_links()
    await destroy_networkd_state(networkd_state)
    return [link[1] for link in links]


class NetworkdOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.config_entry = entry

    async def async_step_init(self, user_input = None):
        if user_input is not None:
            return self.async_create_entry(title = 'Networkd', data = user_input)

        try:
            link_names = await get_link_names()
        except:
            return self.async_abort(reason="connection_failed")

        current_link_names = self.config_entry.data[CONF_INTERFACES]
        data_schema = vol.Schema({
            vol.Required(CONF_INTERFACES, default=current_link_names): cv.multi_select(link_names),
        })

        return self.async_show_form(step_id='init', data_schema = data_schema)


class NetworkdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title = 'Networkd', data = user_input)

        try:
            link_names = await get_link_names()
        except:
            return self.async_abort(reason="connection_failed")
        data_schema = vol.Schema({
            vol.Required(CONF_INTERFACES): cv.multi_select(link_names),
        })

        return self.async_show_form(step_id='user', data_schema = data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return NetworkdOptionsFlow(entry)
