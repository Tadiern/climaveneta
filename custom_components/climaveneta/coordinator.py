"""Coordinator for the climaveneta iMXW and iLife2 AC."""

import logging

# from pymodbus.client import AsyncModbusSerialClient
from pymodbus.client import ModbusSerialClient
from pymodbus.framer import FramerType

# from homeassistant.components.modbus import ModbusHub
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import pyclimaveneta
from .const import (
    CLIMAVENETA_ALARM_2AIR_M5,
    CLIMAVENETA_ALARM_ACQ_DAN,
    CLIMAVENETA_ALARM_AIR,
    CLIMAVENETA_ALARM_COM,
    CLIMAVENETA_ALARM_FILTRO,
    CLIMAVENETA_ALARM_GRID,
    CLIMAVENETA_ALARM_H2,
    CLIMAVENETA_ALARM_H2_NID,
    CLIMAVENETA_ALARM_H4,
    CLIMAVENETA_ALARM_H4_NID,
    CLIMAVENETA_ALARM_HI_RES,
    CLIMAVENETA_ALARM_MOT,
    CLIMAVENETA_ANTISTRAT_TIME_SUMMER,
    CLIMAVENETA_ANTISTRAT_TIME_WINTER,
    CLIMAVENETA_ANTISTRAT_WAIT_TIME,
    CLIMAVENETA_DEAD_ZONE_CENTER,
    CLIMAVENETA_DEAD_ZONE_RANGE,
    CLIMAVENETA_EXCHANGER_TEMPERATURE,
    CLIMAVENETA_FAN_SPEED_RPM,
    CLIMAVENETA_HVAC_STATUS,
    CLIMAVENETA_IMXW,
    CLIMAVENETA_MAX_SUMMER,
    CLIMAVENETA_MAX_WINTER,
    CLIMAVENETA_MIN_SUMMER,
    CLIMAVENETA_MIN_WINTER,
    CLIMAVENETA_MODBUS_ADDRESS,
    CLIMAVENETA_MOTOR_SPEED_SET,
    CLIMAVENETA_PUMP_RELAY,
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
    CLIMAVENETA_SETPOINT_HYSTERESIS,
    CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER,
    CLIMAVENETA_T1_COMPENSATION_BASE_WINTER,
    CLIMAVENETA_T1_COMPENSATION_DELTA,
    CLIMAVENETA_OFFSET_NTC_ETN,
    CLIMAVENETA_T2_TEMPERATURE,
    DOMAIN,
    SCAN_INTERVAL,
    CLIMAVENETA_ACTUAL_TEMPERATURE,
    CLIMAVENETA_MAX_WATER_TEMP_SUMMER,
    CLIMAVENETA_MIN_WATER_TEMP_WINTER,
)

_LOGGER = logging.getLogger(__name__)


class ClimavenetaCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching Climaveneta data."""

    def __init__(
        self, hass: HomeAssistant, device_type: str, hub: str, slaveid: int, name
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )

        if device_type == CLIMAVENETA_IMXW:
            self.device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{hub!s}_{slaveid!s}")},
                manufacturer="Climaveneta",
                name=name,
                model="i-MXW",
                sw_version="unknown",
            )
        else:
            self.device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{hub!s}_{slaveid!s}")},
                manufacturer="Climaveneta",
                name=name,
                model="iLife",
                sw_version="unknown",
            )

        self.device_type = device_type
        self.hub = hub
        self.slave_id = slaveid
        self.name = name
        self.api: pyclimaveneta.ClimavenetaAPI
        self.data_readbacks: dict[str, int] = {}

    async def async_create(self):
        """Create serial connection."""
        # modbus_client = AsyncModbusSerialClient(
        # Use the configured hub value as the serial device path (e.g. /dev/ttyAMA0)
        # Home Assistant may later provide a Modbus hub object here; currently
        # the config stores a string path so we pass it directly to pymodbus.
        _LOGGER.debug(
            "Creating Modbus serial client for device %s on port %s with slave ID %d",
            self.device_type,
            self.hub,
            self.slave_id,
        )
        modbus_client = ModbusSerialClient(
            self.hub,
            bytesize=8,
            baudrate=9600,
            parity="N",
            framer=FramerType.RTU,
            stopbits=1,
            retries=3,
            reconnect_delay=100,
            timeout=1,
        )

        if self.device_type == CLIMAVENETA_IMXW:
            unit_model = pyclimaveneta.CLIMAVENETA_IMXW
        else:
            unit_model = pyclimaveneta.CLIMAVENETA_ILIFE2

        self.api = pyclimaveneta.ClimavenetaAPI(
            modbus_client, self.slave_id, unit_model
        )

        # update configuration data here at creation
        await self.api.async_read_configuration()
        self.data_readbacks[CLIMAVENETA_MIN_WINTER] = self.api.get_min_voltage_winter()
        self.data_readbacks[CLIMAVENETA_MAX_WINTER] = self.api.get_max_voltage_winter()
        self.data_readbacks[CLIMAVENETA_MIN_SUMMER] = self.api.get_min_voltage_summer()
        self.data_readbacks[CLIMAVENETA_MAX_SUMMER] = self.api.get_max_voltage_summer()
        self.data_readbacks[CLIMAVENETA_MAX_WATER_TEMP_SUMMER] = self.api.get_max_water_temp_summer()
        self.data_readbacks[CLIMAVENETA_MIN_WATER_TEMP_WINTER] = self.api.get_min_water_temp_winter()
        self.data_readbacks[CLIMAVENETA_MODBUS_ADDRESS] = self.api.get_modbus_address()

        # IMXW configuration registers (read once at startup)
        if self.device_type == CLIMAVENETA_IMXW:
            self.data_readbacks[CLIMAVENETA_SETPOINT_HYSTERESIS] = self.api.get_setpoint_hysteresis()
            self.data_readbacks[CLIMAVENETA_DEAD_ZONE_CENTER] = self.api.get_dead_zone_center()
            self.data_readbacks[CLIMAVENETA_DEAD_ZONE_RANGE] = self.api.get_dead_zone_range()
            self.data_readbacks[CLIMAVENETA_T1_COMPENSATION_DELTA] = self.api.get_t1_compensation_delta()
            self.data_readbacks[CLIMAVENETA_ANTISTRAT_WAIT_TIME] = self.api.get_antistrat_wait_time()
            self.data_readbacks[CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER] = self.api.get_t1_compensation_base_summer()
            self.data_readbacks[CLIMAVENETA_ANTISTRAT_TIME_SUMMER] = self.api.get_antistrat_time_summer()
            self.data_readbacks[CLIMAVENETA_T1_COMPENSATION_BASE_WINTER] = self.api.get_t1_compensation_base_winter()
            self.data_readbacks[CLIMAVENETA_ANTISTRAT_TIME_WINTER] = self.api.get_antistrat_time_winter()
            self.data_readbacks[CLIMAVENETA_OFFSET_NTC_ETN] = self.api.get_offset_ntc_etn()
            self.data_readbacks[CLIMAVENETA_CONTINUOUS_VENTILATION] = self.api.get_continuous_ventilation()
            self.data_readbacks[CLIMAVENETA_MACHINE_SLAVE] = self.api.get_machine_slave()

        fw = self.api.get_firmware_version()

        self.device_info = DeviceInfo(
            identifiers=self.device_info["identifiers"],
            manufacturer=self.device_info["manufacturer"],
            name=self.device_info["name"],
            model=self.device_info["model"],
            sw_version=fw,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        await self.api.async_update()
        # internally save the values for the sensor entity.
        # eventually, any value should be stored in here.
        self.data_readbacks[CLIMAVENETA_EXCHANGER_TEMPERATURE] = (
            self.api.get_exchanger_temperature()
        )
        self.data_readbacks[CLIMAVENETA_FAN_SPEED_RPM] = self.api.get_fan_speed_rpm()

        # iMXW T2 probe (optional diagnostic)
        if self.device_type == CLIMAVENETA_IMXW:
            self.data_readbacks[CLIMAVENETA_T2_TEMPERATURE] = (
                self.api.get_t2_temperature()
            )
        self.data_readbacks[CLIMAVENETA_PUMP_RELAY] = (
            self.api.get_boiler_water_relay_on_off()
        )
        self.data_readbacks[CLIMAVENETA_ACTUAL_TEMPERATURE] = (
            self.api.get_current_temp()
        )
        self.data_readbacks[CLIMAVENETA_HVAC_STATUS] = (
            self.api.get_hvac_action()
        )

        # iMXW diagnostic registers (0x1022-0x102B)
        if self.device_type == CLIMAVENETA_IMXW:
            self.data_readbacks[CLIMAVENETA_RELAY5_FAN_HIGH] = self.api.get_relay5_fan_high()
            self.data_readbacks[CLIMAVENETA_WINDOW_INPUT] = self.api.get_window_input()
            self.data_readbacks[CLIMAVENETA_PUMP_ALARM_INPUT] = self.api.get_pump_alarm_input()
            self.data_readbacks[CLIMAVENETA_HEATER_PRESENT] = self.api.get_heater_present()
            self.data_readbacks[CLIMAVENETA_ANALOG_OUTPUT] = self.api.get_analog_output()
            self.data_readbacks[CLIMAVENETA_ALARM_T1] = self.api.get_alarm_t1()
            self.data_readbacks[CLIMAVENETA_ALARM_T2] = self.api.get_alarm_t2()
            self.data_readbacks[CLIMAVENETA_ALARM_T3] = self.api.get_alarm_t3()
            self.data_readbacks[CLIMAVENETA_ALARM_WATER_DRAIN] = self.api.get_alarm_water_drain()

        # iLife2 specific readbacks
        if self.device_type != CLIMAVENETA_IMXW:
            self.data_readbacks[CLIMAVENETA_REAL_SETPOINT] = (
                self.api.get_target_temp()
            )
            self.data_readbacks[CLIMAVENETA_MOTOR_SPEED_SET] = (
                self.api.get_fan_speed_rpm()
            )

        # iLife2 alarm flags (bit-by-bit from register 105)
        if self.device_type != CLIMAVENETA_IMXW:
            self.data_readbacks[CLIMAVENETA_ALARM_COM] = self.api.get_alarm_flag(0)
            self.data_readbacks[CLIMAVENETA_ALARM_AIR] = self.api.get_alarm_flag(1)
            self.data_readbacks[CLIMAVENETA_ALARM_H4] = self.api.get_alarm_flag(2)
            self.data_readbacks[CLIMAVENETA_ALARM_ACQ_DAN] = self.api.get_alarm_flag(3)
            self.data_readbacks[CLIMAVENETA_ALARM_H2] = self.api.get_alarm_flag(4)
            self.data_readbacks[CLIMAVENETA_ALARM_H4_NID] = self.api.get_alarm_flag(5)
            self.data_readbacks[CLIMAVENETA_ALARM_HI_RES] = self.api.get_alarm_flag(6)
            self.data_readbacks[CLIMAVENETA_ALARM_MOT] = self.api.get_alarm_flag(7)
            self.data_readbacks[CLIMAVENETA_ALARM_GRID] = self.api.get_alarm_flag(8)
            self.data_readbacks[CLIMAVENETA_ALARM_H2_NID] = self.api.get_alarm_flag(9)
            self.data_readbacks[CLIMAVENETA_ALARM_FILTRO] = self.api.get_alarm_flag(10)
            self.data_readbacks[CLIMAVENETA_ALARM_2AIR_M5] = self.api.get_alarm_flag(11)

        
