import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.climaveneta.coordinator import ClimavenetaCoordinator


def _make_mock_api():
    """Create a fully mocked ClimavenetaAPI."""
    mock_api = MagicMock()
    mock_api.async_read_configuration = AsyncMock()
    mock_api.async_update = AsyncMock()
    mock_api.try_initial_communication = AsyncMock()
    mock_api.get_min_voltage_winter = MagicMock(return_value=0.0)
    mock_api.get_max_voltage_winter = MagicMock(return_value=0.0)
    mock_api.get_min_voltage_summer = MagicMock(return_value=0.0)
    mock_api.get_max_voltage_summer = MagicMock(return_value=0.0)
    mock_api.get_max_water_temp_summer = MagicMock(return_value=0.0)
    mock_api.get_min_water_temp_winter = MagicMock(return_value=0.0)
    mock_api.get_modbus_address = MagicMock(return_value=1)
    mock_api.get_firmware_version = MagicMock(return_value="1.00")
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
    mock_api.get_t2_temperature = MagicMock(return_value=None)
    mock_api.get_exchanger_temperature = MagicMock(return_value=25.0)
    mock_api.get_fan_speed_rpm = MagicMock(return_value=800)
    mock_api.get_boiler_water_relay_on_off = MagicMock(return_value=False)
    mock_api.get_current_temp = MagicMock(return_value=21.5)
    mock_api.get_target_temp = MagicMock(return_value=22.0)
    mock_api.get_alarm_flag = MagicMock(return_value=False)
    return mock_api


@pytest.mark.asyncio
async def test_async_create_imxw(mocker):
    """Test coordinator creation for an IMXW device."""
    hass = MagicMock()
    mock_api = _make_mock_api()
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

    coord = ClimavenetaCoordinator(hass, "imxw", "/dev/ttyUSB0", 1, "test")
    await coord.async_create()

    assert hasattr(coord, "api")
    mock_api.async_read_configuration.assert_awaited_once()
    assert coord.data_readbacks["setpoint_hysteresis"] == 0.5
    assert coord.data_readbacks["antistrat_wait_time"] == 15


@pytest.mark.asyncio
async def test_async_create_ilife2(mocker):
    """Test coordinator creation for an iLife2 device."""
    hass = MagicMock()
    mock_api = _make_mock_api()
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

    coord = ClimavenetaCoordinator(hass, "ilife2", "/dev/ttyUSB0", 2, "test_ilife")
    await coord.async_create()

    assert hasattr(coord, "api")
    mock_api.async_read_configuration.assert_awaited_once()
    assert coord.data_readbacks["modbus_address"] == 1
    # IMXW-only keys should NOT be present for iLife2
    assert "setpoint_hysteresis" not in coord.data_readbacks
