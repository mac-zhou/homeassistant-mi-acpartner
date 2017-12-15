"""
Support SmartMi acpartner.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.xiaomi_miio
"""
import logging
import asyncio
from datetime import timedelta
import voluptuous as vol

from homeassistant.core import callback
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateDevice, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW)
from homeassistant.const import (
    TEMP_CELSIUS, ATTR_TEMPERATURE, ATTR_UNIT_OF_MEASUREMENT,
    CONF_NAME, CONF_HOST, CONF_TOKEN, CONF_TIMEOUT)
# from homeassistant.helpers import condition
from homeassistant.helpers.event import (
    async_track_state_change, async_track_time_interval)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['python-miio==0.3.2']
_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['sensor']

DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = 'Mi ACpartner'

DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3

DEFAULT_MIN_TMEP = 16
DEFAULT_MAX_TMEP = 30
DEFAULT_STEP = 1

CONF_SENSOR = 'target_sensor'
# CONF_TARGET_TEMP = 'target_temp'
CONF_SYNC = 'sync'
CONF_CUSTOMIZE = 'customize'

__Presets__ = {
    "default": {
        "description": "The Default Replacement of AC Partner",
        "defaultMain": "AC model(10)+po+mo+wi+sw+tt",
        "VALUE": ["po", "mo", "wi", "sw", "tt", "li"],
        "po": {
            "type": "switch",
            "on": "1",
            "off": "0"
        },
        "mo": {
            "heater": "0",
            "cooler": "1",
            "auto": "2",
            "dehum": "3",
            "airSup": "4"
        },
        "wi": {
            "auto": "3",
            "1": "0",
            "2": "1",
            "3": "2"
        },
        "sw": {
            "on": "0",
            "off": "1"
        },
        "tt": "1",
        "li": {
            "off": "a0"
        }
    },
    "0180111111": {
        "des": "media_1",
        "main": "0180111111pomowiswtt02"
    },
    "0180222221": {
        "des": "gree_1",
        "main": "0180222221pomowiswtt02"
    },
    "0100010727": {
        "des": "gree_2",
        "main": "0100010727pomowiswtt1100190t0t20500\
                2102000t6t0190t0t207002000000t4wt0",
        "off": "010001072701011101004000205002112000\
                D04000207002000000A0",
        "EXTRA_VALUE": ["t0t", "t6t", "t4wt"],
        "t0t": "1",
        "t6t": "7",
        "t4wt": "4"
    },
    "0100004795": {
        "des": "gree_8",
        "main": "0100004795pomowiswtt0100090900005002"
    },
    "0180333331": {
        "des": "haier_1",
        "main": "0180333331pomowiswtt12"
    },
    "0180666661": {
        "des": "aux_1",
        "main": "0180666661pomowiswtt12"
    },
    "0180777771": {
        "des": "chigo_1",
        "main": "0180777771pomowiswtt12"
    }
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Required(CONF_SENSOR, default=None): cv.entity_id,
    vol.Optional(CONF_CUSTOMIZE, default=None): dict,
    vol.Optional(CONF_SYNC, default=15): cv.positive_int
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Set up the smart mi acpartner platform."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME) or DEFAULT_NAME
    token = config.get(CONF_TOKEN)
    sensor_entity_id = config.get(CONF_SENSOR)
    # target_temp = config.get(CONF_TARGET_TEMP)
    sync = config.get(CONF_SYNC)
    customize = config.get(CONF_CUSTOMIZE)

    add_devices_callback([MiAcPartner(
        hass, name, None, None, None, 'auto', None,
        'off', 'off', None, DEFAULT_MAX_TMEP, DEFAULT_MIN_TMEP, host,
        token, sensor_entity_id, sync, customize)])


class ClimateStatus(ClimateDevice):
    """Container for status reports from the climate."""

    def __init__(self, data):
        self.data = data

    @property
    def acpower(self):
        """Get acpower from the climate."""
        return self.data[2]

    @property
    def acmodel(self):
        """Get acmodel from the climate."""
        return str(self.data[0][0:2] + self.data[0][8:16])

    @property
    def power(self):
        """Get power from the climate."""
        return self.data[1][2:3]

    @property
    def mode(self):
        """Get mode from the climate."""
        return self.data[1][3:4]

    @property
    def wind_force(self):
        """Get wind_force from the climate."""
        if self.data[1][4:5] == '0':
            return 'low'
        elif self.data[1][4:5] == '1':
            return 'medium'
        elif self.data[1][4:5] == '2':
            return 'high'
        return 'auto'

    @property
    def sweep(self):
        """Get sweep from the climate."""
        if self.data[1][5:6] == '0':
            return 'on'
        return 'off'

    @property
    def temp(self):
        """Get temp from the climate."""
        return int(self.data[1][6:8], 16)

    @property
    def operation(self):
        """Get operation from the climate."""
        if self.data[1][2:3] == '0':
            return 'off'
        else:
            if self.data[1][3:4] == '0':
                return 'heat'
            elif self.data[1][3:4] == '1':
                return 'cool'
            return 'auto'


class MiAcPartner(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, hass, name, target_humidity,
                 away, hold, current_fan_mode, current_humidity,
                 current_swing_mode, current_operation, aux,
                 target_temp_high, target_temp_low, host,
                 token, sensor_entity_id, sync, customize):
        """Initialize the climate device."""
        self.hass = hass
        self._name = name if name else DEFAULT_NAME
        self._target_humidity = target_humidity
        self._away = away
        self._hold = hold
        self.host = host
        self.token = token
        self.sync = sync
        self._customize = customize

        self._climate = None
        self._state = None
        self._state = self.climate_get_state()

        self._target_temperature = self._state.temp
        self._current_operation = self._state.operation

        self._current_humidity = current_humidity
        self._aux = aux
        self._operation_list = ['heat', 'cool', 'auto', 'off']

        if self._customize and ('fan' in self._customize):
            self._customize_fan_list = list(self._customize['fan'])
            self._fan_list = self._customize_fan_list
            self._current_fan_mode = 'idle'
        else:
            self._fan_list = ['low', 'medium', 'high', 'auto']
            self._current_fan_mode = self._state.wind_force

        if self._customize and ('swing' in self._customize):
            self._customize_swing_list = list(self._customize['swing'])
            self._swing_list = self._customize_swing_list
            self._current_swing_mode = 'idle'
        else:
            self._swing_list = ['on', 'off']
            self._current_swing_mode = self._state.sweep
        self._target_temperature_high = target_temp_high
        self._target_temperature_low = target_temp_low
        self._max_temp = target_temp_high + 1
        self._min_temp = target_temp_low - 1
        self._target_temp_step = DEFAULT_STEP

        self._unit_of_measurement = TEMP_CELSIUS
        self._current_temperature = None
        self._sensor_entity_id = sensor_entity_id

        if sensor_entity_id:
            async_track_state_change(
                hass, sensor_entity_id, self._async_sensor_changed)
            sensor_state = hass.states.get(sensor_entity_id)
            if sensor_state:
                self._async_update_temp(sensor_state)
        if sync:
            async_track_time_interval(
                hass, self._async_get_states, timedelta(seconds=self.sync))

    @callback
    def _async_update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        try:
            self._current_temperature = self.hass.config.units.temperature(
                float(state.state), unit)
        except ValueError as ex:
            _LOGGER.error('Unable to update from sensor: %s', ex)

    @asyncio.coroutine
    def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Handle temperature changes."""
        if new_state is None:
            return
        self._async_update_temp(new_state)
        # yield from self.async_update_ha_state()

    @asyncio.coroutine
    def _async_get_states(self, now=None):
        """Update the state of this climate device."""
        self.climate_get_state()
        self._current_operation = self._state.operation
        self._target_temperature = self._state.temp
        if (not self._customize) or (self._customize
                                     and 'fan' not in self._customize):
            self._current_fan_mode = self._state.wind_force
        if (not self._customize) or (self._customize
                                     and 'swing' not in self._customize):
            self._current_swing_mode = self._state.sweep
        if not self._sensor_entity_id:
            self._current_temperature = self._state.temp
        _LOGGER.info('Sync climate status, acmodel: %s, operation: %s,\
                     temperature: %s, fan: %s, swing: %s',
                     self._state.acmodel, self._state.operation,
                     self._state.temp, self._state.wind_force,
                     self._state.sweep)
        self.schedule_update_ha_state()

    @property
    def climate(self):
        """Set up the Xiaomi Mi Home Air Conditioner Companion platform."""
        from miio import AirConditioningCompanion
        if not self._climate:
            _LOGGER.info("initializing with host %s token %s",
                         self.host, self.token)
            self._climate = AirConditioningCompanion(self.host, self.token)
        return self._climate

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def target_temperature_step(self):
        """Return the target temperature step."""
        return self._target_temp_step

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self._target_temperature_low

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    @property
    def current_hold_mode(self):
        """Return hold mode setting."""
        return self._hold

    @property
    def is_aux_heat_on(self):
        """Return true if away mode is on."""
        return self._aux

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None and \
           kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)

        if self._target_temperature < self._target_temperature_low:
            self._current_operation = 'off'
            self._target_temperature = self._target_temperature_low
        elif self._target_temperature > self._target_temperature_high:
            self._current_operation = 'off'
            self._target_temperature = self._target_temperature_high
        elif self._current_temperature and (
                self._current_operation == "off" or
                self._current_operation == "idle"):
            self.set_operation_mode('auto')
            return

        self.sendcmd()
        self.schedule_update_ha_state()

    def set_humidity(self, humidity):
        """Set new target temperature."""
        self._target_humidity = humidity
        self.schedule_update_ha_state()

    def set_swing_mode(self, swing_mode):
        """Set new target temperature."""
        self._current_swing_mode = swing_mode
        if self._customize and ('swing' in self._customize):
            self._customize_sendcmd('swing')
        else:
            self.sendcmd()
        self.schedule_update_ha_state()

    def set_fan_mode(self, fan):
        """Set new target temperature."""
        self._current_fan_mode = fan
        if self._customize and ('fan' in self._customize):
            self._customize_sendcmd('fan')
        else:
            self.sendcmd()
        self.schedule_update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation = operation_mode
        self.sendcmd()
        self.schedule_update_ha_state()

    @property
    def current_swing_mode(self):
        """Return the swing setting."""
        return self._current_swing_mode

    @property
    def swing_list(self):
        """List of available swing modes."""
        return self._swing_list

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._away = True
        self.schedule_update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._away = False
        self.schedule_update_ha_state()

    def set_hold_mode(self, hold):
        """Update hold mode on."""
        self._hold = hold
        self.schedule_update_ha_state()

    def turn_aux_heat_on(self):
        """Turn away auxillary heater on."""
        self._aux = True
        self.schedule_update_ha_state()

    def turn_aux_heat_off(self):
        """Turn auxillary heater off."""
        self._aux = False
        self.schedule_update_ha_state()

    def climate_get_state(self):
        """get states from climate"""
        getstate = self.climate.send("get_model_and_state", [])
        _LOGGER.info(getstate)
        self._state = ClimateStatus(getstate)
        return self._state
