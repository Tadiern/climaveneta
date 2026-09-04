"""Tests for Climaveneta integration setup."""

import importlib
from unittest.mock import AsyncMock, MagicMock

import pytest
from modbus_connection import ModbusSerialParams

from custom_components.climaveneta import async_migrate_entry, async_setup_entry
from custom_components.climaveneta.const import (
    CLIMAVENETA_IMXW,
    CONF_HUB,
    DEFAULT_MODBUS_HUB,
    DEVICE_TYPE,
)


@pytest.mark.asyncio
async def test_setup_uses_home_assistant_shared_modbus_unit(mocker) -> None:
    """The integration must not construct or own a Modbus connection."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry-id"
    entry.data = {
        DEVICE_TYPE: CLIMAVENETA_IMXW,
        CONF_HUB: "/dev/ttyUSB0",
        "slave": 1,
        "name": "Living room",
    }

    unit = MagicMock()
    modbus = importlib.import_module("homeassistant.components.modbus")
    get_unit = mocker.patch.object(
        modbus,
        "async_get_unit",
        return_value=unit,
        create=True,
    )
    coordinator = MagicMock()
    coordinator.async_create = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    mocker.patch(
        "custom_components.climaveneta.ClimavenetaCoordinator",
        return_value=coordinator,
    )

    assert await async_setup_entry(hass, entry) is True

    get_unit.assert_called_once_with(
        hass,
        entry,
        ModbusSerialParams(
            device="/dev/ttyUSB0",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            framer="rtu",
        ),
        1,
    )
    coordinator.async_create.assert_awaited_once_with(unit)


@pytest.mark.asyncio
async def test_migrate_v3_entry_preserves_existing_connection_data() -> None:
    """v4 must retain the identifiers of existing installations."""
    hass = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    entry = MagicMock()
    entry.version = 3
    entry.title = "Climaveneta imxw Living room at /dev/ttyUSB0:1"
    entry.data = {
        DEVICE_TYPE: CLIMAVENETA_IMXW,
        CONF_HUB: "/dev/ttyUSB0",
        "slave": 1,
        "name": "Living room",
    }

    assert await async_migrate_entry(hass, entry) is True

    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data=entry.data,
        title=entry.title,
        version=4,
    )


@pytest.mark.asyncio
async def test_migrate_legacy_entry_to_shared_connection_format(mocker) -> None:
    """Migrate a legacy named hub to a serial device path."""
    hass = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    entry = MagicMock()
    entry.entry_id = "entry-id"
    entry.version = 2
    entry.title = "Climaveneta imxw Living room at old_hub:1"
    entry.data = {
        DEVICE_TYPE: CLIMAVENETA_IMXW,
        CONF_HUB: "old_hub",
        "slave": 1,
        "name": "Living room",
    }

    entity_registry = MagicMock()
    device_registry = MagicMock()
    mocker.patch(
        "custom_components.climaveneta.er.async_get",
        return_value=entity_registry,
    )
    mocker.patch(
        "custom_components.climaveneta.er.async_entries_for_config_entry",
        return_value=[],
    )
    mocker.patch(
        "custom_components.climaveneta.dr.async_get",
        return_value=device_registry,
    )
    device_registry.async_get_device.return_value = None

    assert await async_migrate_entry(hass, entry) is True

    hass.config_entries.async_update_entry.assert_called_once_with(
        entry,
        data={
            DEVICE_TYPE: CLIMAVENETA_IMXW,
            CONF_HUB: DEFAULT_MODBUS_HUB,
            "slave": 1,
            "name": "Living room",
        },
        title=(
            "Climaveneta imxw Living room "
            f"at {DEFAULT_MODBUS_HUB}:1"
        ),
        version=4,
    )


@pytest.mark.asyncio
async def test_migrate_legacy_entry_keeps_entity_and_device_registry_records(
    mocker,
) -> None:
    """Legacy identifiers are rewritten instead of creating duplicate devices."""
    hass = MagicMock()
    hass.config_entries.async_update_entry = MagicMock()
    entry = MagicMock(entry_id="entry-id")
    entry.version = 2
    entry.title = "Climaveneta imxw Living room at old_hub:1"
    entry.data = {
        DEVICE_TYPE: CLIMAVENETA_IMXW,
        CONF_HUB: "old_hub",
        "slave": 1,
        "name": "Living room",
    }
    entity = MagicMock(entity_id="climate.living_room", unique_id="old_hub_main_1")
    old_device = MagicMock(id="old-device", name="Living room")
    entity_registry = MagicMock()
    device_registry = MagicMock()

    mocker.patch(
        "custom_components.climaveneta.er.async_get",
        return_value=entity_registry,
    )
    mocker.patch(
        "custom_components.climaveneta.er.async_entries_for_config_entry",
        return_value=[entity],
    )
    mocker.patch(
        "custom_components.climaveneta.dr.async_get",
        return_value=device_registry,
    )
    device_registry.async_get_device.side_effect = [old_device, None]

    assert await async_migrate_entry(hass, entry) is True

    entity_registry.async_update_entity.assert_called_once_with(
        "climate.living_room",
        new_unique_id=f"{DEFAULT_MODBUS_HUB}_main_1",
    )
    device_registry.async_update_device.assert_called_once_with(
        "old-device",
        new_identifiers={(
            "climaveneta",
            f"{DEFAULT_MODBUS_HUB}_1",
        )},
    )
