"""Support for the Mitsubishi-Climaveneta iMXW and iLife2 fancoil series."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_NONE,
    SWING_OFF,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ClimavenetaCoordinator
from .const import CLIMAVENETA_IMXW, DOMAIN
from .pyclimaveneta import (
    CV_ACTION_COOLING,
    CV_ACTION_FAN,
    CV_ACTION_HEATING,
    CV_ACTION_IDLE,
    CV_ACTION_OFF,
    CV_FAN_AUTO,
    CV_FAN_HIGH,
    CV_FAN_LOW,
    CV_FAN_MEDIUM,
    CV_MODE_COOL,
    CV_MODE_FAN_ONLY,
    CV_MODE_HEAT,
    CV_MODE_HEAT_COOL,
    CV_MODE_OFF,
    CV_PRESET_MODE_AWAY,
    CV_PRESET_MODE_ECO,
    CV_PRESET_MODE_NONE,
)

_LOGGER = logging.getLogger(__name__)

CLIMAVENETA_SET_ACTUAL_TEMPERATURE = "set_actual_temperature"
CLIMAVENETA_SET_ACTUAL_TEMPERATURE_VALUE = "temperature"


hvac_modes = {
    CV_MODE_OFF: HVACMode.OFF,
    CV_MODE_FAN_ONLY: HVACMode.FAN_ONLY,
    CV_MODE_COOL: HVACMode.COOL,
    CV_MODE_HEAT: HVACMode.HEAT,
    CV_MODE_HEAT_COOL: HVACMode.HEAT_COOL,
}

hvac_actions = {
    CV_ACTION_OFF: HVACAction.OFF,
    CV_ACTION_IDLE: HVACAction.IDLE,
    CV_ACTION_FAN: HVACAction.FAN,
    CV_ACTION_COOLING: HVACAction.COOLING,
    CV_ACTION_HEATING: HVACAction.HEATING,
}

hvac_fan_mode = {
    CV_FAN_AUTO: FAN_AUTO,
    CV_FAN_LOW: FAN_LOW,
    CV_FAN_MEDIUM: FAN_MEDIUM,
    CV_FAN_HIGH: FAN_HIGH,
}

imxw_preset_modes = {
    CV_PRESET_MODE_NONE: PRESET_NONE,
    CV_PRESET_MODE_ECO: PRESET_ECO,
    CV_PRESET_MODE_AWAY: PRESET_AWAY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a config entry."""
    coordinator: ClimavenetaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ClimateEntity] = []

    entities.append(
        ClimavenetaClimate(
            coordinator,
            coordinator.device_type,
            coordinator.hub,
            coordinator.slave_id,
            coordinator.name,
        )
    )

    if coordinator.device_type == CLIMAVENETA_IMXW:
        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service(
            CLIMAVENETA_SET_ACTUAL_TEMPERATURE,
            {vol.Required("temperature"): cv.positive_float},
            "set_actual_temperature",
        )

    async_add_entities(entities)


