from homeassistant.config_entries import (ConfigEntry, ConfigEntryNotReady)
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up NodeMCU Climate from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "host": entry.data["host"],
        "name": entry.data["name"],
    }

    # Forward the entry to the climate platform
    try:
        # Forward the entry to the climate platform
        await hass.config_entries.async_forward_entry_setup(entry, "climate")
    except Exception as e:
        raise ConfigEntryNotReady(f"Error setting up climate platform: {e}")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "climate")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

