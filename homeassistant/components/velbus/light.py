"""Support for Velbus light."""
import logging

from velbus.util import VelbusException

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_FLASH,
    ATTR_TRANSITION,
    FLASH_LONG,
    FLASH_SHORT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_FLASH,
    SUPPORT_TRANSITION,
    Light,
)

from . import VelbusEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way."""
    pass


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Velbus light based on config_entry."""
    cntrl = hass.data[DOMAIN][entry.entry_id]["cntrl"]
    modules_data = hass.data[DOMAIN][entry.entry_id]["light"]
    entities = []
    for address, channel in modules_data:
        module = cntrl.get_module(address)
        entities.append(VelbusLight(module, channel))
    async_add_entities(entities)


class VelbusLight(VelbusEntity, Light):
    """Representation of a Velbus light."""

    @property
    def name(self):
        """Return the display name of this entity."""
        if self._module.light_is_buttonled(self._channel):
            return f"LED {self._module.get_name(self._channel)}"
        return self._module.get_name(self._channel)

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._module.light_is_buttonled(self._channel):
            return SUPPORT_FLASH
        return SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION

    @property
    def entity_registry_enabled_default(self):
        """Disable Button LEDs by default."""
        if self._module.light_is_buttonled(self._channel):
            return False
        return True

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._module.is_on(self._channel)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._module.get_dimmer_state(self._channel)

    def turn_on(self, **kwargs):
        """Instruct the Velbus light to turn on."""
        if self._module.light_is_buttonled(self._channel):
            if ATTR_FLASH in kwargs:
                if kwargs[ATTR_FLASH] == FLASH_LONG:
                    attr, *args = "set_led_state", self._channel, "slow"
                elif kwargs[ATTR_FLASH] == FLASH_SHORT:
                    attr, *args = "set_led_state", self._channel, "fast"
                else:
                    attr, *args = "set_led_state", self._channel, "on"
            else:
                attr, *args = "set_led_state", self._channel, "on"
        else:
            if ATTR_BRIGHTNESS in kwargs:
                attr, *args = (
                    "set_dimmer_state",
                    self._channel,
                    kwargs[ATTR_BRIGHTNESS],
                    kwargs.get(ATTR_TRANSITION, 0),
                )
            else:
                attr, *args = (
                    "restore_dimmer_state",
                    self._channel,
                    kwargs.get(ATTR_TRANSITION, 0),
                )
        try:
            getattr(self._module, attr)(*args)
        except VelbusException as err:
            _LOGGER.error("A Velbus error occurred: %s", err)

    def turn_off(self, **kwargs):
        """Instruct the velbus light to turn off."""
        if self._module.light_is_buttonled(self._channel):
            attr, *args = "set_led_state", self._channel, "off"
        else:
            attr, *args = (
                "set_dimmer_state",
                self._channel,
                0,
                kwargs.get(ATTR_TRANSITION, 0),
            )
        try:
            getattr(self._module, attr)(*args)
        except VelbusException as err:
            _LOGGER.error("A Velbus error occurred: %s", err)
