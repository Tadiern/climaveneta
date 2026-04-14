"""Connection to a Climaveneta i-MXW or iLife2 ModBus API."""

from concurrent.futures import ThreadPoolExecutor
import logging
import time

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ModbusPDU

IMXW_FIRMWARE_RELEASE_REGISTER = 0x1001
IMXW_ACTUAL_AIR_TEMPERATURE_REGISTER = 0x1002
IMXW_T2_TEMPERATURE_REGISTER = 0x1003
IMXW_ACTUAL_WATER_TEMPERATURE_REGISTER = 0x1004

IMXW_DIP1_REGISTER = 0x1005
IMXW_DIP2_REGISTER = 0x1006

IMXW_STATE_READ_ON_OFF_REGISTER = 0x100F
IMXW_STATE_READ_FAN_ONLY_REGISTER = 0x1010
IMXW_STATE_READ_SEASON_REGISTER = 0x1013
IMXW_STATE_READ_FAN_AUTO_REGISTER = 0x1017
IMXW_STATE_READ_FAN_STOP_REGISTER = 0x1018
IMXW_STATE_READ_FAN_MIN_SPEED_REGISTER = 0x1019
IMXW_STATE_READ_FAN_MED_SPEED_REGISTER = 0x101A
IMXW_STATE_READ_FAN_MAX_SPEED_REGISTER = 0x101B
IMXW_STATE_READ_EV_WATER_REGISTER = 0x101C

IMXW_ALARM_T1_REGISTER = 0x1028
IMXW_ALARM_T2_REGISTER = 0x1029
IMXW_ALARM_T3_REGISTER = 0x102A
IMXW_ALARM_WATER_DRAIN_REGISTER = 0x102B

IMXW_OFFSET_NTC_ETN_REGISTER = 0x102C

IMXW_RELAY5_FAN_HIGH_REGISTER = 0x1022
IMXW_WINDOW_INPUT_REGISTER = 0x1023
IMXW_PUMP_ALARM_INPUT_REGISTER = 0x1024
IMXW_HEATER_PRESENT_REGISTER = 0x1026
IMXW_ANALOG_OUTPUT_REGISTER = 0x1027

IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER = 0x102D
IMXW_TARGET_TEMPERATURE_WINTER_REGISTER = 0x102E

IMWX_MIN_WATER_TEMP_WINTER_REGISTER = 0x1032
IMWX_MAX_WATER_TEMP_SUMMER_REGISTER = 0x1033

IMXW_SETPOINT_HYSTERESIS_REGISTER = 0x1038
IMXW_DEAD_ZONE_CENTER_REGISTER = 0x1039
IMXW_DEAD_ZONE_RANGE_REGISTER = 0x103A
IMXW_T1_COMPENSATION_DELTA_REGISTER = 0x103B

IMXW_MINIMUM_VOLTAGE_WINTER = 0x103F
IMXW_MAXIMUM_VOLTAGE_WINTER = 0x1040

IMXW_MINIMUM_VOLTAGE_SUMMER = 0x1050
IMXW_MAXIMUM_VOLTAGE_SUMMER = 0x1051

IMXW_ANTISTRAT_WAIT_TIME_REGISTER = 0x1057
IMXW_T1_COMPENSATION_BASE_SUMMER_REGISTER = 0x1058
IMXW_ANTISTRAT_TIME_SUMMER_REGISTER = 0x1059
IMXW_T1_COMPENSATION_BASE_WINTER_REGISTER = 0x105A
IMXW_ANTISTRAT_TIME_WINTER_REGISTER = 0x105B

IMXW_STATE_WRITE_ON_OFF_REGISTER = 0x105C
IMXW_PRESET_WRITE_NO_FROST_REGISTER = 0x1055
IMXW_PRESET_WRITE_POWER_SAVE_REGISTER = 0x1056
IMXW_STATE_WRITE_MODE_REGISTER = 0x105D
IMXW_STATE_WRITE_FAN_SPEED_REGISTER = 0x105E

IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_ENABLED_REGISTER = 0x1070
IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_REGISTER = 0x1071


""" Climaveneta iLife modbus registers"""
ILIFE_ACTUAL_AIR_TEMPERATURE_REGISTER = 0
ILIFE_ACTUAL_WATER_TEMPERATURE_REGISTER = 1
ILIFE_STATE_READ_SETPOINT_REGISTER = 8
ILIFE_STATE_OUT_REGISTER = 9
ILIFE_ACTUAL_FAN_SPEED_RPM_REGISTER = 15
ILIFE_STATE_READ_REGISTER = 104
ILIFE_STATE_READ_ALARM_REGISTER = 105
ILIFE_STATE_READ_MODBUS_ADDRESS_REGISTER = 200
ILIFE_STATE_READ_PROGRAM_REGISTER = 201
ILIFE_MIN_WATER_TEMP_HEATING_REGISTER = 218
ILIFE_MAX_WATER_TEMP_COOLING_REGISTER = 219
ILIFE_TARGET_TEMPERATURE_REGISTER = 231
ILIFE_STATE_MAN_REGISTER = 233


""" global mode/flags"""
CV_MODE_SUMMER = 0
CV_MODE_WINTER = 1

CV_IMXW_MODE_SUMMER = 0
CV_IMXW_MODE_WINTER = 1
CV_IMXW_MODE_FAN_ONLY = 2
CV_IMXW_MODE_AUTO = 3


CV_WATER_BYPASS = 0
CV_WATER_CIRCULATING = 1


""" HVAC Modes """
CV_MODE_OFF = 0
CV_MODE_ON = 1
CV_MODE_FAN_ONLY = 2
CV_MODE_COOL = 3
CV_MODE_HEAT = 4
CV_MODE_HEAT_COOL = 5

""" HVAC Actions """
CV_ACTION_OFF = 0
CV_ACTION_IDLE = 1
CV_ACTION_FAN = 2
CV_ACTION_COOLING = 3
CV_ACTION_HEATING = 4

""" Fan Speed """
CV_FAN_AUTO = 0
CV_FAN_LOW = 1
CV_FAN_MEDIUM = 2
CV_FAN_HIGH = 3

""" Fan Modes """
CV_FAN_OFF = 0
CV_FAN_ON = 1

