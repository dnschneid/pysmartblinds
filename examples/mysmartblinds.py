"""
HomeAssistant cover component for MySmartBlinds automated blind tilting

Place in .homeassistant/custom_components/cover/

Example configuration:
cover:
  - platform: mysmartblinds
    blinds:
      livingroom:
        friendly_name: Living Room Blinds
        mac: 12:34:56:78:9A:BC
        access_token: 123456789abcde

For more details about this platform, please refer to the documentation at
https://github.com/dnschneid/pysmartblinds
"""
import logging

import voluptuous as vol

from homeassistant.components.cover import (
    CoverDevice, PLATFORM_SCHEMA,
    SERVICE_TO_METHOD, SERVICE_SET_COVER_TILT_POSITION,
    SUPPORT_OPEN_TILT, SUPPORT_CLOSE_TILT, SUPPORT_STOP_TILT,
    SUPPORT_SET_TILT_POSITION, ATTR_TILT_POSITION)
from homeassistant.const import (
    CONF_ACCESS_TOKEN, CONF_FRIENDLY_NAME, CONF_MAC)
import homeassistant.helpers.config_validation as cv

from pysmartblinds import Blind

_LOGGER = logging.getLogger(__name__)

CONF_BLINDS = 'blinds'
MAC_REGEX = '^([0-9a-fA-F]{2}(:|$)){6}$'
TOKEN_REGEX = '^[0-9a-fA-F]{14}$'

ATTR_TRANSITION = 'transition'

TILT_FEATURES = (SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_STOP_TILT |
                 SUPPORT_SET_TILT_POSITION)

BLIND_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC): cv.matches_regex(MAC_REGEX),
    vol.Required(CONF_ACCESS_TOKEN): cv.matches_regex(TOKEN_REGEX),
    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_BLINDS): vol.Schema({cv.slug: BLIND_SCHEMA}),
})

SERVICE_TO_METHOD[SERVICE_SET_COVER_TILT_POSITION]['schema'] = (
    SERVICE_TO_METHOD[SERVICE_SET_COVER_TILT_POSITION]['schema'].extend({
        vol.Optional(ATTR_TRANSITION):
            vol.All(vol.Coerce(float), vol.Range(min=0)),
    })
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the blind."""
    blinds = []

    for device, device_config in config[CONF_BLINDS].items():
        friendly_name = device_config.get(CONF_FRIENDLY_NAME, device)
        mac = device_config.get(CONF_MAC)[:17]
        token = device_config.get(CONF_ACCESS_TOKEN)
        token = tuple(int(token[i*2:i*2+2], 16) for i in range(7))

        blinds.append(
            CoverMySmartBlinds(
                hass,
                device, friendly_name,
                mac, token
            )
        )
    if not blinds:
        _LOGGER.error("No blinds added")
        return False
    elif len(blinds) > 1:
        _LOGGER.warning("Currently, only one blind can be used at a time")

    add_devices(blinds)
    return True


class CoverMySmartBlinds(CoverDevice):
    """Representation of a MySmartBlinds cover."""

    def __init__(self, hass, device_id, friendly_name, mac, access_token):
        """Initialize the MySmartBlinds cover."""
        self.hass = hass
        self._name = friendly_name
        self._blind = Blind(mac, access_token)
        self._blind.pos(200)
        self._blind.set_callback(self.schedule_update_ha_state)

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def is_closed(self):
        """Return the closed state. We define that as minimum sun passage."""
        return self._blind.pos() == 200

    @property
    def is_opening(self):
        """Return true if the cover is opening."""
        return self._blind.dir() < 0

    @property
    def is_closing(self):
        """Return true if the cover is closing."""
        return self._blind.dir() > 0

    @property
    def current_cover_tilt_position(self):
        """Return current position of cover tilt.

        None is unknown, 0 is closed, 100 is fully open.
        """
        return int(100 - self._blind.pos() / 2)

    @property
    def supported_features(self):
        """Flag supported features."""
        return (SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_STOP_TILT |
                SUPPORT_SET_TILT_POSITION)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    def open_cover_tilt(self, **kwargs):
        """Tilt the cover open. We define that as tilting down."""
        self._blind.down()

    def close_cover_tilt(self, **kwargs):
        """Tilt the cover closed. We define that as tilting up."""
        self._blind.up()

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover tilting."""
        self._blind.stop()

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        self._blind.pos(200 - kwargs[ATTR_TILT_POSITION] * 2,
                        kwargs.get(ATTR_TRANSITION, 0))
