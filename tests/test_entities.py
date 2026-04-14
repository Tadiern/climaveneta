"""Tests for sensor and binary_sensor entity classes."""

import pytest
from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from custom_components.climaveneta.sensor import (
    ClimavenetaSensor,
    ClimavenetaSensorEntityDescription,
    ClimavenetaHvacStatusSensor,
    IMXW_SENSOR_TYPES,
    ILIFE2_SENSOR_TYPES,
    HVAC_STATUS_OPTIONS,
    HVAC_ACTION_TO_STRING,
)
from custom_components.climaveneta.binary_sensor import (
    ClimavenetaBinarySensor,
    ClimavenetaBinarySensorEntityDescription,
    IMXW_BINARY_SENSOR_TYPES,
    ILIFE2_BINARY_SENSOR_TYPES,
)
from custom_components.climaveneta.const import (
    CLIMAVENETA_EXCHANGER_TEMPERATURE,
    CLIMAVENETA_HVAC_STATUS,
    CLIMAVENETA_PUMP_RELAY,
    CLIMAVENETA_RELAY5_FAN_HIGH,
    CLIMAVENETA_CONTINUOUS_VENTILATION,
    CLIMAVENETA_MACHINE_SLAVE,
    CLIMAVENETA_WINDOW_INPUT,
    CLIMAVENETA_PUMP_ALARM_INPUT,
    CLIMAVENETA_HEATER_PRESENT,
    CLIMAVENETA_ANALOG_OUTPUT,
    CLIMAVENETA_ALARM_T1,
    CLIMAVENETA_ALARM_T2,
    CLIMAVENETA_ALARM_T3,
    CLIMAVENETA_ALARM_WATER_DRAIN,
    CLIMAVENETA_ALARM_COM,
)
from custom_components.climaveneta.pyclimaveneta import (
    CV_ACTION_OFF,
    CV_ACTION_IDLE,
    CV_ACTION_FAN,
    CV_ACTION_COOLING,
    CV_ACTION_HEATING,
)


def _mock_coordinator(device_type="imxw"):
    """Create a mock coordinator with data_readbacks."""
    coord = MagicMock()
    coord.hub = "/dev/ttyUSB0"
    coord.slave_id = 1
    coord.device_type = device_type
    coord.device_info = {
        "identifiers": {("climaveneta", "/dev/ttyUSB0_1")},
        "manufacturer": "Climaveneta",
        "name": "test",
        "model": "i-MXW" if device_type == "imxw" else "iLife",
        "sw_version": "1.06",
    }
    coord.data_readbacks = {}
    return coord


# ────────────────────────── Sensor type definitions ──────────────────────────

class TestSensorTypeDefinitions:
    """Verify sensor type tuples are correct."""

    def test_imxw_sensor_count(self):
        # water temp, 4 voltages, actual temp, 2 water temps, hysteresis,
        # dead zone center/range, t1 comp delta, offset ntc etn,
        # t2 probe temp, analog output = 15
        # (antistrat/t1 base params moved to number entities)
        assert len(IMXW_SENSOR_TYPES) == 15

    def test_ilife2_sensor_count(self):
        # actual temp, water temp, real setpoint, motor speed, max summer water,
        # min winter water, modbus address = 7
        assert len(ILIFE2_SENSOR_TYPES) == 7

    def test_imxw_binary_sensor_types(self):
        keys = [d.key for d in IMXW_BINARY_SENSOR_TYPES]
        assert CLIMAVENETA_PUMP_RELAY in keys
        assert CLIMAVENETA_RELAY5_FAN_HIGH in keys
        assert CLIMAVENETA_WINDOW_INPUT in keys
        assert CLIMAVENETA_PUMP_ALARM_INPUT in keys
        assert CLIMAVENETA_HEATER_PRESENT in keys
        assert CLIMAVENETA_CONTINUOUS_VENTILATION in keys
        assert CLIMAVENETA_MACHINE_SLAVE in keys
        assert CLIMAVENETA_ALARM_T1 in keys
        assert CLIMAVENETA_ALARM_T2 in keys
        assert CLIMAVENETA_ALARM_T3 in keys
        assert CLIMAVENETA_ALARM_WATER_DRAIN in keys
        assert len(IMXW_BINARY_SENSOR_TYPES) == 11

    def test_ilife2_binary_sensor_count(self):
        # pump relay + 12 alarm flags = 13
        assert len(ILIFE2_BINARY_SENSOR_TYPES) == 13

    def test_all_imxw_binary_sensors_diagnostic(self):
        for desc in IMXW_BINARY_SENSOR_TYPES:
            assert desc.entity_category == EntityCategory.DIAGNOSTIC

    def test_window_input_device_class(self):
        window = [d for d in IMXW_BINARY_SENSOR_TYPES if d.key == CLIMAVENETA_WINDOW_INPUT][0]
        assert window.device_class == BinarySensorDeviceClass.WINDOW

    def test_alarm_device_classes(self):
        alarm_keys = [
            CLIMAVENETA_PUMP_ALARM_INPUT,
            CLIMAVENETA_ALARM_T1,
            CLIMAVENETA_ALARM_T2,
            CLIMAVENETA_ALARM_T3,
            CLIMAVENETA_ALARM_WATER_DRAIN,
        ]
        for key in alarm_keys:
            desc = [d for d in IMXW_BINARY_SENSOR_TYPES if d.key == key][0]
            assert desc.device_class == BinarySensorDeviceClass.PROBLEM


