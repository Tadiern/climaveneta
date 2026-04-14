"""Support for the Mitsubishi-Climaveneta iMXW and iLife2 fancoil series."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ClimavenetaCoordinator
from .const import (
    CLIMAVENETA_DEAD_ZONE_CENTER,
    CLIMAVENETA_DEAD_ZONE_RANGE,
    CLIMAVENETA_EXCHANGER_TEMPERATURE,
    CLIMAVENETA_HVAC_STATUS,
    CLIMAVENETA_ILIFE2,
    CLIMAVENETA_IMXW,
    CLIMAVENETA_MAX_SUMMER,
    CLIMAVENETA_MAX_WINTER,
    CLIMAVENETA_MIN_SUMMER,
    CLIMAVENETA_MIN_WINTER,
    CLIMAVENETA_ACTUAL_TEMPERATURE,
    CLIMAVENETA_MIN_WATER_TEMP_WINTER,
    CLIMAVENETA_MAX_WATER_TEMP_SUMMER,
    CLIMAVENETA_ANALOG_OUTPUT,
    CLIMAVENETA_MODBUS_ADDRESS,
    CLIMAVENETA_MOTOR_SPEED_SET,
    CLIMAVENETA_OFFSET_NTC_ETN,
    CLIMAVENETA_REAL_SETPOINT,
    CLIMAVENETA_SETPOINT_HYSTERESIS,
    CLIMAVENETA_T1_COMPENSATION_DELTA,
    CLIMAVENETA_T2_TEMPERATURE,
    DOMAIN,
)
from .pyclimaveneta import (
    CV_ACTION_COOLING,
    CV_ACTION_FAN,
    CV_ACTION_HEATING,
    CV_ACTION_IDLE,
    CV_ACTION_OFF,
)


HVAC_STATUS_OPTIONS = ["off", "idle", "fan", "cooling", "heating"]

HVAC_ACTION_TO_STRING = {
    CV_ACTION_OFF: "off",
    CV_ACTION_IDLE: "idle",
    CV_ACTION_FAN: "fan",
    CV_ACTION_COOLING: "cooling",
    CV_ACTION_HEATING: "heating",
}


class ClimavenetaSensorEntityDescription(SensorEntityDescription):
    """Class describing Climaveneta sensor entities."""

    attrs: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


IMXW_SENSOR_TYPES: tuple[ClimavenetaSensorEntityDescription, ...] = (
    ClimavenetaSensorEntityDescription(
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_EXCHANGER_TEMPERATURE,
    ),
    ClimavenetaSensorEntityDescription(
        name="Min. Winter Fan Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MIN_WINTER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Max. Winter Fan Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MAX_WINTER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Min. Summer Fan Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MIN_SUMMER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Max. Summer Fan Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MAX_SUMMER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Actual Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_ACTUAL_TEMPERATURE,
    ),
    ClimavenetaSensorEntityDescription(
        name="Max Summer Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        key=CLIMAVENETA_MAX_WATER_TEMP_SUMMER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Min Winter Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MIN_WATER_TEMP_WINTER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Setpoint Hysteresis",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_SETPOINT_HYSTERESIS,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Dead Zone Center",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_DEAD_ZONE_CENTER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Dead Zone Range",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_DEAD_ZONE_RANGE,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="T1 Compensation Delta",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_T1_COMPENSATION_DELTA,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="NTC ETN Offset",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_OFFSET_NTC_ETN,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="T2 Probe Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_T2_TEMPERATURE,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Analog Output",
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_ANALOG_OUTPUT,
        entity_registry_visible_default=False,
    ),
)


ILIFE2_SENSOR_TYPES: tuple[ClimavenetaSensorEntityDescription, ...] = (
    ClimavenetaSensorEntityDescription(
        name="Actual Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_ACTUAL_TEMPERATURE,
    ),
    ClimavenetaSensorEntityDescription(
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_EXCHANGER_TEMPERATURE,
    ),
    ClimavenetaSensorEntityDescription(
        name="Real Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_REAL_SETPOINT,
    ),
    ClimavenetaSensorEntityDescription(
        name="Motor Speed Set",
        state_class=SensorStateClass.MEASUREMENT,
        key=CLIMAVENETA_MOTOR_SPEED_SET,
    ),
    ClimavenetaSensorEntityDescription(
        name="Max Summer Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        key=CLIMAVENETA_MAX_WATER_TEMP_SUMMER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Min Winter Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        key=CLIMAVENETA_MIN_WATER_TEMP_WINTER,
        entity_registry_visible_default=False,
    ),
    ClimavenetaSensorEntityDescription(
        name="Modbus Address",
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_MODBUS_ADDRESS,
        entity_registry_visible_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator: ClimavenetaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list = []

    # Add the sensors specific for the unit type
    if coordinator.device_type == CLIMAVENETA_IMXW:
        entities.extend(
            ClimavenetaSensor(coordinator, description)
            for description in IMXW_SENSOR_TYPES
        )
    elif coordinator.device_type == CLIMAVENETA_ILIFE2:
        entities.extend(
            ClimavenetaSensor(coordinator, description)
            for description in ILIFE2_SENSOR_TYPES
        )

    # Add HVAC status sensor for all device types
    entities.append(ClimavenetaHvacStatusSensor(coordinator))

    async_add_entities(entities)


class ClimavenetaSensor(CoordinatorEntity[ClimavenetaCoordinator], SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True
    entity_description: ClimavenetaSensorEntityDescription

    def __init__(
        self,
        coordinator: ClimavenetaCoordinator,
        description: ClimavenetaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_device_info = coordinator.device_info
        self.entity_description = description
        self._state = 0.0
        self._attr_unique_id = (
            f"{coordinator.hub!s}_{description.key!s}_{coordinator.slave_id!s}"
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        try:
            self._state = self.coordinator.data_readbacks[self.entity_description.key]
        except KeyError:
            self._state = 0

        return self._state

    async def async_update(self) -> None:
        """Retrieve latest state."""
        try:
            self._state = self.coordinator.data_readbacks[self.entity_description.key]
        except KeyError:
            self._state = 0


    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state from the coordinator."""
        try:
            self._attr_native_value = self.coordinator.data_readbacks[self.entity_description.key]
        except KeyError:
            self._attr_native_value = None

        # notify Home Assistant of the status change
        self.async_write_ha_state()


class ClimavenetaHvacStatusSensor(CoordinatorEntity[ClimavenetaCoordinator], SensorEntity):
    """Sensor showing current HVAC action as text (off, idle, fan, cooling, heating)."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = HVAC_STATUS_OPTIONS

    def __init__(
        self,
        coordinator: ClimavenetaCoordinator,
    ) -> None:
        """Initialize the HVAC status sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = "HVAC Status"
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = (
            f"{coordinator.hub!s}_{CLIMAVENETA_HVAC_STATUS}_{coordinator.slave_id!s}"
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor as a string."""
        try:
            action_int = self.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS]
            return HVAC_ACTION_TO_STRING.get(action_int, "off")
        except KeyError:
            return "off"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state from the coordinator."""
        try:
            action_int = self.coordinator.data_readbacks[CLIMAVENETA_HVAC_STATUS]
            self._attr_native_value = HVAC_ACTION_TO_STRING.get(action_int, "off")
        except KeyError:
            self._attr_native_value = "off"

        self.async_write_ha_state()
