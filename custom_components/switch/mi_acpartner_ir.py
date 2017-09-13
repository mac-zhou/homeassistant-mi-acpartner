"""
Support Mi ACpartner IR.

Thank rytilahti for his great work
"""
import logging
from datetime import timedelta
import asyncio
from random import randint
import voluptuous as vol

import homeassistant.loader as loader
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_SWITCHES,
                                 CONF_COMMAND_OFF, CONF_COMMAND_ON,
                                 CONF_TIMEOUT, CONF_HOST, CONF_TOKEN,
                                 CONF_TYPE, CONF_NAME)
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utcnow

REQUIREMENTS = ['python-miio==0.0.11']

_LOGGER = logging.getLogger(__name__)

DEVICE_DEFAULT_NAME = 'mi_acpartner_ir'
SWITCH_DEFAULT_NAME = 'mi_acpartner_ir_switch'
DOMAIN = "mi_acpartner_ir"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3
SERVICE_LEARN = "learn_command"
SERVICE_SEND = "send_packet"

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_COMMAND_OFF, default=None): cv.string,
    vol.Optional(CONF_COMMAND_ON, default=None): cv.string,
    vol.Optional(CONF_NAME, default=SWITCH_DEFAULT_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA}),
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the smart mi fan platform."""
    import miio
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    devices = config.get(CONF_SWITCHES, {})
    persistent_notification = loader.get_component('persistent_notification')

    @asyncio.coroutine
    def _learn_command(call):
        ir_remote = miio.device(host, token)
        if not ir_remote:
            _LOGGER.error("Failed to connect to device.")
            return

        # key = randint(1,1000000)

        # ir_remote.send("miIO.ir_learn", {'key': str(key)})

        _LOGGER.info("Press the key you want HASS to learn")
        start_time = utcnow()
        while (utcnow() - start_time) < timedelta(seconds=DEFAULT_TIMEOUT):
            res = ir_remote.send('get_ir_learn_result', [])
            _LOGGER.error(type(res["code"]))
            _LOGGER.error(res["code"])
            if res["code"]:
                log_msg = 'Recieved packet is: %s' % res["code"]
                _LOGGER.info(log_msg)
                persistent_notification.async_create(hass, log_msg,
                                                     title='Mi_ACpartner switch')
                return
            yield from asyncio.sleep(1, loop=hass.loop)
        _LOGGER.error('Did not received any signal.')
        persistent_notification.async_create(hass,
                                             "Did not received any signal",
                                             title='Mi_ACpartner switch')

    @asyncio.coroutine
    def _send_packet(call):
        ir_remote = miio.device(host, token)
        if not ir_remote:
            _LOGGER.error("Failed to connect to device.")
            return

        packets = call.data.get('packet', [])
        for packet in packets:
            for retry in range(DEFAULT_RETRY):
                try:
                    ir_remote.send('send_ir_code', [str(packet)])
                    break
                except ValueError:
                    _LOGGER.error("Failed to send packet to device.")

    ir_remote = miio.device(host, token)
    if not ir_remote:
        _LOGGER.error("Failed to connect to device.")

    hass.services.register(DOMAIN, SERVICE_LEARN + '_' +
                            host.replace('.', '_'), _learn_command)
    hass.services.register(DOMAIN, SERVICE_SEND + '_' +
                            host.replace('.', '_'), _send_packet)
    switches = []
    for object_id, device_config in devices.items():
        switches.append(
            ChuangmiIRSwitch(
                ir_remote,
                device_config.get(CONF_NAME, object_id),
                device_config.get(CONF_COMMAND_ON),
                device_config.get(CONF_COMMAND_OFF)
            )
        )

    add_devices(switches)

class ChuangmiIRSwitch(SwitchDevice):
    """Representation of an Chuangmi switch."""

    def __init__(self, device, name, command_on, command_off):
        """Initialize the switch."""
        self._name = name
        self._state = False
        self._command_on = command_on or None
        self._command_off = command_off or None
        self._device = device

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._sendpacket(self._command_on):
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._sendpacket(self._command_off):
            self._state = False
            self.schedule_update_ha_state()

    def _sendpacket(self, packet):
        """Send packet to device."""
        if packet is None:
            _LOGGER.debug("Empty packet.")
            return True
        try:
            self._device.send('send_ir_code', [str(packet)])
            _LOGGER.info(str(packet))
        except ValueError as error:
            _LOGGER.error(error)
            return False
        return True