# ────────────────────────── Sensor entity tests ──────────────────────────

class TestClimavenetaSensor:
    """Tests for ClimavenetaSensor entity."""

    def _make_sensor(self, key=CLIMAVENETA_EXCHANGER_TEMPERATURE):
        coord = _mock_coordinator()
        desc = ClimavenetaSensorEntityDescription(
            name="Test Sensor",
            key=key,
        )
        # Patch super().__init__ to avoid HA infrastructure
        with patch.object(ClimavenetaSensor, "__init__", lambda self, *a, **kw: None):
            sensor = ClimavenetaSensor.__new__(ClimavenetaSensor)
        sensor.coordinator = coord
        sensor.entity_description = desc
        sensor._state = 0.0
        sensor._attr_unique_id = f"{coord.hub}_{key}_{coord.slave_id}"
        sensor._attr_device_info = coord.device_info
        return sensor

    def test_native_value_with_data(self):
        sensor = self._make_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] = 25.3
        assert sensor.native_value == 25.3

    def test_native_value_missing_key(self):
        sensor = self._make_sensor()
        # data_readbacks is empty → KeyError → returns 0
        assert sensor.native_value == 0

    def test_async_update(self):
        sensor = self._make_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] = 30.0
        import asyncio
        asyncio.get_event_loop().run_until_complete(sensor.async_update())
        assert sensor._state == 30.0

    def test_async_update_missing_key(self):
        sensor = self._make_sensor()
        import asyncio
        asyncio.get_event_loop().run_until_complete(sensor.async_update())
        assert sensor._state == 0

    def test_handle_coordinator_update(self):
        sensor = self._make_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor.coordinator.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] = 28.5
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == 28.5
        sensor.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_missing_key(self):
        sensor = self._make_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value is None


# ────────────────────────── HVAC Status Sensor ──────────────────────────

