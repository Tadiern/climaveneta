"""Tests for coordinator _async_update_data and entity classes."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from custom_components.climaveneta.coordinator import ClimavenetaCoordinator
from custom_components.climaveneta.const import (
    CLIMAVENETA_EXCHANGER_TEMPERATURE,
    CLIMAVENETA_FAN_SPEED_RPM,
    CLIMAVENETA_PUMP_RELAY,
    CLIMAVENETA_ACTUAL_TEMPERATURE,
    CLIMAVENETA_HVAC_STATUS,
    CLIMAVENETA_RELAY5_FAN_HIGH,
    CLIMAVENETA_WINDOW_INPUT,
    CLIMAVENETA_PUMP_ALARM_INPUT,
    CLIMAVENETA_HEATER_PRESENT,
    CLIMAVENETA_ANALOG_OUTPUT,
    CLIMAVENETA_ALARM_T1,
    CLIMAVENETA_ALARM_T2,
    CLIMAVENETA_ALARM_T3,
    CLIMAVENETA_ALARM_WATER_DRAIN,
    CLIMAVENETA_CONTINUOUS_VENTILATION,
    CLIMAVENETA_MACHINE_SLAVE,
    CLIMAVENETA_REAL_SETPOINT,
    CLIMAVENETA_MOTOR_SPEED_SET,
    CLIMAVENETA_ALARM_COM,
    CLIMAVENETA_ALARM_AIR,
    CLIMAVENETA_ALARM_H4,
    CLIMAVENETA_ALARM_ACQ_DAN,
    CLIMAVENETA_ALARM_H2,
    CLIMAVENETA_ALARM_H4_NID,
    CLIMAVENETA_ALARM_HI_RES,
    CLIMAVENETA_ALARM_MOT,
    CLIMAVENETA_ALARM_GRID,
    CLIMAVENETA_ALARM_H2_NID,
    CLIMAVENETA_ALARM_FILTRO,
    CLIMAVENETA_ALARM_2AIR_M5,
    CLIMAVENETA_SETPOINT_HYSTERESIS,
    CLIMAVENETA_ANTISTRAT_WAIT_TIME,
    CLIMAVENETA_MODBUS_ADDRESS,
    CLIMAVENETA_T2_TEMPERATURE,
    CLIMAVENETA_OFFSET_NTC_ETN,
    DOMAIN,
)


def _make_mock_api():
    """Create a fully mocked ClimavenetaAPI with all getters."""
    mock_api = MagicMock()
    mock_api.async_read_configuration = AsyncMock()
    mock_api.async_update = AsyncMock()
    mock_api.try_initial_communication = AsyncMock()
    mock_api.get_min_voltage_winter = MagicMock(return_value=2.0)
    mock_api.get_max_voltage_winter = MagicMock(return_value=9.0)
    mock_api.get_min_voltage_summer = MagicMock(return_value=1.5)
    mock_api.get_max_voltage_summer = MagicMock(return_value=8.5)
    mock_api.get_max_water_temp_summer = MagicMock(return_value=18.0)
    mock_api.get_min_water_temp_winter = MagicMock(return_value=35.0)
    mock_api.get_modbus_address = MagicMock(return_value=1)
    mock_api.get_firmware_version = MagicMock(return_value="1.06")
    mock_api.get_setpoint_hysteresis = MagicMock(return_value=0.5)
    mock_api.get_dead_zone_center = MagicMock(return_value=22.0)
    mock_api.get_dead_zone_range = MagicMock(return_value=2.0)
    mock_api.get_t1_compensation_delta = MagicMock(return_value=1.0)
    mock_api.get_antistrat_wait_time = MagicMock(return_value=15)
    mock_api.get_t1_compensation_base_summer = MagicMock(return_value=1.0)
    mock_api.get_antistrat_time_summer = MagicMock(return_value=60)
    mock_api.get_t1_compensation_base_winter = MagicMock(return_value=2.0)
    mock_api.get_antistrat_time_winter = MagicMock(return_value=90)
    mock_api.get_offset_ntc_etn = MagicMock(return_value=0.5)
    mock_api.get_t2_temperature = MagicMock(return_value=23.5)
    mock_api.get_continuous_ventilation = MagicMock(return_value=True)
    mock_api.get_machine_slave = MagicMock(return_value=False)
    mock_api.get_exchanger_temperature = MagicMock(return_value=25.0)
    mock_api.get_fan_speed_rpm = MagicMock(return_value=800)
    mock_api.get_boiler_water_relay_on_off = MagicMock(return_value=True)
    mock_api.get_current_temp = MagicMock(return_value=21.5)
    mock_api.get_target_temp = MagicMock(return_value=22.0)
    mock_api.get_hvac_action = MagicMock(return_value=4)  # HEATING
    mock_api.get_relay5_fan_high = MagicMock(return_value=True)
    mock_api.get_window_input = MagicMock(return_value=False)
    mock_api.get_pump_alarm_input = MagicMock(return_value=False)
    mock_api.get_heater_present = MagicMock(return_value=True)
    mock_api.get_analog_output = MagicMock(return_value=5.5)
    mock_api.get_alarm_t1 = MagicMock(return_value=False)
    mock_api.get_alarm_t2 = MagicMock(return_value=False)
    mock_api.get_alarm_t3 = MagicMock(return_value=True)
    mock_api.get_alarm_water_drain = MagicMock(return_value=False)
    mock_api.get_alarm_flag = MagicMock(return_value=False)
    return mock_api


def _make_coordinator(hass, device_type, mock_api, mocker):
    """Create a coordinator with mocked dependencies."""
    mocker.patch(
        "custom_components.climaveneta.pyclimaveneta.ClimavenetaAPI",
        return_value=mock_api,
    )
    mocker.patch(
        "custom_components.climaveneta.coordinator.ModbusSerialClient",
        return_value=MagicMock(),
    )
    mocker.patch(
        "homeassistant.helpers.frame.report_usage",
    )
    coord = ClimavenetaCoordinator(hass, device_type, "/dev/ttyUSB0", 1, "test")
    return coord


# ────────────────────────── Coordinator _async_update_data ──────────────────────────

@pytest.mark.asyncio
async def test_update_data_imxw(mocker):
    """Test _async_update_data populates all IMXW readbacks."""
    hass = MagicMock()
    mock_api = _make_mock_api()
    coord = _make_coordinator(hass, "imxw", mock_api, mocker)
    await coord.async_create()

    # Run the periodic update
    await coord._async_update_data()

    # Common readbacks
    assert coord.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] == 25.0
    assert coord.data_readbacks[CLIMAVENETA_FAN_SPEED_RPM] == 800
    assert coord.data_readbacks[CLIMAVENETA_PUMP_RELAY] is True
    assert coord.data_readbacks[CLIMAVENETA_ACTUAL_TEMPERATURE] == 21.5
    assert coord.data_readbacks[CLIMAVENETA_HVAC_STATUS] == 4

    # iMXW diagnostic readbacks
    assert coord.data_readbacks[CLIMAVENETA_RELAY5_FAN_HIGH] is True
    assert coord.data_readbacks[CLIMAVENETA_WINDOW_INPUT] is False
    assert coord.data_readbacks[CLIMAVENETA_PUMP_ALARM_INPUT] is False
    assert coord.data_readbacks[CLIMAVENETA_HEATER_PRESENT] is True
    assert coord.data_readbacks[CLIMAVENETA_ANALOG_OUTPUT] == 5.5
    assert coord.data_readbacks[CLIMAVENETA_ALARM_T1] is False
    assert coord.data_readbacks[CLIMAVENETA_ALARM_T2] is False
    assert coord.data_readbacks[CLIMAVENETA_ALARM_T3] is True
    assert coord.data_readbacks[CLIMAVENETA_ALARM_WATER_DRAIN] is False

    # iMXW config readbacks (from async_create)
    assert coord.data_readbacks[CLIMAVENETA_CONTINUOUS_VENTILATION] is True
    assert coord.data_readbacks[CLIMAVENETA_MACHINE_SLAVE] is False
    assert coord.data_readbacks[CLIMAVENETA_OFFSET_NTC_ETN] == 0.5

    # iMXW T2 probe readback
    assert coord.data_readbacks[CLIMAVENETA_T2_TEMPERATURE] == 23.5

    # iLife2-only keys should NOT be present
    assert CLIMAVENETA_REAL_SETPOINT not in coord.data_readbacks
    assert CLIMAVENETA_ALARM_COM not in coord.data_readbacks


@pytest.mark.asyncio
async def test_update_data_ilife2(mocker):
    """Test _async_update_data populates all iLife2 readbacks."""
    hass = MagicMock()
    mock_api = _make_mock_api()
    coord = _make_coordinator(hass, "ilife2", mock_api, mocker)
    await coord.async_create()

    await coord._async_update_data()

    # Common readbacks
    assert coord.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] == 25.0
    assert coord.data_readbacks[CLIMAVENETA_PUMP_RELAY] is True
    assert coord.data_readbacks[CLIMAVENETA_HVAC_STATUS] == 4

    # iLife2-only readbacks
    assert coord.data_readbacks[CLIMAVENETA_REAL_SETPOINT] == 22.0
    assert coord.data_readbacks[CLIMAVENETA_MOTOR_SPEED_SET] == 800

    # iLife2 alarm flags
    assert coord.data_readbacks[CLIMAVENETA_ALARM_COM] is False
    assert coord.data_readbacks[CLIMAVENETA_ALARM_AIR] is False
    assert coord.data_readbacks[CLIMAVENETA_ALARM_FILTRO] is False

    # T2 probe should NOT be present for iLife2
    assert CLIMAVENETA_T2_TEMPERATURE not in coord.data_readbacks
    assert CLIMAVENETA_OFFSET_NTC_ETN not in coord.data_readbacks
    assert coord.data_readbacks[CLIMAVENETA_ALARM_2AIR_M5] is False

    # iMXW-only keys should NOT be present
    assert CLIMAVENETA_RELAY5_FAN_HIGH not in coord.data_readbacks
    assert CLIMAVENETA_CONTINUOUS_VENTILATION not in coord.data_readbacks


@pytest.mark.asyncio
async def test_async_create_imxw_dip_readbacks(mocker):
    """Verify dip switch readbacks are populated after async_create."""
    hass = MagicMock()
    mock_api = _make_mock_api()
    coord = _make_coordinator(hass, "imxw", mock_api, mocker)
    await coord.async_create()

    assert coord.data_readbacks[CLIMAVENETA_CONTINUOUS_VENTILATION] is True
    assert coord.data_readbacks[CLIMAVENETA_MACHINE_SLAVE] is False


@pytest.mark.asyncio
async def test_async_create_ilife2_no_imxw_config(mocker):
    """Verify iLife2 coordinator does not have IMXW config readbacks."""
    hass = MagicMock()
    mock_api = _make_mock_api()
    coord = _make_coordinator(hass, "ilife2", mock_api, mocker)
    await coord.async_create()

    assert CLIMAVENETA_SETPOINT_HYSTERESIS not in coord.data_readbacks
    assert CLIMAVENETA_CONTINUOUS_VENTILATION not in coord.data_readbacks
    assert coord.data_readbacks[CLIMAVENETA_MODBUS_ADDRESS] == 1


@pytest.mark.asyncio
async def test_coordinator_device_info_updated(mocker):
    """Verify firmware version is set in device_info after async_create."""
    hass = MagicMock()
    mock_api = _make_mock_api()
    coord = _make_coordinator(hass, "imxw", mock_api, mocker)
    await coord.async_create()

    assert coord.device_info["sw_version"] == "1.06"
