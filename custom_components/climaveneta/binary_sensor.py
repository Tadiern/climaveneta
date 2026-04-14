"""Support for the Mitsubishi-Climaveneta iMXW and iLife2 fancoil series."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ClimavenetaCoordinator
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
    CLIMAVENETA_ALARM_T1,
    CLIMAVENETA_ALARM_T2,
    CLIMAVENETA_ALARM_T3,
    CLIMAVENETA_ALARM_WATER_DRAIN,
    CLIMAVENETA_CONTINUOUS_VENTILATION,
    CLIMAVENETA_HEATER_PRESENT,
    CLIMAVENETA_MACHINE_SLAVE,
    CLIMAVENETA_PUMP_ALARM_INPUT,
    CLIMAVENETA_PUMP_RELAY,
    CLIMAVENETA_RELAY5_FAN_HIGH,
    CLIMAVENETA_WINDOW_INPUT,
    CLIMAVENETA_ILIFE2,
    CLIMAVENETA_IMXW,
    DOMAIN,
)


class ClimavenetaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing Climaveneta binary sensor entities."""

    attrs: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


IMXW_BINARY_SENSOR_TYPES: tuple[ClimavenetaBinarySensorEntityDescription, ...] = (
    ClimavenetaBinarySensorEntityDescription(
        name="Pump Relay",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_PUMP_RELAY,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Continuous Ventilation",
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_CONTINUOUS_VENTILATION,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Machine Slave",
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_MACHINE_SLAVE,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Relay 5 FAN HIGH",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_RELAY5_FAN_HIGH,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Window Input",
        device_class=BinarySensorDeviceClass.WINDOW,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_WINDOW_INPUT,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Pump Alarm Input",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_PUMP_ALARM_INPUT,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Heater Present",
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_HEATER_PRESENT,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: T1 Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_T1,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: T2 Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_T2,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: T3 Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_T3,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: Water Drain",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_WATER_DRAIN,
        entity_registry_visible_default=False,
    ),
)

ILIFE2_BINARY_SENSOR_TYPES: tuple[ClimavenetaBinarySensorEntityDescription, ...] = (
    ClimavenetaBinarySensorEntityDescription(
        name="Pump Relay",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_PUMP_RELAY,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: Communication",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_COM,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: AIR Probe",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_AIR,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: H4 Probe",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_H4,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: Water Temperature",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_ACQ_DAN,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: H2 Probe",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_H2,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: H4 Wrong Temperature",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_H4_NID,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: High Resistance",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_HI_RES,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: Motor Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_MOT,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: GRID Contact Open",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_GRID,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: H2 Wrong Temperature",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_H2_NID,
        entity_registry_visible_default=False,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: Filter Maintenance",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_FILTRO,
    ),
    ClimavenetaBinarySensorEntityDescription(
        name="Alarm: 2 AIR M5",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        key=CLIMAVENETA_ALARM_2AIR_M5,
        entity_registry_visible_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a config entry."""
    coordinator: ClimavenetaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list = []

    # Add the binary sensors specific for the unit type
    if coordinator.device_type == CLIMAVENETA_IMXW:
        entities.extend(
            ClimavenetaBinarySensor(coordinator, description)
            for description in IMXW_BINARY_SENSOR_TYPES
        )
    elif coordinator.device_type == CLIMAVENETA_ILIFE2:
        entities.extend(
            ClimavenetaBinarySensor(coordinator, description)
            for description in ILIFE2_BINARY_SENSOR_TYPES
        )

    async_add_entities(entities)


class ClimavenetaBinarySensor(
    CoordinatorEntity[ClimavenetaCoordinator], BinarySensorEntity
):
    """Representation of a Binary Sensor."""

    _attr_has_entity_name = True
    entity_description: ClimavenetaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ClimavenetaCoordinator,
        description: ClimavenetaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_device_info = coordinator.device_info
        self.entity_description = description
        self._attr_is_on = False
        self._attr_unique_id = (
            f"{coordinator.hub!s}_{description.key!s}_{coordinator.slave_id!s}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        try:
            state = self.coordinator.data_readbacks[self.entity_description.key]
            self._attr_is_on = bool(state)
        except KeyError:
            self._attr_is_on = False

        return self._attr_is_on

    async def async_update(self) -> None:
        """Retrieve latest state."""
        try:
            state = self.coordinator.data_readbacks[self.entity_description.key]
            self._attr_is_on = bool(state)
        except KeyError:
            self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update binary sensor state from the coordinator."""
        try:
            state = self.coordinator.data_readbacks[self.entity_description.key]
            self._attr_is_on = bool(state)
        except KeyError:
            self._attr_is_on = False

        # Notify Home Assistant, status change
        self.async_write_ha_state()