class TestClimavenetaHvacStatusSensor:
    """Tests for ClimavenetaHvacStatusSensor entity."""

    def _make_hvac_sensor(self):
        coord = _mock_coordinator()
        with patch.object(ClimavenetaHvacStatusSensor, "__init__", lambda self, *a, **kw: None):
            sensor = ClimavenetaHvacStatusSensor.__new__(ClimavenetaHvacStatusSensor)
        sensor.coordinator = coord
        sensor._attr_name = "HVAC Status"
        sensor._attr_device_info = coord.device_info
        sensor._attr_unique_id = f"{coord.hub}_{CLIMAVENETA_HVAC_STATUS}_{coord.slave_id}"
        sensor._attr_device_class = SensorDeviceClass.ENUM
        sensor._attr_options = HVAC_STATUS_OPTIONS
        return sensor

    def test_native_value_off(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_OFF
        assert sensor.native_value == "off"

    def test_native_value_idle(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_IDLE
        assert sensor.native_value == "idle"

    def test_native_value_fan(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_FAN
        assert sensor.native_value == "fan"

    def test_native_value_cooling(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_COOLING
        assert sensor.native_value == "cooling"

    def test_native_value_heating(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_HEATING
        assert sensor.native_value == "heating"

    def test_native_value_missing_key(self):
        sensor = self._make_hvac_sensor()
        # empty data → default "off"
        assert sensor.native_value == "off"

    def test_native_value_unknown_action(self):
        sensor = self._make_hvac_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = 99
        assert sensor.native_value == "off"

    def test_handle_coordinator_update_heating(self):
        sensor = self._make_hvac_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS] = CV_ACTION_HEATING
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == "heating"
        sensor.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_missing(self):
        sensor = self._make_hvac_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor._handle_coordinator_update()
        assert sensor._attr_native_value == "off"

    def test_hvac_status_options(self):
        assert HVAC_STATUS_OPTIONS == ["off", "idle", "fan", "cooling", "heating"]

    def test_hvac_action_to_string_mapping(self):
        assert HVAC_ACTION_TO_STRING[CV_ACTION_OFF] == "off"
        assert HVAC_ACTION_TO_STRING[CV_ACTION_IDLE] == "idle"
        assert HVAC_ACTION_TO_STRING[CV_ACTION_FAN] == "fan"
        assert HVAC_ACTION_TO_STRING[CV_ACTION_COOLING] == "cooling"
        assert HVAC_ACTION_TO_STRING[CV_ACTION_HEATING] == "heating"


# ────────────────────────── Binary Sensor entity tests ──────────────────────────

class TestClimavenetaBinarySensor:
    """Tests for ClimavenetaBinarySensor entity."""

    def _make_binary_sensor(self, key=CLIMAVENETA_PUMP_RELAY, device_class=BinarySensorDeviceClass.POWER):
        coord = _mock_coordinator()
        desc = ClimavenetaBinarySensorEntityDescription(
            name="Test Binary Sensor",
            key=key,
            device_class=device_class,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        with patch.object(ClimavenetaBinarySensor, "__init__", lambda self, *a, **kw: None):
            sensor = ClimavenetaBinarySensor.__new__(ClimavenetaBinarySensor)
        sensor.coordinator = coord
        sensor.entity_description = desc
        sensor._attr_is_on = False
        sensor._attr_unique_id = f"{coord.hub}_{key}_{coord.slave_id}"
        sensor._attr_device_info = coord.device_info
        return sensor

    def test_is_on_true(self):
        sensor = self._make_binary_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = True
        assert sensor.is_on is True

    def test_is_on_false(self):
        sensor = self._make_binary_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = False
        assert sensor.is_on is False

    def test_is_on_missing_key(self):
        sensor = self._make_binary_sensor()
        assert sensor.is_on is False

    def test_is_on_integer_truthy(self):
        sensor = self._make_binary_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = 1
        assert sensor.is_on is True

    def test_is_on_integer_falsy(self):
        sensor = self._make_binary_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = 0
        assert sensor.is_on is False

    def test_async_update(self):
        sensor = self._make_binary_sensor()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = True
        import asyncio
        asyncio.get_event_loop().run_until_complete(sensor.async_update())
        assert sensor._attr_is_on is True

    def test_async_update_missing_key(self):
        sensor = self._make_binary_sensor()
        import asyncio
        asyncio.get_event_loop().run_until_complete(sensor.async_update())
        assert sensor._attr_is_on is False

    def test_handle_coordinator_update(self):
        sensor = self._make_binary_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor.coordinator.data_readbacks[CLIMAVENETA_PUMP_RELAY] = True
        sensor._handle_coordinator_update()
        assert sensor._attr_is_on is True
        sensor.async_write_ha_state.assert_called_once()

    def test_handle_coordinator_update_missing(self):
        sensor = self._make_binary_sensor()
        sensor.async_write_ha_state = MagicMock()
        sensor._handle_coordinator_update()
        assert sensor._attr_is_on is False

    def test_alarm_t3_binary_sensor(self):
        sensor = self._make_binary_sensor(
            key=CLIMAVENETA_ALARM_T3,
            device_class=BinarySensorDeviceClass.PROBLEM,
        )
        sensor.coordinator.data_readbacks[CLIMAVENETA_ALARM_T3] = True
        assert sensor.is_on is True

    def test_window_input_binary_sensor(self):
        sensor = self._make_binary_sensor(
            key=CLIMAVENETA_WINDOW_INPUT,
            device_class=BinarySensorDeviceClass.WINDOW,
        )
        sensor.coordinator.data_readbacks[CLIMAVENETA_WINDOW_INPUT] = True
        assert sensor.is_on is True


# ────────────────────────── Number entity tests ──────────────────────────

from custom_components.climaveneta.number import (
    ClimavenetaNumber,
    IMXW_NUMBER_TYPES,
    _SETTER_MAP,
    _GETTER_MAP,
)
from custom_components.climaveneta.const import (
    CLIMAVENETA_ANTISTRAT_WAIT_TIME,
    CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER,
    CLIMAVENETA_ANTISTRAT_TIME_SUMMER,
    CLIMAVENETA_T1_COMPENSATION_BASE_WINTER,
    CLIMAVENETA_ANTISTRAT_TIME_WINTER,
)


class TestNumberTypeDefinitions:
    """Verify number entity type tuples are correct."""

    def test_imxw_number_count(self):
        assert len(IMXW_NUMBER_TYPES) == 5

    def test_all_config_category(self):
        for desc in IMXW_NUMBER_TYPES:
            assert desc.entity_category == EntityCategory.CONFIG

    def test_setter_map_keys(self):
        for desc in IMXW_NUMBER_TYPES:
            assert desc.key in _SETTER_MAP

    def test_getter_map_keys(self):
        for desc in IMXW_NUMBER_TYPES:
            assert desc.key in _GETTER_MAP

    def test_antistrat_wait_time_range(self):
        desc = [d for d in IMXW_NUMBER_TYPES if d.key == CLIMAVENETA_ANTISTRAT_WAIT_TIME][0]
        assert desc.native_min_value == 10
        assert desc.native_max_value == 20
        assert desc.native_step == 1

    def test_t1_base_summer_range(self):
        desc = [d for d in IMXW_NUMBER_TYPES if d.key == CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER][0]
        assert desc.native_min_value == 0.5
        assert desc.native_max_value == 2.0
        assert desc.native_step == 0.1

    def test_antistrat_time_summer_range(self):
        desc = [d for d in IMXW_NUMBER_TYPES if d.key == CLIMAVENETA_ANTISTRAT_TIME_SUMMER][0]
        assert desc.native_min_value == 30
        assert desc.native_max_value == 180


class TestClimavenetaNumber:
    """Tests for ClimavenetaNumber entity."""

    def _make_number(self, key=CLIMAVENETA_ANTISTRAT_WAIT_TIME):
        coord = _mock_coordinator()
        desc = [d for d in IMXW_NUMBER_TYPES if d.key == key][0]
        with patch.object(ClimavenetaNumber, "__init__", lambda self, *a, **kw: None):
            entity = ClimavenetaNumber.__new__(ClimavenetaNumber)
        entity.coordinator = coord
        entity.entity_description = desc
        entity._attr_device_info = coord.device_info
        entity._attr_unique_id = f"{coord.hub}_{key}_{coord.slave_id}"
        return entity

    def test_native_value_with_data(self):
        entity = self._make_number()
        entity.coordinator.data_readbacks[CLIMAVENETA_ANTISTRAT_WAIT_TIME] = 15
        assert entity.native_value == 15

    def test_native_value_missing_key(self):
        entity = self._make_number()
        assert entity.native_value is None

    @pytest.mark.asyncio
    async def test_async_set_native_value(self):
        entity = self._make_number(CLIMAVENETA_ANTISTRAT_WAIT_TIME)
        entity.async_write_ha_state = MagicMock()
        mock_api = MagicMock()
        mock_api.set_antistrat_wait_time = MagicMock(return_value=True)
        mock_api.set_antistrat_wait_time = pytest.importorskip("asyncio").coroutine(
            lambda v: True
        ) if False else MagicMock()
        # Use AsyncMock
        from unittest.mock import AsyncMock
        mock_api.set_antistrat_wait_time = AsyncMock(return_value=True)
        mock_api.get_antistrat_wait_time = MagicMock(return_value=15)
        entity.coordinator.api = mock_api
        entity.coordinator.data_readbacks = {}
        await entity.async_set_native_value(15)
        mock_api.set_antistrat_wait_time.assert_called_once_with(15)
        assert entity.coordinator.data_readbacks[CLIMAVENETA_ANTISTRAT_WAIT_TIME] == 15

    def test_handle_coordinator_update(self):
        entity = self._make_number()
        entity.async_write_ha_state = MagicMock()
        entity._handle_coordinator_update()
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_write_failure(self):
        """When the modbus write fails, readback should not be updated."""
        from unittest.mock import AsyncMock
        entity = self._make_number(CLIMAVENETA_ANTISTRAT_WAIT_TIME)
        entity.async_write_ha_state = MagicMock()
        mock_api = MagicMock()
        mock_api.set_antistrat_wait_time = AsyncMock(return_value=False)
        entity.coordinator.api = mock_api
        entity.coordinator.data_readbacks = {}
        await entity.async_set_native_value(15)
        assert CLIMAVENETA_ANTISTRAT_WAIT_TIME not in entity.coordinator.data_readbacks
        entity.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_native_value_t1_base_summer(self):
        from unittest.mock import AsyncMock
        entity = self._make_number(CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER)
        entity.async_write_ha_state = MagicMock()
        mock_api = MagicMock()
        mock_api.set_t1_compensation_base_summer = AsyncMock(return_value=True)
        mock_api.get_t1_compensation_base_summer = MagicMock(return_value=1.5)
        entity.coordinator.api = mock_api
        entity.coordinator.data_readbacks = {}
        await entity.async_set_native_value(1.5)
        mock_api.set_t1_compensation_base_summer.assert_called_once_with(1.5)
        assert entity.coordinator.data_readbacks[CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER] == 1.5

    @pytest.mark.asyncio
    async def test_async_set_native_value_antistrat_time_winter(self):
        from unittest.mock import AsyncMock
        entity = self._make_number(CLIMAVENETA_ANTISTRAT_TIME_WINTER)
        entity.async_write_ha_state = MagicMock()
        mock_api = MagicMock()
        mock_api.set_antistrat_time_winter = AsyncMock(return_value=True)
        mock_api.get_antistrat_time_winter = MagicMock(return_value=120)
        entity.coordinator.api = mock_api
        entity.coordinator.data_readbacks = {}
        await entity.async_set_native_value(120)
        mock_api.set_antistrat_time_winter.assert_called_once_with(120)


# ────────────────────────── Number platform setup ──────────────────────────

from custom_components.climaveneta.number import async_setup_entry as number_setup_entry


class TestNumberSetup:
    """Tests for number.async_setup_entry."""

    @pytest.mark.asyncio
    async def test_setup_imxw_creates_entities(self):
        hass = MagicMock()
        coord = _mock_coordinator("imxw")
        hass.data = {"climaveneta": {"entry_id_1": coord}}
        entry = MagicMock()
        entry.entry_id = "entry_id_1"
        added = []
        await number_setup_entry(hass, entry, lambda entities: added.extend(entities))
        assert len(added) == 5

    @pytest.mark.asyncio
    async def test_setup_ilife2_creates_no_entities(self):
        hass = MagicMock()
        coord = _mock_coordinator("ilife2")
        hass.data = {"climaveneta": {"entry_id_1": coord}}
        entry = MagicMock()
        entry.entry_id = "entry_id_1"
        added = []
        await number_setup_entry(hass, entry, lambda entities: added.extend(entities))
        assert len(added) == 0
