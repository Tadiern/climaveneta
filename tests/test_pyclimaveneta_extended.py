"""Extended tests for pyclimaveneta — covers getters, HVAC logic, setters, modbus I/O."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.climaveneta import pyclimaveneta
from custom_components.climaveneta.pyclimaveneta import (
    ClimavenetaAPI,
    ClimavenetaLock,
    CV_MODE_OFF,
    CV_MODE_ON,
    CV_MODE_FAN_ONLY,
    CV_MODE_COOL,
    CV_MODE_HEAT,
    CV_MODE_HEAT_COOL,
    CV_ACTION_OFF,
    CV_ACTION_IDLE,
    CV_ACTION_FAN,
    CV_ACTION_COOLING,
    CV_ACTION_HEATING,
    CV_FAN_AUTO,
    CV_FAN_LOW,
    CV_FAN_MEDIUM,
    CV_FAN_HIGH,
    CV_FAN_OFF,
    CV_FAN_ON,
    CV_MODE_SUMMER,
    CV_MODE_WINTER,
    CV_WATER_BYPASS,
    CV_WATER_CIRCULATING,
    CV_PRESET_MODE_NONE,
    CV_PRESET_MODE_ECO,
    CV_PRESET_MODE_AWAY,
)


def _make_api(unit_type="imxw"):
    """Create a ClimavenetaAPI with mocked Modbus connection."""
    orig = ClimavenetaLock.initialized
    ClimavenetaLock.initialized = True
    ClimavenetaLock.port = MagicMock()
    try:
        api = ClimavenetaAPI(MagicMock(), 1, unit_type)
    finally:
        ClimavenetaLock.initialized = orig
    return api


# ────────────────────────── iMXW diagnostic getters ──────────────────────────

class TestImxwDiagnosticGetters:
    """Tests for the new diagnostic getters (registers 0x1022-0x102B + dip)."""

    def test_continuous_ventilation_on(self):
        api = _make_api("imxw")
        api._data_modbus["continuous_ventilation"] = 1
        assert api.get_continuous_ventilation() is True

    def test_continuous_ventilation_off(self):
        api = _make_api("imxw")
        api._data_modbus["continuous_ventilation"] = 0
        assert api.get_continuous_ventilation() is False

    def test_machine_slave(self):
        api = _make_api("imxw")
        api._data_modbus["machine_slave"] = 1
        assert api.get_machine_slave() is True
        api._data_modbus["machine_slave"] = 0
        assert api.get_machine_slave() is False

    def test_relay5_fan_high(self):
        api = _make_api("imxw")
        api._data_modbus["relay5_fan_high"] = 1
        assert api.get_relay5_fan_high() is True
        api._data_modbus["relay5_fan_high"] = 0
        assert api.get_relay5_fan_high() is False

    def test_window_input(self):
        api = _make_api("imxw")
        api._data_modbus["window_input"] = 1
        assert api.get_window_input() is True
        api._data_modbus["window_input"] = 0
        assert api.get_window_input() is False

    def test_pump_alarm_input(self):
        api = _make_api("imxw")
        api._data_modbus["pump_alarm_input"] = 1
        assert api.get_pump_alarm_input() is True

    def test_heater_present(self):
        api = _make_api("imxw")
        api._data_modbus["heater_present"] = 1
        assert api.get_heater_present() is True
        api._data_modbus["heater_present"] = 0
        assert api.get_heater_present() is False

    def test_analog_output(self):
        api = _make_api("imxw")
        api._data_modbus["analog_output"] = 55
        assert api.get_analog_output() == 5.5

    def test_alarm_t1(self):
        api = _make_api("imxw")
        api._data_modbus["alarm_t1"] = 1
        assert api.get_alarm_t1() is True
        api._data_modbus["alarm_t1"] = 0
        assert api.get_alarm_t1() is False

    def test_alarm_t2(self):
        api = _make_api("imxw")
        api._data_modbus["alarm_t2"] = 1
        assert api.get_alarm_t2() is True

    def test_alarm_t3(self):
        api = _make_api("imxw")
        api._data_modbus["alarm_t3"] = 1
        assert api.get_alarm_t3() is True

    def test_alarm_water_drain(self):
        api = _make_api("imxw")
        api._data_modbus["alarm_water_drain"] = 1
        assert api.get_alarm_water_drain() is True
        api._data_modbus["alarm_water_drain"] = 0
        assert api.get_alarm_water_drain() is False


# ────────────────────────── HVAC mode / action getters ──────────────────────────

class TestHvacGetters:
    """Tests for HVAC mode, action, preset, fan getters."""

    def test_get_hvac_mode(self):
        api = _make_api("imxw")
        api._data_modbus["hvac_mode"] = CV_MODE_COOL
        assert api.get_hvac_mode() == CV_MODE_COOL

    def test_get_hvac_action(self):
        api = _make_api("imxw")
        api._data_modbus["hvac_action"] = CV_ACTION_HEATING
        assert api.get_hvac_action() == CV_ACTION_HEATING

    def test_get_preset_mode(self):
        api = _make_api("imxw")
        api._data_modbus["preset_mode"] = CV_PRESET_MODE_ECO
        assert api.get_preset_mode() == CV_PRESET_MODE_ECO

    def test_get_fan_mode(self):
        api = _make_api("imxw")
        api._data_modbus["fan_mode"] = CV_FAN_HIGH
        assert api.get_fan_mode() == CV_FAN_HIGH

    def test_get_fan_only(self):
        api = _make_api("imxw")
        api._data_modbus["fan_only"] = CV_FAN_ON
        assert api.get_fan_only() is True
        api._data_modbus["fan_only"] = CV_FAN_OFF
        assert api.get_fan_only() is False

    def test_get_on_off(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_ON
        assert api.get_on_off() is True
        api._data_modbus["on_off"] = CV_MODE_OFF
        assert api.get_on_off() is False


# ────────────────────────── Boiler relay logic ──────────────────────────

class TestBoilerRelay:
    """Tests for get_boiler_water_relay_on_off across device types."""

    def test_imxw_relay_on_water_circulating(self):
        api = _make_api("imxw")
        api._data_modbus["ev_water"] = CV_WATER_CIRCULATING
        assert api.get_boiler_water_relay_on_off() is True

    def test_imxw_relay_off_water_bypass(self):
        api = _make_api("imxw")
        api._data_modbus["ev_water"] = CV_WATER_BYPASS
        assert api.get_boiler_water_relay_on_off() is False

    def test_ilife2_relay_heater_on(self):
        api = _make_api("ilife2")
        api._data_modbus["out_register"] = (1 << 3)  # bit 3 = boiler
        assert api.get_boiler_water_relay_on_off() is True

    def test_ilife2_relay_chiller_on(self):
        api = _make_api("ilife2")
        api._data_modbus["out_register"] = (1 << 2)  # bit 2 = chiller
        assert api.get_boiler_water_relay_on_off() is True

    def test_ilife2_relay_off(self):
        api = _make_api("ilife2")
        api._data_modbus["out_register"] = 0
        assert api.get_boiler_water_relay_on_off() is False


# ────────────────────────── IMXW async update HVAC logic ──────────────────────────

class TestImxwUpdateLogic:
    """Tests for _async_update_imxw() HVAC mode/action state machine."""

    async def _run_update(self, api, register_values):
        """Run _async_update_imxw with mocked register reads."""
        call_idx = {"i": 0}

        async def mock_read(register, old_value):
            idx = call_idx["i"]
            call_idx["i"] += 1
            if idx < len(register_values):
                return register_values[idx]
            return old_value

        api._read_modbus_register = mock_read
        api._write_modbus_register = AsyncMock()
        await api._async_update_imxw()

    @pytest.mark.asyncio
    async def test_off_state(self):
        api = _make_api("imxw")
        # season=winter, winter_temp=210, current=200, on_off=0, fan_only=0, ev_water=0
        # Then reads: no_frost=0, eco=0, fan_auto=0, fan_min=0, fan_med=0, fan_max=0
        # exchanger=250, then 9 diagnostic regs, external_probe=0
        values = [
            CV_MODE_WINTER, 210, 200,  # season, winter_temp, current_temp
            0,  # on_off=OFF
            0,  # fan_only
            0,  # ev_water
            0, 0,  # no_frost, eco_mode
            0, 0, 0, 0,  # fan_auto, fan_min, fan_med, fan_max
            250,  # exchanger
            0, 0, 0, 0, 0, 0, 0, 0, 0,  # 9 diagnostic regs
            0,  # external_probe_enabled
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_OFF
        assert api.get_hvac_action() == CV_ACTION_OFF

    @pytest.mark.asyncio
    async def test_heating_active(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,  # season, winter_temp, current
            1,  # on_off=ON
            0,  # fan_only=OFF
            CV_WATER_CIRCULATING,  # ev_water
            0, 0,  # no_frost, eco
            1,  # fan_auto=ON
            250,  # exchanger
            0, 0, 0, 0, 0, 0, 0, 0, 0,  # diagnostics
            0,  # external_probe
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_HEAT
        assert api.get_hvac_action() == CV_ACTION_HEATING

    @pytest.mark.asyncio
    async def test_heating_idle(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1,  # on_off=ON
            0,  # fan_only=OFF
            CV_WATER_BYPASS,  # ev_water=BYPASS → idle
            0, 0,  # no_frost, eco
            1,  # fan_auto=ON
            250,  # exchanger
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_HEAT
        assert api.get_hvac_action() == CV_ACTION_IDLE

    @pytest.mark.asyncio
    async def test_cooling_active(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_SUMMER, 220, 250,  # summer season
            1,  # on
            0,  # fan_only off
            CV_WATER_CIRCULATING,
            0, 0,
            1,  # fan_auto
            300,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_COOL
        assert api.get_hvac_action() == CV_ACTION_COOLING

    @pytest.mark.asyncio
    async def test_cooling_idle(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_SUMMER, 220, 250,
            1, 0,
            CV_WATER_BYPASS,  # idle
            0, 0,
            1,
            300,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_COOL
        assert api.get_hvac_action() == CV_ACTION_IDLE

    @pytest.mark.asyncio
    async def test_fan_only_mode(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1,  # on
            CV_FAN_ON,  # fan_only=ON
            0,  # ev_water
            0, 0,
            1,
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_FAN_ONLY
        assert api.get_hvac_action() == CV_ACTION_FAN

    @pytest.mark.asyncio
    async def test_preset_eco(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            0,  # no_frost=OFF
            1,  # eco_mode=ON
            1,  # fan_auto
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_preset_mode() == CV_PRESET_MODE_ECO

    @pytest.mark.asyncio
    async def test_preset_away(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            1,  # no_frost=ON
            0,  # eco=OFF
            1,
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_preset_mode() == CV_PRESET_MODE_AWAY

    @pytest.mark.asyncio
    async def test_fan_speed_low(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            0, 0,
            0,  # fan_auto=OFF
            1,  # fan_min=ON
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_LOW

    @pytest.mark.asyncio
    async def test_fan_speed_medium(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            0, 0,
            0,  # fan_auto=OFF
            0,  # fan_min=OFF
            1,  # fan_med=ON
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_MEDIUM

    @pytest.mark.asyncio
    async def test_fan_speed_high(self):
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            0, 0,
            0,  # fan_auto=OFF
            0,  # fan_min=OFF
            0,  # fan_med=OFF
            1,  # fan_max=ON
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_HIGH

    @pytest.mark.asyncio
    async def test_fan_speed_fallback_auto(self):
        """When no fan speed flag is on, it defaults to AUTO."""
        api = _make_api("imxw")
        values = [
            CV_MODE_WINTER, 210, 200,
            1, 0, 0,
            0, 0,
            0,  # fan_auto=OFF
            0,  # fan_min=OFF
            0,  # fan_med=OFF
            0,  # fan_max=OFF
            250,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0,
        ]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_AUTO


# ────────────────────────── iLife2 async update logic ──────────────────────────

class TestIlife2UpdateLogic:
    """Tests for _async_update_ilife2() state machine."""

    async def _run_update(self, api, register_values):
        call_idx = {"i": 0}

        async def mock_read(register, old_value):
            idx = call_idx["i"]
            call_idx["i"] += 1
            if idx < len(register_values):
                return register_values[idx]
            return old_value

        api._read_modbus_register = mock_read
        api._write_modbus_register = AsyncMock()
        await api._async_update_ilife2()

    @pytest.mark.asyncio
    async def test_ilife2_off(self):
        api = _make_api("ilife2")
        # target, current, exchanger, fan_rpm, man, program(standby=0x80), stat, out, alarm
        values = [0, 200, 300, 0, 0, 0x80, 0, 0, 0]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_OFF
        assert api.get_hvac_action() == CV_ACTION_OFF

    @pytest.mark.asyncio
    async def test_ilife2_heating(self):
        api = _make_api("ilife2")
        # program=0 (on), man=3 (heat), stat bit1=1 → heating
        values = [220, 200, 300, 850, 3, 0b000, 0b10, 0, 0]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_HEAT
        assert api.get_hvac_action() == CV_ACTION_HEATING

    @pytest.mark.asyncio
    async def test_ilife2_cooling(self):
        api = _make_api("ilife2")
        # man=5 (cool), stat bit0=1 bit1=0 → cooling
        values = [220, 250, 300, 850, 5, 0b000, 0b01, 0, 0]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_COOL
        assert api.get_hvac_action() == CV_ACTION_COOLING

    @pytest.mark.asyncio
    async def test_ilife2_auto_idle(self):
        api = _make_api("ilife2")
        # man=0 (auto), stat=0 → idle
        values = [220, 200, 300, 850, 0, 0b000, 0b00, 0, 0]
        await self._run_update(api, values)
        assert api.get_hvac_mode() == CV_MODE_HEAT_COOL
        assert api.get_hvac_action() == CV_ACTION_IDLE

    @pytest.mark.asyncio
    async def test_ilife2_fan_speed_low(self):
        api = _make_api("ilife2")
        values = [220, 200, 300, 850, 0, 0b001, 0, 0, 0]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_LOW

    @pytest.mark.asyncio
    async def test_ilife2_fan_speed_medium(self):
        api = _make_api("ilife2")
        values = [220, 200, 300, 850, 0, 0b010, 0, 0, 0]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_MEDIUM

    @pytest.mark.asyncio
    async def test_ilife2_fan_speed_high(self):
        api = _make_api("ilife2")
        values = [220, 200, 300, 850, 0, 0b011, 0, 0, 0]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_HIGH

    @pytest.mark.asyncio
    async def test_ilife2_fan_speed_auto(self):
        api = _make_api("ilife2")
        values = [220, 200, 300, 850, 0, 0b000, 0, 0, 0]
        await self._run_update(api, values)
        assert api.get_fan_mode() == CV_FAN_AUTO


# ────────────────────────── Setter methods ──────────────────────────

class TestSetters:
    """Tests for set_target_temp, turn_on, set_fan_speed, set_hvac_mode, set_preset_mode."""

    @pytest.mark.asyncio
    async def test_set_target_temp_imxw_winter(self):
        api = _make_api("imxw")
        api._data_modbus["summer_winter"] = CV_MODE_WINTER
        api._data_modbus["target_temperature"] = 0
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_target_temp(22.0)
        assert result is True
        api._write_modbus_register.assert_awaited_once()
        assert api._data_modbus["target_temperature"] == 220

    @pytest.mark.asyncio
    async def test_set_target_temp_imxw_summer(self):
        api = _make_api("imxw")
        api._data_modbus["summer_winter"] = CV_MODE_SUMMER
        api._data_modbus["target_temperature"] = 0
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_target_temp(24.5)
        assert result is True
        assert api._data_modbus["target_temperature"] == 245

    @pytest.mark.asyncio
    async def test_set_target_temp_no_change(self):
        api = _make_api("imxw")
        api._data_modbus["summer_winter"] = CV_MODE_WINTER
        api._data_modbus["target_temperature"] = 220
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_target_temp(22.0)
        assert result is True
        api._write_modbus_register.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_target_temp_ilife2(self):
        api = _make_api("ilife2")
        api._data_modbus["target_temperature"] = 0
        api._write_modbus_register = AsyncMock(return_value=True)
        await api.set_target_temp(21.0)
        assert api._data_modbus["target_temperature"] == 210

    @pytest.mark.asyncio
    async def test_turn_on_imxw(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock()
        await api.turn_on()
        assert api._data_modbus["on_off"] == CV_MODE_ON
        api._write_modbus_register.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_turn_on_ilife2(self):
        api = _make_api("ilife2")
        api._write_modbus_register = AsyncMock()
        await api.turn_on()
        assert api._data_modbus["on_off"] == CV_MODE_ON

    @pytest.mark.asyncio
    async def test_set_fan_speed_imxw(self):
        api = _make_api("imxw")
        api._data_modbus["fan_mode"] = CV_FAN_AUTO
        api._write_modbus_register = AsyncMock()
        await api.set_fan_speed(CV_FAN_HIGH)
        assert api._data_modbus["fan_mode"] == CV_FAN_HIGH

    @pytest.mark.asyncio
    async def test_set_fan_speed_no_change(self):
        api = _make_api("imxw")
        api._data_modbus["fan_mode"] = CV_FAN_HIGH
        api._write_modbus_register = AsyncMock()
        await api.set_fan_speed(CV_FAN_HIGH)
        api._write_modbus_register.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_fan_speed_ilife2_while_off(self):
        api = _make_api("ilife2")
        api._data_modbus["on_off"] = CV_MODE_OFF
        api._data_modbus["fan_mode"] = CV_FAN_AUTO
        api._write_modbus_register = AsyncMock()
        await api.set_fan_speed(CV_FAN_LOW)
        # Fan mode when off gets bit 7 set
        call_args = api._write_modbus_register.call_args
        assert call_args[0][1] == CV_FAN_LOW + (1 << 7)

    @pytest.mark.asyncio
    async def test_set_hvac_mode_imxw_off(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_HEAT
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_OFF)
        assert api._data_modbus["on_off"] == CV_MODE_OFF

    @pytest.mark.asyncio
    async def test_set_hvac_mode_imxw_heat(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_OFF
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_HEAT)
        assert api._data_modbus["on_off"] == CV_MODE_ON
        assert api._data_modbus["hvac_mode"] == CV_MODE_HEAT

    @pytest.mark.asyncio
    async def test_set_hvac_mode_imxw_cool(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_COOL)
        assert api._data_modbus["hvac_mode"] == CV_MODE_COOL

    @pytest.mark.asyncio
    async def test_set_hvac_mode_imxw_auto(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_HEAT_COOL)
        assert api._data_modbus["hvac_mode"] == CV_MODE_HEAT_COOL

    @pytest.mark.asyncio
    async def test_set_hvac_mode_imxw_fan_only(self):
        api = _make_api("imxw")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_FAN_ONLY)
        assert api._data_modbus["hvac_mode"] == CV_MODE_FAN_ONLY

    @pytest.mark.asyncio
    async def test_set_hvac_mode_ilife2_off(self):
        api = _make_api("ilife2")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_OFF)
        assert api._data_modbus["on_off"] == CV_MODE_OFF

    @pytest.mark.asyncio
    async def test_set_hvac_mode_ilife2_cool(self):
        api = _make_api("ilife2")
        api._data_modbus["on_off"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_COOL)
        assert api._data_modbus["hvac_mode"] == CV_MODE_COOL

    @pytest.mark.asyncio
    async def test_set_hvac_mode_ilife2_heat(self):
        api = _make_api("ilife2")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_HEAT)
        assert api._data_modbus["hvac_mode"] == CV_MODE_HEAT

    @pytest.mark.asyncio
    async def test_set_hvac_mode_ilife2_auto(self):
        api = _make_api("ilife2")
        api._data_modbus["on_off"] = CV_MODE_ON
        api._data_modbus["hvac_mode"] = CV_MODE_OFF
        api._write_modbus_register = AsyncMock()
        api.async_update = AsyncMock()
        await api.set_hvac_mode(CV_MODE_HEAT_COOL)
        assert api._data_modbus["hvac_mode"] == CV_MODE_HEAT_COOL

    @pytest.mark.asyncio
    async def test_set_preset_none(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock()
        await api.set_preset_mode(CV_PRESET_MODE_NONE)
        assert api._data_modbus["preset_mode"] == CV_PRESET_MODE_NONE

    @pytest.mark.asyncio
    async def test_set_preset_eco(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock()
        await api.set_preset_mode(CV_PRESET_MODE_ECO)
        assert api._data_modbus["preset_mode"] == CV_PRESET_MODE_ECO

    @pytest.mark.asyncio
    async def test_set_preset_away(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock()
        await api.set_preset_mode(CV_PRESET_MODE_AWAY)
        assert api._data_modbus["preset_mode"] == CV_PRESET_MODE_AWAY

    @pytest.mark.asyncio
    async def test_set_actual_true_temperature(self):
        api = _make_api("imxw")
        await api.set_actual_true_temperature(23.5)
        assert api._actual_true_temperature == 235
        assert api._enable_actual_true_temperature is True

    @pytest.mark.asyncio
    async def test_set_actual_true_temperature_ilife2_noop(self):
        """iLife2 should not set true temperature (IMXW-only feature)."""
        api = _make_api("ilife2")
        await api.set_actual_true_temperature(23.5)
        assert api._enable_actual_true_temperature is False


# ────────────────────────── Modbus read/write ──────────────────────────

class TestModbusIO:
    """Tests for _read_modbus_register and _write_modbus_register."""

    @pytest.mark.asyncio
    async def test_read_register_success(self):
        api = _make_api("imxw")
        mock_result = MagicMock()
        mock_result.registers = [42]
        with patch.object(pyclimaveneta, "cv_pool") as mock_pool:
            future = MagicMock()
            future.result.return_value = mock_result
            mock_pool.submit.return_value = future
            val = await api._read_modbus_register(0x1002, 99)
        assert val == 42

    @pytest.mark.asyncio
    async def test_read_register_no_registers_attr(self):
        api = _make_api("imxw")
        mock_result = MagicMock(spec=[])  # no 'registers' attribute
        with patch.object(pyclimaveneta, "cv_pool") as mock_pool:
            future = MagicMock()
            future.result.return_value = mock_result
            mock_pool.submit.return_value = future
            val = await api._read_modbus_register(0x1002, 99)
        assert val == 99  # returns old_value

    @pytest.mark.asyncio
    async def test_read_register_modbus_exception(self):
        api = _make_api("imxw")
        from pymodbus.exceptions import ModbusException
        with patch.object(pyclimaveneta, "cv_pool") as mock_pool:
            mock_pool.submit.side_effect = ModbusException("fail")
            val = await api._read_modbus_register(0x1002, 77)
        assert val == 77  # returns old_value


# ────────────────────────── hex_to_custom_string edge cases ──────────────────────────

class TestHexToCustomString:
    """Additional edge cases for version string conversion."""

    def test_short_hex(self):
        fn = ClimavenetaAPI._ClimavenetaAPI__hex_to_custom_string
        assert fn(0x05) == "0.05"

    def test_normal_hex(self):
        fn = ClimavenetaAPI._ClimavenetaAPI__hex_to_custom_string
        assert fn(0x106) == "1.06"

    def test_zero(self):
        fn = ClimavenetaAPI._ClimavenetaAPI__hex_to_custom_string
        result = fn(0)
        assert "." in result


# ────────────────────────── Default initialization ──────────────────────────

class TestDefaults:
    """Verify default values are correctly set for each device type."""

    def test_imxw_defaults(self):
        api = _make_api("imxw")
        assert api._data_modbus["continuous_ventilation"] == 0
        assert api._data_modbus["machine_slave"] == 0
        assert api._data_modbus["relay5_fan_high"] == 0
        assert api._data_modbus["alarm_t1"] == 0
        assert api._data_modbus["alarm_water_drain"] == 0
        assert api._data_modbus["analog_output"] == 0
        assert api._data_modbus["on_off"] == CV_FAN_OFF
        assert api._data_modbus["preset_mode"] == CV_PRESET_MODE_NONE

    def test_ilife2_defaults(self):
        api = _make_api("ilife2")
        assert api._data_modbus["alarm_register"] == 0
        assert api._data_modbus["program_register"] == 0b10000000
        assert api._data_modbus["stat_register"] == 0
        assert "relay5_fan_high" not in api._data_modbus  # iMXW-only

    def test_try_initial_communication(self):
        api = _make_api("imxw")
        asyncio.get_event_loop().run_until_complete(api.try_initial_communication())


# ────────────────────────── async_read_configuration ──────────────────────────

class TestAsyncReadConfiguration:
    """Test async_read_configuration for both device types."""

    @pytest.mark.asyncio
    async def test_imxw_config_reads_dip_switches(self):
        api = _make_api("imxw")
        call_count = {"i": 0}

        async def mock_read(register, old_value):
            from custom_components.climaveneta.pyclimaveneta import (
                IMXW_DIP1_REGISTER, IMXW_DIP2_REGISTER,
            )
            call_count["i"] += 1
            if register == IMXW_DIP1_REGISTER:
                return 1  # dip1=1 → continuous_ventilation should be inverted to 0
            if register == IMXW_DIP2_REGISTER:
                return 1  # slave
            return old_value

        api._read_modbus_register = mock_read
        api.async_update = AsyncMock()
        await api.async_read_configuration()

        assert api._data_modbus["continuous_ventilation"] == 0  # inverted
        assert api._data_modbus["machine_slave"] == 1

    @pytest.mark.asyncio
    async def test_imxw_config_dip1_zero_means_ventilation_on(self):
        api = _make_api("imxw")

        async def mock_read(register, old_value):
            from custom_components.climaveneta.pyclimaveneta import IMXW_DIP1_REGISTER
            if register == IMXW_DIP1_REGISTER:
                return 0  # dip1=0 → continuous_ventilation ON
            return old_value

        api._read_modbus_register = mock_read
        api.async_update = AsyncMock()
        await api.async_read_configuration()

        assert api._data_modbus["continuous_ventilation"] == 1

    @pytest.mark.asyncio
    async def test_ilife2_config(self):
        api = _make_api("ilife2")

        async def mock_read(register, old_value):
            return old_value

        api._read_modbus_register = mock_read
        api.async_update = AsyncMock()
        await api.async_read_configuration()

        assert api._firmware_version_text == ""

    @pytest.mark.asyncio
    async def test_imxw_config_ofs_positive(self):
        """OFS register with a positive signed value."""
        api = _make_api("imxw")

        async def mock_read(register, old_value):
            from custom_components.climaveneta.pyclimaveneta import IMXW_OFFSET_NTC_ETN_REGISTER
            if register == IMXW_OFFSET_NTC_ETN_REGISTER:
                return 15  # +1.5 °C
            return old_value

        api._read_modbus_register = mock_read
        api.async_update = AsyncMock()
        await api.async_read_configuration()

        assert api._data_modbus["offset_ntc_etn"] == 15
        assert api.get_offset_ntc_etn() == 1.5

    @pytest.mark.asyncio
    async def test_imxw_config_ofs_negative(self):
        """OFS register with a negative value (unsigned 65516 → signed -20 → -2.0 °C)."""
        api = _make_api("imxw")

        async def mock_read(register, old_value):
            from custom_components.climaveneta.pyclimaveneta import IMXW_OFFSET_NTC_ETN_REGISTER
            if register == IMXW_OFFSET_NTC_ETN_REGISTER:
                return 65516  # unsigned representation of -20
            return old_value

        api._read_modbus_register = mock_read
        api.async_update = AsyncMock()
        await api.async_read_configuration()

        assert api._data_modbus["offset_ntc_etn"] == -20
        assert api.get_offset_ntc_etn() == -2.0


# ────────────────────────── Configuration parameter setters ──────────────────────────

class TestConfigSetters:
    """Test setter methods for configuration registers 0x1057-0x105B."""

    @pytest.mark.asyncio
    async def test_set_antistrat_wait_time(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_wait_time(15)
        assert result is True
        assert api._data_modbus["antistrat_wait_time"] == 15

    @pytest.mark.asyncio
    async def test_set_antistrat_wait_time_fail(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=False)
        api._data_modbus["antistrat_wait_time"] = 10
        result = await api.set_antistrat_wait_time(15)
        assert result is False
        assert api._data_modbus["antistrat_wait_time"] == 10  # unchanged

    @pytest.mark.asyncio
    async def test_set_t1_compensation_base_summer(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_summer(1.5)
        assert result is True
        assert api._data_modbus["t1_compensation_base_summer"] == 15  # raw * 10

    @pytest.mark.asyncio
    async def test_set_antistrat_time_summer(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_summer(90)
        assert result is True
        assert api._data_modbus["antistrat_time_summer"] == 90

    @pytest.mark.asyncio
    async def test_set_t1_compensation_base_winter(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_winter(3.0)
        assert result is True
        assert api._data_modbus["t1_compensation_base_winter"] == 30  # raw * 10

    @pytest.mark.asyncio
    async def test_set_antistrat_time_winter(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_winter(120)
        assert result is True
        assert api._data_modbus["antistrat_time_winter"] == 120

    # ── Failure paths ──

    @pytest.mark.asyncio
    async def test_set_t1_compensation_base_summer_fail(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=False)
        api._data_modbus["t1_compensation_base_summer"] = 10
        result = await api.set_t1_compensation_base_summer(1.5)
        assert result is False
        assert api._data_modbus["t1_compensation_base_summer"] == 10

    @pytest.mark.asyncio
    async def test_set_antistrat_time_summer_fail(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=False)
        api._data_modbus["antistrat_time_summer"] = 60
        result = await api.set_antistrat_time_summer(90)
        assert result is False
        assert api._data_modbus["antistrat_time_summer"] == 60

    @pytest.mark.asyncio
    async def test_set_t1_compensation_base_winter_fail(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=False)
        api._data_modbus["t1_compensation_base_winter"] = 20
        result = await api.set_t1_compensation_base_winter(3.0)
        assert result is False
        assert api._data_modbus["t1_compensation_base_winter"] == 20

    @pytest.mark.asyncio
    async def test_set_antistrat_time_winter_fail(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=False)
        api._data_modbus["antistrat_time_winter"] = 90
        result = await api.set_antistrat_time_winter(120)
        assert result is False
        assert api._data_modbus["antistrat_time_winter"] == 90

    # ── Boundary values ──

    @pytest.mark.asyncio
    async def test_set_antistrat_wait_time_min(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_wait_time(10)
        assert result is True
        assert api._data_modbus["antistrat_wait_time"] == 10

    @pytest.mark.asyncio
    async def test_set_antistrat_wait_time_max(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_wait_time(20)
        assert result is True
        assert api._data_modbus["antistrat_wait_time"] == 20

    @pytest.mark.asyncio
    async def test_set_t1_base_summer_min(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_summer(0.5)
        assert result is True
        assert api._data_modbus["t1_compensation_base_summer"] == 5

    @pytest.mark.asyncio
    async def test_set_t1_base_summer_max(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_summer(2.0)
        assert result is True
        assert api._data_modbus["t1_compensation_base_summer"] == 20

    @pytest.mark.asyncio
    async def test_set_t1_base_winter_min(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_winter(0.5)
        assert result is True
        assert api._data_modbus["t1_compensation_base_winter"] == 5

    @pytest.mark.asyncio
    async def test_set_t1_base_winter_max(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_t1_compensation_base_winter(5.0)
        assert result is True
        assert api._data_modbus["t1_compensation_base_winter"] == 50

    @pytest.mark.asyncio
    async def test_set_antistrat_time_summer_min(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_summer(30)
        assert result is True
        assert api._data_modbus["antistrat_time_summer"] == 30

    @pytest.mark.asyncio
    async def test_set_antistrat_time_summer_max(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_summer(180)
        assert result is True
        assert api._data_modbus["antistrat_time_summer"] == 180

    @pytest.mark.asyncio
    async def test_set_antistrat_time_winter_min(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_winter(30)
        assert result is True
        assert api._data_modbus["antistrat_time_winter"] == 30

    @pytest.mark.asyncio
    async def test_set_antistrat_time_winter_max(self):
        api = _make_api("imxw")
        api._write_modbus_register = AsyncMock(return_value=True)
        result = await api.set_antistrat_time_winter(180)
        assert result is True
        assert api._data_modbus["antistrat_time_winter"] == 180
