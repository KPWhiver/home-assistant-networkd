import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_INTERFACE, LOGGER
from .common import create_networkd_state, destroy_networkd_state


DATA_SCHEMA = vol.Schema({vol.Required(CONF_INTERFACE): str})


class NetworkdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input = None):
        if user_input is None:
            return self.async_show_form(step_id='user', data_schema = DATA_SCHEMA)

        interface_name = user_input.get(CONF_INTERFACE)

        await self.async_set_unique_id(interface_name)
        self._abort_if_unique_id_configured()

        errors = {}
        try:
            networkd_state = await create_networkd_state()
        except:
            errors['base'] = 'connection_failed'
        else:
            try:
                interface = await networkd_state.manager.call_get_link_by_name(interface_name)
            except:
                errors['base'] = 'interface_not_found'
            else:
                link_introspection = await networkd_state.bus.introspect('org.freedesktop.network1', interface[1])
                link_obj = networkd_state.bus.get_proxy_object('org.freedesktop.network1', interface[1], link_introspection)
                try:
                    link_obj.get_interface('org.freedesktop.network1.DHCPServer')
                except:
                    errors['base'] = 'no_dhcp_server'
            finally:
                await destroy_networkd_state(networkd_state)

        if errors != {}:
            return self.async_show_form(step_id='user', data_schema = DATA_SCHEMA, errors=errors)

        return self.async_create_entry(title = interface_name, data = user_input)
