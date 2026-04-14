import pytest
from unittest.mock import MagicMock

from custom_components.climaveneta import pyclimaveneta


def test_hex_to_custom_string():
    """Test hex-to-version string conversion."""
    s = pyclimaveneta.ClimavenetaAPI.__dict__.get(
        "_ClimavenetaAPI__hex_to_custom_string"
    )
    if s is None:
        pytest.skip("__hex_to_custom_string not exposed; unit test skipped")
    else:
        assert callable(s)
        out = s(0x0100)
        assert isinstance(out, str)
        assert "." in out


def _make_api(unit_type="imxw"):
    """Create a ClimavenetaAPI with mocked Modbus connection."""
    # Save and restore initialized state to avoid interference between tests
    orig_initialized = pyclimaveneta.ClimavenetaLock.initialized
    pyclimaveneta.ClimavenetaLock.initialized = True
    mock_port = MagicMock()
    pyclimaveneta.ClimavenetaLock.port = mock_port
    try:
        api = pyclimaveneta.ClimavenetaAPI(MagicMock(), 1, unit_type)
    finally:
        pyclimaveneta.ClimavenetaLock.initialized = orig_initialized
    return api


class TestClimavenetaAPIImxw:
    """Tests for i-MXW getter methods."""

    def test_get_current_temp(self):
        api = _make_api("imxw")
        api._data_modbus["current_temperature"] = 215
        assert api.get_current_temp() == 21.5

    def test_get_target_temp(self):
        api = _make_api("imxw")
        api._data_modbus["target_temperature"] = 220
        assert api.get_target_temp() == 22.0

    def test_get_exchanger_temperature(self):
        api = _make_api("imxw")
        api._data_modbus["exchanger_temperature"] = 350
        assert api.get_exchanger_temperature() == 35.0

    def test_voltage_getters(self):
        api = _make_api("imxw")
        api._data_modbus["min_voltage_winter"] = 30
        api._data_modbus["max_voltage_winter"] = 100
        api._data_modbus["min_voltage_summer"] = 20
        api._data_modbus["max_voltage_summer"] = 80
        assert api.get_min_voltage_winter() == 3.0
        assert api.get_max_voltage_winter() == 10.0
        assert api.get_min_voltage_summer() == 2.0
        assert api.get_max_voltage_summer() == 8.0

    def test_water_temp_getters(self):
        api = _make_api("imxw")
        api._data_modbus["max_water_temp_summer"] = 200
        api._data_modbus["min_water_temp_winter"] = 300
        assert api.get_max_water_temp_summer() == 20.0
        assert api.get_min_water_temp_winter() == 30.0

    def test_setpoint_hysteresis(self):
        api = _make_api("imxw")
        api._data_modbus["setpoint_hysteresis"] = 10
        assert api.get_setpoint_hysteresis() == 1.0

    def test_dead_zone_getters(self):
        api = _make_api("imxw")
        api._data_modbus["dead_zone_center"] = 220
        api._data_modbus["dead_zone_range"] = 30
        assert api.get_dead_zone_center() == 22.0
        assert api.get_dead_zone_range() == 3.0

    def test_t1_compensation_delta(self):
        api = _make_api("imxw")
        api._data_modbus["t1_compensation_delta"] = 15
        assert api.get_t1_compensation_delta() == 1.5

    def test_antistrat_getters(self):
        api = _make_api("imxw")
        api._data_modbus["antistrat_wait_time"] = 15
        api._data_modbus["t1_compensation_base_summer"] = 10
        api._data_modbus["antistrat_time_summer"] = 120
        api._data_modbus["t1_compensation_base_winter"] = 30
        api._data_modbus["antistrat_time_winter"] = 180
        assert api.get_antistrat_wait_time() == 15
        assert api.get_t1_compensation_base_summer() == 1.0
        assert api.get_antistrat_time_summer() == 120
        assert api.get_t1_compensation_base_winter() == 3.0
        assert api.get_antistrat_time_winter() == 180

    def test_offset_ntc_etn_positive(self):
        api = _make_api("imxw")
        api._data_modbus["offset_ntc_etn"] = 15
        assert api.get_offset_ntc_etn() == 1.5

    def test_offset_ntc_etn_negative(self):
        api = _make_api("imxw")
        api._data_modbus["offset_ntc_etn"] = -20
        assert api.get_offset_ntc_etn() == -2.0

    def test_offset_ntc_etn_zero(self):
        api = _make_api("imxw")
        api._data_modbus["offset_ntc_etn"] = 0
        assert api.get_offset_ntc_etn() == 0.0

    def test_t2_temperature_present(self):
        api = _make_api("imxw")
        api._data_modbus["t2_temperature"] = 235
        assert api.get_t2_temperature() == 23.5

    def test_t2_temperature_not_present_zero(self):
        api = _make_api("imxw")
        api._data_modbus["t2_temperature"] = 0
        assert api.get_t2_temperature() is None

    def test_t2_temperature_not_present_high(self):
        """Disconnected probe returning 0xFFFF (65535 unsigned)."""
        api = _make_api("imxw")
        api._data_modbus["t2_temperature"] = 65535
        assert api.get_t2_temperature() is None

    def test_t2_temperature_not_present_7fff(self):
        """Disconnected probe returning 0x7FFF (32767 unsigned)."""
        api = _make_api("imxw")
        api._data_modbus["t2_temperature"] = 32767
        assert api.get_t2_temperature() is None

    def test_t2_temperature_not_present_large(self):
        """Any absurd value above 100°C."""
        api = _make_api("imxw")
        api._data_modbus["t2_temperature"] = 60000
        assert api.get_t2_temperature() is None

    def test_firmware_version(self):
        api = _make_api("imxw")
        assert isinstance(api.get_firmware_version(), str)

    def test_modbus_address_default(self):
        api = _make_api("imxw")
        assert api.get_modbus_address() == 0


class TestClimavenetaAPIIlife2:
    """Tests for iLife2 getter methods."""

    def test_get_current_temp(self):
        api = _make_api("ilife2")
        api._data_modbus["current_temperature"] = 195
        assert api.get_current_temp() == 19.5

    def test_alarm_flag(self):
        api = _make_api("ilife2")
        api._data_modbus["alarm_register"] = 0b101
        assert api.get_alarm_flag(0) is True
        assert api.get_alarm_flag(1) is False
        assert api.get_alarm_flag(2) is True

    def test_fan_speed_rpm(self):
        api = _make_api("ilife2")
        api._data_modbus["fan_speed_rpm"] = 850
        assert api.get_fan_speed_rpm() == 850
