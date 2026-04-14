"""Number entities for configuring Climaveneta iMXW machine parameters."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ClimavenetaCoordinator
from .const import (
    CLIMAVENETA_ANTISTRAT_TIME_SUMMER,
    CLIMAVENETA_ANTISTRAT_TIME_WINTER,
    CLIMAVENETA_ANTISTRAT_WAIT_TIME,
    CLIMAVENETA_IMXW,
    CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER,
    CLIMAVENETA_T1_COMPENSATION_BASE_WINTER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


IMXW_NUMBER_TYPES: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        name="Anti-stratification Wait Time",
        key=CLIMAVENETA_ANTISTRAT_WAIT_TIME,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=10,
        native_max_value=20,
        native_step=1,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        name="T1 Compensation Base Summer",
        key=CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0.5,
        native_max_value=2.0,
        native_step=0.1,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        name="Anti-stratification Time Summer",
        key=CLIMAVENETA_ANTISTRAT_TIME_SUMMER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=30,
        native_max_value=180,
        native_step=1,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        name="T1 Compensation Base Winter",
        key=CLIMAVENETA_T1_COMPENSATION_BASE_WINTER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0.5,
        native_max_value=5.0,
        native_step=0.1,
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        name="Anti-stratification Time Winter",
        key=CLIMAVENETA_ANTISTRAT_TIME_WINTER,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=30,
        native_max_value=180,
        native_step=1,
        mode=NumberMode.BOX,
    ),
)

# Map keys to API setter method names
_SETTER_MAP = {
    CLIMAVENETA_ANTISTRAT_WAIT_TIME: "set_antistrat_wait_time",
    CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER: "set_t1_compensation_base_summer",
    CLIMAVENETA_ANTISTRAT_TIME_SUMMER: "set_antistrat_time_summer",
    CLIMAVENETA_T1_COMPENSATION_BASE_WINTER: "set_t1_compensation_base_winter",
    CLIMAVENETA_ANTISTRAT_TIME_WINTER: "set_antistrat_time_winter",
}

# Map keys to API getter method names
_GETTER_MAP = {
    CLIMAVENETA_ANTISTRAT_WAIT_TIME: "get_antistrat_wait_time",
    CLIMAVENETA_T1_COMPENSATION_BASE_SUMMER: "get_t1_compensation_base_summer",
    CLIMAVENETA_ANTISTRAT_TIME_SUMMER: "get_antistrat_time_summer",
    CLIMAVENETA_T1_COMPENSATION_BASE_WINTER: "get_t1_compensation_base_winter",
    CLIMAVENETA_ANTISTRAT_TIME_WINTER: "get_antistrat_time_winter",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up number entities from a config entry."""
    coordinator: ClimavenetaCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.device_type != CLIMAVENETA_IMXW:
        return

    entities = [
        ClimavenetaNumber(coordinator, description)
        for description in IMXW_NUMBER_TYPES
    ]
    async_add_entities(entities)


class ClimavenetaNumber(CoordinatorEntity[ClimavenetaCoordinator], NumberEntity):
    """Number entity for a writable Climaveneta iMXW configuration parameter."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ClimavenetaCoordinator,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = (
            f"{coordinator.hub!s}_{description.key!s}_{coordinator.slave_id!s}"
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return self.coordinator.data_readbacks[self.entity_description.key]
        except KeyError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the configuration parameter on the device."""
        setter_name = _SETTER_MAP.get(self.entity_description.key)
        if setter_name is None:
            return
        setter = getattr(self.coordinator.api, setter_name)
        result = await setter(value)
        if result:
            # Update the coordinator readback with the fresh value from getter
            getter_name = _GETTER_MAP.get(self.entity_description.key)
            if getter_name:
                getter = getattr(self.coordinator.api, getter_name)
                self.coordinator.data_readbacks[self.entity_description.key] = getter()
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state from the coordinator."""
        self.async_write_ha_state()
