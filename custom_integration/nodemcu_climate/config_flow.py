import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.const import CONF_HOST, CONF_NAME
from .const import DOMAIN

class NodeMCUClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NodeMCU Climate integration."""

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle discovery via Zeroconf and prompt for custom name."""
        host = discovery_info.host
        name = discovery_info.name.removesuffix("._nodemcu-climate._tcp.local")
        
        # Assuming you have MAC address available in the discovery_info
        # Example: discovery_info.properties["mac_address"] (you would need to adjust this based on your setup)
        mac_address = discovery_info.properties.get("mac_address", None)
        
        if mac_address is None:
            # If no MAC address is found, fall back to host IP or some other identifier
            mac_address = host

        # Check if the device is already configured
        existing_entry = await self.async_set_unique_id(mac_address)
        if existing_entry is not None:
            # Device is already added, abort discovery
            return self.async_abort(reason="already_configured")

        # Proceed with adding the device if not already configured
        return await self.async_step_name(host, name)
    
    async def async_step_name(self, host, name):
        """Ask user for custom name."""
        # Create a form that asks for a custom name
        return self.async_show_form(
            step_id="name",
            data_schema=self._get_name_schema(name),
            description_placeholders={"default_name": name},
        )

    def _get_name_schema(self, default_name):
        """Return the schema for the name input form."""
        return vol.Schema({
            vol.Required(CONF_NAME, default=default_name): str,
        })

    async def async_step_user(self, user_input=None):
        """Handle user input after the name is provided."""
        if user_input is not None:
            # The user has provided a name
            host = user_input[CONF_HOST]
            name = user_input[CONF_NAME]

            # Save the configuration entry with a unique id (host)
            self._set_unique_id(host)
            return self.async_create_entry(
                title=name,
                data={CONF_HOST: host, CONF_NAME: name}
            )
        
        # If no input yet, show the form again
        return self.async_show_form(step_id="user")
