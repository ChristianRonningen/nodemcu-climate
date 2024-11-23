import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.const import CONF_HOST, CONF_NAME
from .const import DOMAIN

class NodeMCUClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NodeMCU Climate integration."""

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle discovery via Zeroconf."""
        host = discovery_info.host
        name = discovery_info.name.removesuffix("._nodemcu-climate._tcp.local")

        # Extract MAC address from mDNS properties
        mac_address = discovery_info.properties.get("mac_address")

        if not mac_address:
            self._abort_if_unique_id_configured()  # Ensure no duplicates
            return self.async_abort(reason="no_mac_address")

        # Ensure the device isn't already added
        await self.async_set_unique_id(mac_address)
        self._abort_if_unique_id_configured()

        # Store data temporarily for later use in the next step
        self.context["host"] = host
        self.context["default_name"] = name

        # Prompt the user to confirm or change the name
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle user input for the custom name."""
        errors = {}

        if user_input is not None:
            # Validate user input and create a new entry
            host = self.context["host"]
            mac_address = self.unique_id  # Already set in zeroconf step
            name = user_input[CONF_NAME]

            return self.async_create_entry(
                title=name,
                data={CONF_HOST: host, CONF_NAME: name, "mac_address": mac_address},
            )

        # Default name from context
        default_name = self.context.get("default_name", "NodeMCU Climate")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=default_name): str,
            }),
            errors=errors,
        )