""" Preset modes - IMXW """
CV_PRESET_MODE_NONE = 0
CV_PRESET_MODE_ECO = 1
CV_PRESET_MODE_AWAY = 2


CLIMAVENETA_IMXW = "imxw"
CLIMAVENETA_ILIFE2 = "ilife2"


""" Delays and timeouts """
CLIMAVENETA_IMXW_TIMEOUT_TRUE_TEMPERATURE_SECONDS = 15 * 60
CLIMAVENETA_MODBUS_LAZY_ERROR_COUNT = 2
CLIMAVENETA_MODBUS_OK_SLEEP_SECONDS = 0.04
CLIMAVENETA_MODBUS_KO_SLEEP_SECONDS = 0.2

_LOGGER = logging.getLogger(__name__)


cv_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="climaveneta_executor")


class ClimavenetaLock:
    """Climaveneta global lock and executor class."""

    #    lock = asyncio.Lock()
    initialized = False
    port: ModbusSerialClient


class ClimavenetaAPI:
    """Climaveneta API."""

    _connected = False

    def __init__(self, port, slave, unit_type) -> None:
        """Initialize Climaveneta communication."""
        if ClimavenetaLock.initialized is False:
            ClimavenetaLock.port = port
            ClimavenetaLock.initialized = True
            ClimavenetaLock.port.connect()

        self._slave = slave
        self._unit_type = unit_type
        self._data_modbus: dict[str, int] = {}
        self._enable_actual_true_temperature = False
        self._actual_true_temperature = 0
        self._last_time_true_temperature_sent = time.time()
        self._firmware_version_text = "0.00"

        # some defaults initialization
        if self._unit_type == CLIMAVENETA_IMXW:
            self._data_modbus["summer_winter"] = CV_MODE_WINTER
            self._data_modbus["winter_temperature"] = 0
            self._data_modbus["summer_temperature"] = 0
            self._data_modbus["on_off"] = CV_FAN_OFF
            self._data_modbus["fan_only"] = CV_FAN_OFF
            self._data_modbus["ev_water"] = 0
            self._data_modbus["fan_auto"] = CV_FAN_OFF
            self._data_modbus["fan_min"] = CV_FAN_OFF
            self._data_modbus["fan_med"] = CV_FAN_OFF
            self._data_modbus["fan_max"] = CV_FAN_OFF
            self._data_modbus["no_frost"] = 0
            self._data_modbus["eco_mode"] = 0
            self._data_modbus["external_probe_enabled"] = 0
            self._data_modbus["setpoint_hysteresis"] = 0
            self._data_modbus["dead_zone_center"] = 0
            self._data_modbus["dead_zone_range"] = 0
            self._data_modbus["t1_compensation_delta"] = 0
            self._data_modbus["antistrat_wait_time"] = 0
            self._data_modbus["t1_compensation_base_summer"] = 0
            self._data_modbus["antistrat_time_summer"] = 0
            self._data_modbus["t1_compensation_base_winter"] = 0
            self._data_modbus["antistrat_time_winter"] = 0
            self._data_modbus["offset_ntc_etn"] = 0
            self._data_modbus["t2_temperature"] = 0
            self._data_modbus["continuous_ventilation"] = 0
            self._data_modbus["machine_slave"] = 0
            self._data_modbus["relay5_fan_high"] = 0
            self._data_modbus["window_input"] = 0
            self._data_modbus["pump_alarm_input"] = 0
            self._data_modbus["heater_present"] = 0
            self._data_modbus["analog_output"] = 0
            self._data_modbus["alarm_t1"] = 0
            self._data_modbus["alarm_t2"] = 0
            self._data_modbus["alarm_t3"] = 0
            self._data_modbus["alarm_water_drain"] = 0
        else:
            self._data_modbus["man_register"] = 0
            self._data_modbus["program_register"] = 0b10000000
            self._data_modbus["stat_register"] = 0
            self._data_modbus["alarm_register"] = 0
            self._data_modbus["modbus_address"] = 0

        self._data_modbus["target_temperature"] = 0
        self._data_modbus["current_temperature"] = 0
        self._data_modbus["fan_speed_rpm"] = 0
        self._data_modbus["exchanger_temperature"] = 0
        self._data_modbus["preset_mode"] = CV_PRESET_MODE_NONE
        self._data_modbus["min_voltage_winter"] = 0
        self._data_modbus["max_voltage_winter"] = 0
        self._data_modbus["min_voltage_summer"] = 0
        self._data_modbus["max_voltage_summer"] = 0
        self._data_modbus["max_water_temp_summer"] = 0
        self._data_modbus["min_water_temp_winter"] = 0
        self._data_modbus["out_register"] = 0
        self._data_modbus["modbus_address"] = 0

    async def try_initial_communication(self) -> None:
        """Connect to rs485 device."""
        # async with ClimavenetaLock.lock:
        # future = cv_pool.submit(ClimavenetaLock.port.connect)  # does not block
        # result = future.result()  # blocks

        result = "ok"

        _LOGGER.info(
            "Connected slave %d unit type %s, connected %s",
            self._slave,
            self._unit_type,
            result,
        )

    async def async_read_configuration(self):
        """Request current configuration from heat pump."""

        
 
        if self._unit_type == CLIMAVENETA_IMXW:
            firmware_version = 0
            firmware_version = await self._read_modbus_register(
                IMXW_FIRMWARE_RELEASE_REGISTER, firmware_version
            )
            self._firmware_version_text = self.__hex_to_custom_string(firmware_version)

            self._data_modbus["min_voltage_winter"] = await self._read_modbus_register(
                IMXW_MINIMUM_VOLTAGE_WINTER, self._data_modbus["min_voltage_winter"]
            )
            self._data_modbus["max_voltage_winter"] = await self._read_modbus_register(
                IMXW_MAXIMUM_VOLTAGE_WINTER, self._data_modbus["max_voltage_winter"]
            )
            self._data_modbus["min_voltage_summer"] = await self._read_modbus_register(
                IMXW_MINIMUM_VOLTAGE_SUMMER, self._data_modbus["min_voltage_summer"]
            )
            self._data_modbus["max_voltage_summer"] = await self._read_modbus_register(
                IMXW_MAXIMUM_VOLTAGE_SUMMER, self._data_modbus["max_voltage_summer"]
            )
            self._data_modbus["max_water_temp_summer"] = await self._read_modbus_register(
                IMWX_MAX_WATER_TEMP_SUMMER_REGISTER, self._data_modbus["max_water_temp_summer"]
            )
            self._data_modbus["min_water_temp_winter"] = await self._read_modbus_register(
                IMWX_MIN_WATER_TEMP_WINTER_REGISTER, self._data_modbus["min_water_temp_winter"]
            )
            self._data_modbus["setpoint_hysteresis"] = await self._read_modbus_register(
                IMXW_SETPOINT_HYSTERESIS_REGISTER, self._data_modbus["setpoint_hysteresis"]
            )
            self._data_modbus["dead_zone_center"] = await self._read_modbus_register(
                IMXW_DEAD_ZONE_CENTER_REGISTER, self._data_modbus["dead_zone_center"]
            )
            self._data_modbus["dead_zone_range"] = await self._read_modbus_register(
                IMXW_DEAD_ZONE_RANGE_REGISTER, self._data_modbus["dead_zone_range"]
            )
            self._data_modbus["t1_compensation_delta"] = await self._read_modbus_register(
                IMXW_T1_COMPENSATION_DELTA_REGISTER, self._data_modbus["t1_compensation_delta"]
            )
            self._data_modbus["antistrat_wait_time"] = await self._read_modbus_register(
                IMXW_ANTISTRAT_WAIT_TIME_REGISTER, self._data_modbus["antistrat_wait_time"]
            )
            self._data_modbus["t1_compensation_base_summer"] = await self._read_modbus_register(
                IMXW_T1_COMPENSATION_BASE_SUMMER_REGISTER, self._data_modbus["t1_compensation_base_summer"]
            )
            self._data_modbus["antistrat_time_summer"] = await self._read_modbus_register(
                IMXW_ANTISTRAT_TIME_SUMMER_REGISTER, self._data_modbus["antistrat_time_summer"]
            )
            self._data_modbus["t1_compensation_base_winter"] = await self._read_modbus_register(
                IMXW_T1_COMPENSATION_BASE_WINTER_REGISTER, self._data_modbus["t1_compensation_base_winter"]
            )
            self._data_modbus["antistrat_time_winter"] = await self._read_modbus_register(
                IMXW_ANTISTRAT_TIME_WINTER_REGISTER, self._data_modbus["antistrat_time_winter"]
            )

            # OFS - NTC ETN probe offset (signed, °C*10)
            raw_ofs = await self._read_modbus_register(
                IMXW_OFFSET_NTC_ETN_REGISTER, self._data_modbus["offset_ntc_etn"]
            )
            # Convert unsigned 16-bit to signed
            if raw_ofs > 32767:
                raw_ofs = raw_ofs - 65536
            self._data_modbus["offset_ntc_etn"] = raw_ofs

            # Dip switch configuration (read once at startup)
            dip1_raw = await self._read_modbus_register(
                IMXW_DIP1_REGISTER, 0
            )
            # For machines without resistance: 1=continuous ventilation OFF, 0=ON → invert
            self._data_modbus["continuous_ventilation"] = 0 if dip1_raw else 1

            dip2_raw = await self._read_modbus_register(
                IMXW_DIP2_REGISTER, 0
            )
            # 1=Slave, 0=Master
            self._data_modbus["machine_slave"] = dip2_raw
        else:
            self._firmware_version_text = ""

            self._data_modbus["max_water_temp_summer"] = await self._read_modbus_register(
                ILIFE_MAX_WATER_TEMP_COOLING_REGISTER, self._data_modbus["max_water_temp_summer"]
            )
            self._data_modbus["min_water_temp_winter"] = await self._read_modbus_register(
                ILIFE_MIN_WATER_TEMP_HEATING_REGISTER, self._data_modbus["min_water_temp_winter"]
            )
            self._data_modbus["modbus_address"] = await self._read_modbus_register(
                ILIFE_STATE_READ_MODBUS_ADDRESS_REGISTER, self._data_modbus["modbus_address"]
            )

        # at start, sync data so we have everything set in place
        await self.async_update()




    async def async_update(self):
        """Request current values from heat pump."""

        if self._unit_type == CLIMAVENETA_IMXW:
            await self._async_update_imxw()
        else:
            await self._async_update_ilife2()

    async def _async_update_imxw(self):
        """Fetch data from IMXW device."""

        # setpoint and actuals

        self._data_modbus["summer_winter"] = await self._read_modbus_register(
            IMXW_STATE_READ_SEASON_REGISTER, self._data_modbus["summer_winter"]
        )

        if self._data_modbus["summer_winter"] == CV_MODE_WINTER:  # winter
            self._data_modbus["winter_temperature"] = await self._read_modbus_register(
                IMXW_TARGET_TEMPERATURE_WINTER_REGISTER,
                self._data_modbus["winter_temperature"],
            )

            self._data_modbus["target_temperature"] = self._data_modbus[
                "winter_temperature"
            ]
        else:  # summer
            self._data_modbus["summer_temperature"] = await self._read_modbus_register(
                IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER,
                self._data_modbus["summer_temperature"],
            )

            self._data_modbus["target_temperature"] = self._data_modbus[
                "summer_temperature"
            ]

        self._data_modbus["current_temperature"] = await self._read_modbus_register(
            IMXW_ACTUAL_AIR_TEMPERATURE_REGISTER,
            self._data_modbus["current_temperature"],
        )

        # state heating/cooling/fan only/off
        self._data_modbus["on_off"] = await self._read_modbus_register(
            IMXW_STATE_READ_ON_OFF_REGISTER, self._data_modbus["on_off"]
        )

        # These registers are read always regardless of on/off state
        self._data_modbus["fan_only"] = await self._read_modbus_register(
            IMXW_STATE_READ_FAN_ONLY_REGISTER, self._data_modbus["fan_only"]
        )

        self._data_modbus["ev_water"] = await self._read_modbus_register(
            IMXW_STATE_READ_EV_WATER_REGISTER, self._data_modbus["ev_water"]
        )

        if self._data_modbus["on_off"]:
            if self._data_modbus["fan_only"] == CV_FAN_ON:
                self._data_modbus["hvac_mode"] = CV_MODE_FAN_ONLY
                self._data_modbus["hvac_action"] = CV_ACTION_FAN
            elif self._data_modbus["summer_winter"] == CV_MODE_SUMMER:
                self._data_modbus["hvac_mode"] = CV_MODE_COOL
                if self._data_modbus["ev_water"] == CV_WATER_CIRCULATING:
                    self._data_modbus["hvac_action"] = CV_ACTION_COOLING
                else:
                    self._data_modbus["hvac_action"] = CV_ACTION_IDLE
            else:
                self._data_modbus["hvac_mode"] = CV_MODE_HEAT
                if self._data_modbus["ev_water"] == CV_WATER_CIRCULATING:
                    self._data_modbus["hvac_action"] = CV_ACTION_HEATING
                else:
                    self._data_modbus["hvac_action"] = CV_ACTION_IDLE
        else:
            self._data_modbus["hvac_mode"] = CV_MODE_OFF
            self._data_modbus["hvac_action"] = CV_ACTION_OFF
            self._data_modbus["fan_only"] = CV_FAN_OFF

        # preset mode
        self._data_modbus["no_frost"] = await self._read_modbus_register(
            IMXW_PRESET_WRITE_NO_FROST_REGISTER, self._data_modbus["no_frost"]
        )
        self._data_modbus["eco_mode"] = await self._read_modbus_register(
            IMXW_PRESET_WRITE_POWER_SAVE_REGISTER, self._data_modbus["eco_mode"]
        )
        if self._data_modbus["no_frost"] == CV_MODE_ON:
            self._data_modbus["preset_mode"] = CV_PRESET_MODE_AWAY
        elif self._data_modbus["eco_mode"] == CV_MODE_ON:
            self._data_modbus["preset_mode"] = CV_PRESET_MODE_ECO
        else:
            self._data_modbus["preset_mode"] = CV_PRESET_MODE_NONE

        # fan speed

        self._data_modbus["fan_auto"] = await self._read_modbus_register(
            IMXW_STATE_READ_FAN_AUTO_REGISTER, self._data_modbus["fan_auto"]
        )

        if self._data_modbus["fan_auto"] == CV_FAN_ON:
            self._data_modbus["fan_mode"] = CV_FAN_AUTO
        else:
            self._data_modbus["fan_min"] = await self._read_modbus_register(
                IMXW_STATE_READ_FAN_MIN_SPEED_REGISTER, self._data_modbus["fan_min"]
            )

            if self._data_modbus["fan_min"] == CV_FAN_ON:
                self._data_modbus["fan_mode"] = CV_FAN_LOW
            else:
                self._data_modbus["fan_med"] = await self._read_modbus_register(
                    IMXW_STATE_READ_FAN_MED_SPEED_REGISTER, self._data_modbus["fan_med"]
                )

                if self._data_modbus["fan_med"] == CV_FAN_ON:
                    self._data_modbus["fan_mode"] = CV_FAN_MEDIUM
                else:
                    self._data_modbus["fan_max"] = await self._read_modbus_register(
                        IMXW_STATE_READ_FAN_MAX_SPEED_REGISTER,
                        self._data_modbus["fan_max"],
                    )

                    if self._data_modbus["fan_max"] == CV_FAN_ON:
                        self._data_modbus["fan_mode"] = CV_FAN_HIGH
                    else:
                        self._data_modbus["fan_mode"] = (
                            CV_FAN_AUTO  # fallback: all fan bits off
                        )

        self._data_modbus["exchanger_temperature"] = await self._read_modbus_register(
            IMXW_ACTUAL_WATER_TEMPERATURE_REGISTER,
            self._data_modbus["exchanger_temperature"],
        )

        # T2 probe (optional, 0 = not present)
        self._data_modbus["t2_temperature"] = await self._read_modbus_register(
            IMXW_T2_TEMPERATURE_REGISTER,
            self._data_modbus["t2_temperature"],
        )

        # Diagnostic registers 0x1022-0x102B
        self._data_modbus["relay5_fan_high"] = await self._read_modbus_register(
            IMXW_RELAY5_FAN_HIGH_REGISTER, self._data_modbus["relay5_fan_high"]
        )
        self._data_modbus["window_input"] = await self._read_modbus_register(
            IMXW_WINDOW_INPUT_REGISTER, self._data_modbus["window_input"]
        )
        self._data_modbus["pump_alarm_input"] = await self._read_modbus_register(
            IMXW_PUMP_ALARM_INPUT_REGISTER, self._data_modbus["pump_alarm_input"]
        )
        self._data_modbus["heater_present"] = await self._read_modbus_register(
            IMXW_HEATER_PRESENT_REGISTER, self._data_modbus["heater_present"]
        )
        self._data_modbus["analog_output"] = await self._read_modbus_register(
            IMXW_ANALOG_OUTPUT_REGISTER, self._data_modbus["analog_output"]
        )
        self._data_modbus["alarm_t1"] = await self._read_modbus_register(
            IMXW_ALARM_T1_REGISTER, self._data_modbus["alarm_t1"]
        )
        self._data_modbus["alarm_t2"] = await self._read_modbus_register(
            IMXW_ALARM_T2_REGISTER, self._data_modbus["alarm_t2"]
        )
        self._data_modbus["alarm_t3"] = await self._read_modbus_register(
            IMXW_ALARM_T3_REGISTER, self._data_modbus["alarm_t3"]
        )
        self._data_modbus["alarm_water_drain"] = await self._read_modbus_register(
            IMXW_ALARM_WATER_DRAIN_REGISTER, self._data_modbus["alarm_water_drain"]
        )

        self._data_modbus["external_probe_enabled"] = await self._read_modbus_register(
            IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_ENABLED_REGISTER,
            self._data_modbus["external_probe_enabled"],
        )

        # update true temperature if data is present
        if self._enable_actual_true_temperature is True:
            # enable the external probe if not enabled
            if self._data_modbus["external_probe_enabled"] == 0:
                await self._write_modbus_register(
                    IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_ENABLED_REGISTER, 1
                )
            # send anyway the temperature, also in cases the reading is the same value
            await self._write_modbus_register(
                IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_REGISTER,
                self._actual_true_temperature,
            )

        if self._data_modbus["external_probe_enabled"]:
            # reset the enable actual true temperature if no updates for at least 15 minutes
            if (
                self._last_time_true_temperature_sent
                + CLIMAVENETA_IMXW_TIMEOUT_TRUE_TEMPERATURE_SECONDS
            ) < time.time():
                self._enable_actual_true_temperature = False
                await self._write_modbus_register(
                    IMXW_AMBIENT_TEMP_EXTERNAL_PROBE_ENABLED_REGISTER, 0
                )

        return self._data_modbus

    async def _async_update_ilife2(self):
        """Fetch data from iLife device."""

        # setpoint and actuals
        self._data_modbus["target_temperature"] = await self._read_modbus_register(
            ILIFE_STATE_READ_SETPOINT_REGISTER, self._data_modbus["target_temperature"]
        )

        self._data_modbus["current_temperature"] = await self._read_modbus_register(
            ILIFE_ACTUAL_AIR_TEMPERATURE_REGISTER,
            self._data_modbus["current_temperature"],
        )

        self._data_modbus["exchanger_temperature"] = await self._read_modbus_register(
            ILIFE_ACTUAL_WATER_TEMPERATURE_REGISTER,
            self._data_modbus["exchanger_temperature"],
        )

        self._data_modbus["fan_speed_rpm"] = await self._read_modbus_register(
            ILIFE_ACTUAL_FAN_SPEED_RPM_REGISTER,
            self._data_modbus["fan_speed_rpm"],
        )

        # state heating/cooling/fan only/off
        self._data_modbus["man_register"] = await self._read_modbus_register(
            ILIFE_STATE_MAN_REGISTER, self._data_modbus["man_register"]
        )

        self._data_modbus["program_register"] = await self._read_modbus_register(
            ILIFE_STATE_READ_PROGRAM_REGISTER, self._data_modbus["program_register"]
        )

        if self._data_modbus["program_register"] != -1:
            if (self._data_modbus["program_register"] & (1 << 7)) == 0b10000000:
                self._data_modbus["on_off"] = CV_MODE_OFF  # standby
            else:
                self._data_modbus["on_off"] = CV_MODE_ON  # normal operation
        else:
            self._data_modbus["on_off"] = (
                CV_MODE_OFF  # force off in case data read isn't valid
            )

        # STAT register (104) - read always regardless of on/off state
        self._data_modbus["stat_register"] = await self._read_modbus_register(
            ILIFE_STATE_READ_REGISTER, self._data_modbus["stat_register"]
        )

        # OUT register (009) - read always regardless of on/off state
        # Bit 2: CHILLER, Bit 3: BOILER
        self._data_modbus["out_register"] = await self._read_modbus_register(
            ILIFE_STATE_OUT_REGISTER, self._data_modbus["out_register"]
        )

        if self._data_modbus["on_off"] == CV_MODE_ON:
            if self._data_modbus["man_register"] == 0:
                self._data_modbus["hvac_mode"] = CV_MODE_HEAT_COOL
            elif self._data_modbus["man_register"] == 3:
                self._data_modbus["hvac_mode"] = CV_MODE_HEAT
            elif self._data_modbus["man_register"] == 5:
                self._data_modbus["hvac_mode"] = CV_MODE_COOL
            elif self._data_modbus["man_register"] != -1:
                self._data_modbus["hvac_mode"] = (
                    CV_MODE_OFF  # not a valid number, this register should always be 0, 3 or 5.
                )

            if self._data_modbus["stat_register"] != -1:
                if (self._data_modbus["stat_register"] & (1 << 1) == 0) and (
                    self._data_modbus["stat_register"] & (1 << 0) == 0
                ):
                    self._data_modbus["hvac_action"] = CV_ACTION_IDLE
                elif self._data_modbus["stat_register"] & (1 << 1) == 0:
                    self._data_modbus["hvac_action"] = CV_ACTION_COOLING
                else:
                    self._data_modbus["hvac_action"] = CV_ACTION_HEATING

            # fan speed
            if self._data_modbus["program_register"] != -1:
                if (self._data_modbus["program_register"] & 0b111) == 0b000:
                    self._data_modbus["fan_mode"] = CV_FAN_AUTO
                elif (self._data_modbus["program_register"] & 0b111) == 0b001:
                    self._data_modbus["fan_mode"] = CV_FAN_LOW
                elif (self._data_modbus["program_register"] & 0b111) == 0b010:
                    self._data_modbus["fan_mode"] = CV_FAN_MEDIUM
                elif (self._data_modbus["program_register"] & 0b111) == 0b011:
                    self._data_modbus["fan_mode"] = CV_FAN_HIGH
                else:
                    self._data_modbus["fan_mode"] = CV_FAN_OFF  # unknown state
        elif self._data_modbus["on_off"] == CV_MODE_OFF:
            self._data_modbus["hvac_mode"] = CV_MODE_OFF
            self._data_modbus["hvac_action"] = CV_ACTION_OFF
            self._data_modbus["fan_mode"] = CV_FAN_OFF

        self._data_modbus["fan_only"] = CV_FAN_OFF  # not possible, always off

        # alarm register
        self._data_modbus["alarm_register"] = await self._read_modbus_register(
            ILIFE_STATE_READ_ALARM_REGISTER, self._data_modbus["alarm_register"]
        )

        return self._data_modbus

    # Handle room temperature & humidity

    def get_current_temp(self) -> float:
        """Get the current room temperature."""
        return float(self._data_modbus["current_temperature"]) / 10.0

    def get_target_temp(self) -> float:
        """Get the target room temperature."""
        return float(self._data_modbus["target_temperature"]) / 10.0

    def get_min_voltage_winter(self) -> float:
        """Get the fan voltage for summer/winter min/max, 1.0 to 10.0V."""
        return float(self._data_modbus["min_voltage_winter"]) / 10.0

    def get_max_voltage_winter(self) -> float:
        """Get the fan voltage for summer/winter min/max, 1.0 to 10.0V."""
        return float(self._data_modbus["max_voltage_winter"]) / 10.0

    def get_min_voltage_summer(self) -> float:
        """Get the fan voltage for summer/winter min/max, 1.0 to 10.0V."""
        return float(self._data_modbus["min_voltage_summer"]) / 10.0

    def get_max_voltage_summer(self) -> float:
        """Get the fan voltage for summer/winter min/max, 1.0 to 10.0V."""
        return float(self._data_modbus["max_voltage_summer"]) / 10.0
    
    def get_max_water_temp_summer(self) -> float:
        """Get the max water temp for summer - cooling """
        return float(self._data_modbus["max_water_temp_summer"]) / 10.0
    
    def get_min_water_temp_winter(self) -> float:
        """Get the min water temp for winter - heating """
        return float(self._data_modbus["min_water_temp_winter"]) / 10.0

    def get_setpoint_hysteresis(self) -> float:
        """Get the setpoint hysteresis (I-rL) in °C."""
        return float(self._data_modbus["setpoint_hysteresis"]) / 10.0

    def get_dead_zone_center(self) -> float:
        """Get the dead zone center set (dEds) in °C."""
        return float(self._data_modbus["dead_zone_center"]) / 10.0

    def get_dead_zone_range(self) -> float:
        """Get the dead zone range (dEdr) in °C."""
        return float(self._data_modbus["dead_zone_range"]) / 10.0

    def get_t1_compensation_delta(self) -> float:
        """Get the T1 compensation delta (t1dS) in °C."""
        return float(self._data_modbus["t1_compensation_delta"]) / 10.0

    def get_antistrat_wait_time(self) -> int:
        """Get the anti-stratification wait time (Ft1) in minutes."""
        return int(self._data_modbus["antistrat_wait_time"])

    def get_t1_compensation_base_summer(self) -> float:
        """Get the T1 compensation base summer (t1SE) in °C."""
        return float(self._data_modbus["t1_compensation_base_summer"]) / 10.0

    def get_antistrat_time_summer(self) -> int:
        """Get the anti-stratification time summer (Ft2E) in seconds."""
        return int(self._data_modbus["antistrat_time_summer"])

    def get_t1_compensation_base_winter(self) -> float:
        """Get the T1 compensation base winter (t1SI) in °C."""
        return float(self._data_modbus["t1_compensation_base_winter"]) / 10.0

    def get_antistrat_time_winter(self) -> int:
        """Get the anti-stratification time winter (Ft2I) in seconds."""
        return int(self._data_modbus["antistrat_time_winter"])

    def get_offset_ntc_etn(self) -> float:
        """Get the offset for NTC ETN probe (OFS) in °C."""
        return float(self._data_modbus["offset_ntc_etn"]) / 10.0

    def get_t2_temperature(self) -> float | None:
        """Get the T2 probe temperature in °C (None if probe not present/disconnected).

        The register is sig16 (°C*10).  When the probe is absent the device
        returns a sentinel (often 0xFFFF / 0x7FFF) that appears as an absurd
        temperature.  Any unsigned raw value outside the sane physical range
        50..1000 (i.e. 5 °C .. 100 °C) is treated as 'probe not connected'.
        A T2 water probe realistically reads between ~5 °C and ~80 °C.
        """
        raw = self._data_modbus["t2_temperature"]
        if raw < 50 or raw > 1000:
            return None
        return float(raw) / 10.0

    async def set_antistrat_wait_time(self, value: int) -> bool:
        """Set the anti-stratification wait time (Ft1) in minutes (10-20)."""
        result = await self._write_modbus_register(IMXW_ANTISTRAT_WAIT_TIME_REGISTER, int(value))
        if result:
            self._data_modbus["antistrat_wait_time"] = int(value)
        return result

    async def set_t1_compensation_base_summer(self, value: float) -> bool:
        """Set the T1 compensation base summer (t1SE) in °C (0.5-2.0)."""
        raw = int(round(value * 10.0))
        result = await self._write_modbus_register(IMXW_T1_COMPENSATION_BASE_SUMMER_REGISTER, raw)
        if result:
            self._data_modbus["t1_compensation_base_summer"] = raw
        return result

    async def set_antistrat_time_summer(self, value: int) -> bool:
        """Set the anti-stratification time summer (Ft2E) in seconds (30-180)."""
        result = await self._write_modbus_register(IMXW_ANTISTRAT_TIME_SUMMER_REGISTER, int(value))
        if result:
            self._data_modbus["antistrat_time_summer"] = int(value)
        return result

    async def set_t1_compensation_base_winter(self, value: float) -> bool:
        """Set the T1 compensation base winter (t1SI) in °C (0.5-5.0)."""
        raw = int(round(value * 10.0))
        result = await self._write_modbus_register(IMXW_T1_COMPENSATION_BASE_WINTER_REGISTER, raw)
        if result:
            self._data_modbus["t1_compensation_base_winter"] = raw
        return result

    async def set_antistrat_time_winter(self, value: int) -> bool:
        """Set the anti-stratification time winter (Ft2I) in seconds (30-180)."""
        result = await self._write_modbus_register(IMXW_ANTISTRAT_TIME_WINTER_REGISTER, int(value))
        if result:
            self._data_modbus["antistrat_time_winter"] = int(value)
        return result

    def get_hvac_mode(self) -> int:
        """Get the hvac mode (set status)."""
        return int(self._data_modbus["hvac_mode"])

    def get_hvac_action(self) -> int:
        """Get the hvac action (actual status)."""
        return int(self._data_modbus["hvac_action"])

    def get_preset_mode(self) -> int:
        """Get the preset mode (actual status)."""
        return int(self._data_modbus["preset_mode"])

    def get_fan_speed_rpm(self) -> int:
        """Get the hvac mode (set status)."""
        return int(self._data_modbus["fan_speed_rpm"])

    def get_fan_mode(self) -> int:
        """Get the fan speed."""
        return int(self._data_modbus["fan_mode"])

    def get_fan_only(self) -> bool:
        """Get the fan only flag."""
        return bool(self._data_modbus["fan_only"])

    def get_on_off(self) -> bool:
        """Get the status of the device on or off."""
        return bool(self._data_modbus["on_off"])

    def get_exchanger_temperature(self) -> float:
        """Get the water-air exchanger temperature."""
        return float(self._data_modbus["exchanger_temperature"]) / 10.0

    def get_continuous_ventilation(self) -> bool:
        """Get continuous ventilation status (derived from Dip 1, no-resistance machines)."""
        return bool(self._data_modbus["continuous_ventilation"])

    def get_machine_slave(self) -> bool:
        """Get whether machine is configured as Slave (Dip 2: 1=Slave, 0=Master)."""
        return bool(self._data_modbus["machine_slave"])

    def get_relay5_fan_high(self) -> bool:
        """Get Relay 5 FAN HIGH / Inverter on status."""
        return bool(self._data_modbus["relay5_fan_high"])

    def get_window_input(self) -> bool:
        """Get the window digital input (0=Closed, 1=Open)."""
        return bool(self._data_modbus["window_input"])

    def get_pump_alarm_input(self) -> bool:
        """Get the pump alarm digital input (0=Closed, 1=Open)."""
        return bool(self._data_modbus["pump_alarm_input"])

    def get_heater_present(self) -> bool:
        """Get whether a heater is present (0=Absent, 1=Present)."""
        return bool(self._data_modbus["heater_present"])

    def get_analog_output(self) -> float:
        """Get the analog output 0-10V (stored as Volt*10)."""
        return float(self._data_modbus["analog_output"]) / 10.0

    def get_alarm_t1(self) -> bool:
        """Get T1 fault alarm."""
        return bool(self._data_modbus["alarm_t1"])

    def get_alarm_t2(self) -> bool:
        """Get T2 fault alarm."""
        return bool(self._data_modbus["alarm_t2"])

    def get_alarm_t3(self) -> bool:
        """Get T3 fault alarm."""
        return bool(self._data_modbus["alarm_t3"])

    def get_alarm_water_drain(self) -> bool:
        """Get water drain level alarm."""
        return bool(self._data_modbus["alarm_water_drain"])

    @staticmethod
    def __hex_to_custom_string(hex_value: int) -> str:
        hex_str = f"{hex_value:X}"

        if len(hex_str) < 3:
            hex_str = hex_str.zfill(3)

        integer_part = hex_str[:-2]
        fractional_part = hex_str[-2:]
        result = f"{integer_part}.{fractional_part}"

        return result

    def get_firmware_version(self) -> str:
        """Get the firmware version."""
        return self._firmware_version_text

    def get_modbus_address(self) -> int:
        """Get the modbus address of the device."""
        return int(self._data_modbus["modbus_address"])

    def get_alarm_flag(self, bit: int) -> bool:
        """Get a specific alarm flag bit from register 105."""
        return bool(self._data_modbus["alarm_register"] & (1 << bit))


    def get_boiler_water_relay_on_off(self) -> bool:
        """Get the hot/cold water relay. On means pump request power on. Off --> pump off."""
        relay_on = False

        if self._unit_type == CLIMAVENETA_ILIFE2:
            if (self._data_modbus["out_register"] & (1 << 3)) != 0:
                # Heater relay enabled
                relay_on = True
            elif (self._data_modbus["out_register"] & (1 << 2)) != 0:
                # Chiller relay enabled
                relay_on = True
        else:
            # iMXW
            if self._data_modbus["ev_water"] == CV_WATER_CIRCULATING:
                # The EV1 water is also controlling the external pump closure contact relay
                relay_on = True

        return relay_on

    async def set_target_temp(self, temp):
        """Set the target room temperature."""

        if (
            self._unit_type == CLIMAVENETA_IMXW
            and self._data_modbus["summer_winter"] == CV_MODE_WINTER
        ):
            reg_address = IMXW_TARGET_TEMPERATURE_WINTER_REGISTER
        elif (
            self._unit_type == CLIMAVENETA_IMXW
            and self._data_modbus["summer_winter"] == CV_MODE_SUMMER
        ):
            reg_address = IMXW_TARGET_TEMPERATURE_SUMMER_REGISTER
        else:
            reg_address = ILIFE_TARGET_TEMPERATURE_REGISTER

        new_value = round(temp * 10.0)

        if self._data_modbus["target_temperature"] != new_value:
            # write target temperature only if setpoint changes from the one already set
            result = await self._write_modbus_register(reg_address, new_value)
            if result:
                self._data_modbus["target_temperature"] = new_value
        else:
            result = True

        return result

    async def turn_on(self):
        """Power on the device."""

        if self._unit_type == CLIMAVENETA_IMXW:
            await self._write_modbus_register(
                IMXW_STATE_WRITE_ON_OFF_REGISTER, CV_MODE_ON
            )
        else:
            await self._write_modbus_register(ILIFE_STATE_READ_PROGRAM_REGISTER, 0)

        self._data_modbus["on_off"] = CV_MODE_ON

    async def set_actual_true_temperature(self, temp):
        """Set the actual true room temperature read from an external thermostat."""

        if self._unit_type == CLIMAVENETA_IMXW:
            self._actual_true_temperature = int(round(temp * 10.0))
            self._enable_actual_true_temperature = True
            self._last_time_true_temperature_sent = time.time()

    async def set_fan_speed(self, fan_mode):
        """Set the fan mode."""

        if fan_mode in (CV_FAN_AUTO, CV_FAN_LOW, CV_FAN_MEDIUM, CV_FAN_HIGH):
            if self._unit_type == CLIMAVENETA_IMXW:
                reg_address = IMXW_STATE_WRITE_FAN_SPEED_REGISTER
            else:
                reg_address = ILIFE_STATE_READ_PROGRAM_REGISTER
                if self._data_modbus["on_off"] == CV_MODE_OFF:
                    fan_mode = fan_mode + (
                        1 << 7
                    )  # keep it powered off (standby) if fan mode is set when off.

            if self._data_modbus["fan_mode"] != fan_mode:
                await self._write_modbus_register(reg_address, fan_mode)
                self._data_modbus["fan_mode"] = fan_mode

    async def set_hvac_mode(self, hvac_mode):
        """Set the hvac mode."""

        if self._unit_type == CLIMAVENETA_IMXW and hvac_mode == CV_MODE_OFF:
            # set the device to OFF
            if self._data_modbus["on_off"] != CV_MODE_OFF:
                await self._write_modbus_register(
                    IMXW_STATE_WRITE_ON_OFF_REGISTER, CV_MODE_OFF
                )
                self._data_modbus["on_off"] = CV_MODE_OFF
        elif self._unit_type == CLIMAVENETA_IMXW:
            # set the device to the selected mode
            if self._data_modbus["on_off"] == CV_MODE_OFF:
                # if the device is off, then power it on and only then set the mode
                await self._write_modbus_register(
                    IMXW_STATE_WRITE_ON_OFF_REGISTER, CV_MODE_ON
                )
                self._data_modbus["on_off"] = CV_MODE_ON

            if self._data_modbus["hvac_mode"] != hvac_mode:
                if hvac_mode == CV_MODE_HEAT:
                    heatcool = CV_IMXW_MODE_WINTER
                elif hvac_mode == CV_MODE_COOL:
                    heatcool = CV_IMXW_MODE_SUMMER
                elif hvac_mode == CV_MODE_HEAT_COOL:
                    heatcool = CV_IMXW_MODE_AUTO
                elif hvac_mode == CV_MODE_FAN_ONLY:
                    heatcool = CV_IMXW_MODE_FAN_ONLY

                await self._write_modbus_register(
                    IMXW_STATE_WRITE_MODE_REGISTER, heatcool
                )
                self._data_modbus["hvac_mode"] = hvac_mode

        elif hvac_mode == CV_MODE_OFF:
            # iLife device
            # set the device to OFF
            await self._write_modbus_register(
                ILIFE_STATE_READ_PROGRAM_REGISTER, 0b10000000
            )
            self._data_modbus["on_off"] = CV_MODE_OFF
            self._data_modbus["hvac_mode"] = hvac_mode

        else:
            # iLife device
            # set the device to the selected mode
            if self._data_modbus["on_off"] == CV_MODE_OFF:
                # if the device is off, then power it on and then set the mode
                await self._write_modbus_register(ILIFE_STATE_READ_PROGRAM_REGISTER, 0)
                self._data_modbus["on_off"] = CV_MODE_ON

            if hvac_mode == CV_MODE_COOL:
                winter_summer = 5  # summer
            elif hvac_mode == CV_MODE_HEAT_COOL:
                winter_summer = 0  # auto
            else:
                winter_summer = 3  # winter

            await self._write_modbus_register(ILIFE_STATE_MAN_REGISTER, winter_summer)
            self._data_modbus["hvac_mode"] = hvac_mode

        # update the whole status from the device to update the action and status
        await self.async_update()

    async def set_preset_mode(self, preset_mode):
        """Set the preset (none, eco, away, etc.) mode."""
        if self._unit_type == CLIMAVENETA_IMXW:
            if preset_mode == CV_PRESET_MODE_NONE:
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_NO_FROST_REGISTER, CV_MODE_OFF
                )
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_POWER_SAVE_REGISTER, CV_MODE_OFF
                )
                self._data_modbus["preset_mode"] = preset_mode
            elif preset_mode == CV_PRESET_MODE_ECO:
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_NO_FROST_REGISTER, CV_MODE_OFF
                )
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_POWER_SAVE_REGISTER, CV_MODE_ON
                )
                self._data_modbus["preset_mode"] = preset_mode
            elif preset_mode == CV_PRESET_MODE_AWAY:
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_NO_FROST_REGISTER, CV_MODE_ON
                )
                await self._write_modbus_register(
                    IMXW_PRESET_WRITE_POWER_SAVE_REGISTER, CV_MODE_OFF
                )
                self._data_modbus["preset_mode"] = preset_mode

    async def _read_modbus_register(self, register, old_value):
        """Queue a modbus read."""
        _LOGGER.info(
            "Calling read register slave %d unit type %s register %d",
            self._slave,
            self._unit_type,
            register,
        )
        try:
            future = cv_pool.submit(
                self.read_register,
                register=register,
                count=1,
                slave=self._slave,
            )  # does not block
            result = future.result()  # blocks

            if not hasattr(result, "registers"):
                return old_value

            return int(result.registers[0])

        except ModbusException:
            _LOGGER.info(
                "Exception on read register slave %d unit type %s register %d",
                self._slave,
                self._unit_type,
                register,
            )
        return old_value

    async def _write_modbus_register(self, register, value) -> bool:
        """Queue a modbus write."""
        future = cv_pool.submit(
            self.write_register,
            register=register,
            value=value,
            slave=self._slave,
        )  # does not block
        result = future.result()  # blocks

        if not result:
            return False
        return True

    def read_register(self, register, count, slave) -> ModbusPDU:  # type: ignore[name-defined]
        """Sync read of a modbus register."""
        lazy_error_count = CLIMAVENETA_MODBUS_LAZY_ERROR_COUNT
        rr = 0  # type: ignore[assignment]
        while lazy_error_count > 0:
            try:
                rr = ClimavenetaLock.port.read_holding_registers(
                    register, count=count, device_id=slave
                )
                time.sleep(CLIMAVENETA_MODBUS_OK_SLEEP_SECONDS)
            except ModbusException:
                _LOGGER.debug(
                    "Read exception, retry %d on slave %d", lazy_error_count, slave
                )
                time.sleep(CLIMAVENETA_MODBUS_KO_SLEEP_SECONDS)
                lazy_error_count -= 1
                continue
            if not hasattr(rr, "registers"):
                _LOGGER.debug(
                    "Read returned no registers, retry %d on slave %d", lazy_error_count, slave
                )
                lazy_error_count -= 1
                continue
            break

        return rr  # type: ignore[return-value]

    def write_register(self, register, value, slave) -> bool:
        """Sync write of a modbus register."""
        lazy_error_count = CLIMAVENETA_MODBUS_LAZY_ERROR_COUNT
        while lazy_error_count > 0:
            try:
                rr = ClimavenetaLock.port.write_register(
                    register, value=value, device_id=slave
                )
                time.sleep(CLIMAVENETA_MODBUS_OK_SLEEP_SECONDS)
            except ModbusException:
                _LOGGER.debug(
                    "Write exception, retry %d on slave %d", lazy_error_count, slave
                )
                time.sleep(CLIMAVENETA_MODBUS_KO_SLEEP_SECONDS)
                lazy_error_count -= 1
                continue
            if not hasattr(rr, "registers"):
                _LOGGER.debug(
                    "Write returned no registers, retry %d on slave %d", lazy_error_count, slave
                )
                lazy_error_count -= 1
                continue
            break

        return True
