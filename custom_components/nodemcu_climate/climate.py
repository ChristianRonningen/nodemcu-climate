import requests
import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
    SWING_OFF,
    SWING_BOTH,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.SWING_MODE

class NodeMCUClimate(ClimateEntity):
    """Representation of a NodeMCU Climate Device."""

    def __init__(self, name, host):
        """Initialize the climate entity."""
        self._name = name
        self._host = host
        self._hvac_mode = HVACMode.HEAT
        self._target_temperature = 22
        self._fan_mode = "High"
        self._swing_mode = "off"
        self._available = True
        self._current_temperature = None  # Cached temperature
        self._current_humidity = None  # Cached humidity
        self._target_temperature_step = 1

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def hvac_modes(self):
        """Return the list of supported HVAC modes."""
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL]

    @property
    def swing_modes(self):
        return [SWING_OFF, SWING_BOTH, SWING_VERTICAL, SWING_HORIZONTAL]

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def target_temperature_step(self):
        return self._target_temperature_step

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def target_temperature(self):
        """Return the current target temperature."""
        return self._target_temperature

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return ["Low", "Medium", "High", "Auto"]

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._fan_mode

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def swing_mode(self):
        """Return the current swing mode."""
        return self._swing_mode

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def current_humidity(self):
        """Return the cached humidity."""
        return self._current_humidity

    def turn_off(self):
        """Turn the entity off."""
        self._hvac_mode = HVACMode.OFF
        self._send_command("off", "")

    def turn_on(self):
        """Turn the entity on."""
        self._send_command("on", "")

    def set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        self._hvac_mode = hvac_mode
        self._send_command("mode", hvac_mode)

    def set_temperature(self, **kwargs):
        """Set the target temperature."""
        self._target_temperature = kwargs.get("temperature")
        self._send_command("temp", self._target_temperature)

    def set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        self._fan_mode = fan_mode
        self._send_command("fan", fan_mode)

    def set_swing_mode(self, swing_mode):
        self._swing_mode = swing_mode
        self._send_command("swing_mode", swing_mode)

    def _send_command(self, command, value):
        """Send a command to the NodeMCU."""
        try:
            url = f"http://{self._host}/send_ir"
            payload = {
                'command': command,
                'value': value
            }
            response = requests.post(url, data=payload)
            #response.raise_for_status()  # Raise an exception for HTTP errors
            self._available = True
        # Log response success
            if response.status_code == 200:
                _LOGGER.info(f"Successfully sent {command} with value {value} to {self._host}")
            else:
                _LOGGER.warning(f"Received unexpected status code {response.status_code} from {self._host}")

            # No impact on availability
        except requests.RequestException as e:
            # Log the error, but don't affect availability
            _LOGGER.error(f"Error sending {command} with value {value} to {self._host}: {e}")

    def update(self):
        """Fetch the latest temperature from the NodeMCU."""
        try:
            url = f"http://{self._host}/temp"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                self._current_temperature = data.get("temperature")
                self._current_humidity = data.get("humidity")
            else:
                _LOGGER.warning(f"Failed to fetch temperature and humidity: {response.status_code}")
        except requests.RequestException as e:
            _LOGGER.error(f"Error connecting to NodeMCU: {e}")

    @property
    def available(self):
        """Return True if the device is available."""
        return self._available


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Set up climate entities from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NodeMCUClimate(data["name"], data["host"])])