class ClimavenetaClimate(CoordinatorEntity[ClimavenetaCoordinator], ClimateEntity):
    """Representation of a Climaveneta fancoil unit."""

    _attr_has_entity_name = True
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_fan_mode = FAN_AUTO
    _attr_target_temperature_step = 0.1

    _attr_hvac_mode = HVACMode.OFF

    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    _filter_alarm: int | None = None
    _heat_recovery: int | None = None
    _heater_enabled: int | None = None
    _heating: int | None = None
    _cooling: int | None = None
    _alarm = False
    _summer_winter: int = 0
    _target_temperature_winter: int | None = None
    _attr_winter_temperature: float = 0.0
    _attr_summer_temperature: float = 0.0
    _exchanger_temperature: float = 0.0
    _t1_alarm: int = 0
    _t3_alarm: int = 0
    _water_drain: int = 0
    _min_temp: int = 15
    _max_temp: int = 30
    _attr_on_off: int = 0
    _attr_fan_only: int = 0
    _attr_ev_water: int = 0
    _attr_target_temperature: float = 0
    _attr_current_temperature: float = 0
    _attr_hvac_action: HVACAction = HVACAction.OFF

    def __init__(
        self,
        coordinator,
        device_type: str,
        hub: str,
        modbus_slave: int | None,
        name: str | None,
    ) -> None:
        """Initialize the unit."""
        super().__init__(coordinator)
        self._type = device_type
        self._hub = hub
        self._attr_name = None
        self._slave = modbus_slave
        self._attr_icon = "mdi:hvac-off"
        self._attr_unique_id = f"{hub!s}_{name}_{modbus_slave!s}"

        self._attr_device_info = coordinator.device_info

        if self._type == CLIMAVENETA_IMXW:
            self._attr_hvac_modes = [
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.FAN_ONLY,
                HVACMode.OFF,
            ]
            self._attr_swing_modes = [SWING_OFF]
            self._attr_swing_mode = SWING_OFF
            self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.PRESET_MODE
            )
            self._attr_preset_modes = [PRESET_NONE, PRESET_ECO, PRESET_AWAY]
            self._attr_preset_mode = PRESET_NONE
        else:
            self._attr_hvac_modes = [
                HVACMode.HEAT,
                HVACMode.COOL,
                HVACMode.OFF,
            ]
            self._attr_preset_modes = [PRESET_NONE]
            self._attr_preset_mode = PRESET_NONE
            self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        _LOGGER.debug(
            "Calling _handle_coordinator_update id %d slave %d",
            id(self.coordinator),
            self._slave,
        )

        try:
            self._attr_target_temperature = self.coordinator.api.get_target_temp()

            self._attr_current_temperature = self.coordinator.api.get_current_temp()

            _LOGGER.debug(
                "Current_temperature valid for id %d slave %d, value %f",
                id(self.coordinator),
                self._slave,
                self._attr_current_temperature,
            )
            self._attr_on_off = self.coordinator.api.get_on_off()
            self._attr_fan_only = self.coordinator.api.get_fan_only()
            self._attr_hvac_action = hvac_actions[
                self.coordinator.api.get_hvac_action()
            ]
            self._attr_hvac_mode = hvac_modes[self.coordinator.api.get_hvac_mode()]
            self._attr_fan_mode = hvac_fan_mode[self.coordinator.api.get_fan_mode()]
            self._attr_preset_mode = imxw_preset_modes[
                self.coordinator.api.get_preset_mode()
            ]

        except KeyError:
            self._attr_target_temperature = 0
            self._attr_current_temperature = 0
            self._attr_hvac_action = HVACAction.OFF
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_fan_mode = FAN_AUTO

            if self._attr_hvac_mode == HVACMode.OFF:
                self._attr_icon = "mdi:hvac-off"
            else:
                self._attr_icon = "mdi:hvac"

            _LOGGER.debug(
                "Current_temperature not valid for id %d slave %d",
                id(self.coordinator),
                self._slave,
            )

        self.async_write_ha_state()

    async def set_actual_temperature(self, **kwargs: Any) -> None:
        """Set the actual true temperature value."""
        value = float(kwargs[CLIMAVENETA_SET_ACTUAL_TEMPERATURE_VALUE])
        _LOGGER.info(
            "Setting actual external temperature value %f",
            value,
        )
        # update the temperature in the API
        await self.coordinator.api.set_actual_true_temperature(value)
        self._handle_coordinator_update()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (target_temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            _LOGGER.error("Received invalid temperature")
            return

        await self.coordinator.api.set_target_temp(target_temperature)
        self._handle_coordinator_update()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""

        await self.coordinator.api.turn_on()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if fan_mode in (FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH):
            for key, value in hvac_fan_mode.items():
                if fan_mode == value:
                    clivaveneta_fan_mode = key
                    await self.coordinator.api.set_fan_speed(clivaveneta_fan_mode)
                    self._handle_coordinator_update()
                    return

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        if hvac_mode in (
            HVACMode.OFF,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ):
            for key, value in hvac_modes.items():
                if hvac_mode == value:
                    clivaveneta_hvac_mode = key
                    await self.coordinator.api.set_hvac_mode(clivaveneta_hvac_mode)
                    self._handle_coordinator_update()
                    return

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self._type == CLIMAVENETA_IMXW:
            # only if imxw for now
            if preset_mode in (
                PRESET_NONE,
                PRESET_ECO,
                PRESET_AWAY,
            ):
                for key, value in imxw_preset_modes.items():
                    if preset_mode == value:
                        clivaveneta_preset_mode = key
                        await self.coordinator.api.set_preset_mode(
                            clivaveneta_preset_mode
                        )
                        self._handle_coordinator_update()
                        return
