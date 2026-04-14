"""Platform for the climaveneta iMXW and iLife2 AC."""

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, CONF_SLAVE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import CONF_HUB, DEFAULT_MODBUS_HUB, DEVICE_TYPE, DOMAIN
from .coordinator import ClimavenetaCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]


_LOGGER = logging.getLogger(__name__)


SET_TEMPERATURE_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(ATTR_TEMPERATURE, "temperature"): vol.Coerce(float),
        }
    )
)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entries to new schema."""
    _LOGGER.info(
        "Migrating entry '%s' from version %s",
        config_entry.title,
        config_entry.version,
    )

    if config_entry.version < 3:
        new_data = dict(config_entry.data)
        current_hub = new_data.get(CONF_HUB, "")
        slave_id = new_data.get(CONF_SLAVE, 0)

        # If hub is still a legacy name (v1), update config data
        if current_hub and not current_hub.startswith("/dev/"):
            new_data[CONF_HUB] = DEFAULT_MODBUS_HUB
            current_hub = DEFAULT_MODBUS_HUB

        # Parse old hub from title (format: "Climaveneta {type} {name} at {hub}:{slave}")
        old_hub = None
        title_parts = config_entry.title.split(" at ")
        if len(title_parts) >= 2:
            old_hub = title_parts[-1].rsplit(":", 1)[0]

        if old_hub and old_hub != current_hub:
            ent_reg = er.async_get(hass)
            dev_reg = dr.async_get(hass)

            # 1) Remove duplicate entities created by the buggy v1→v2 migration
            #    (those with new hub prefix — they have no area/customizations)
            for entity_entry in list(
                er.async_entries_for_config_entry(ent_reg, config_entry.entry_id)
            ):
                if entity_entry.unique_id.startswith(f"{current_hub}_"):
                    _LOGGER.info(
                        "Removing duplicate entity %s (unique_id: %s)",
                        entity_entry.entity_id,
                        entity_entry.unique_id,
                    )
                    ent_reg.async_remove(entity_entry.entity_id)

            # 2) Migrate original entities' unique_ids to use new hub
            for entity_entry in list(
                er.async_entries_for_config_entry(ent_reg, config_entry.entry_id)
            ):
                old_uid = entity_entry.unique_id
                if old_uid.startswith(f"{old_hub}_"):
                    new_uid = f"{current_hub}_{old_uid[len(old_hub) + 1:]}"
                    _LOGGER.info(
                        "Migrating entity %s unique_id: '%s' -> '%s'",
                        entity_entry.entity_id,
                        old_uid,
                        new_uid,
                    )
                    ent_reg.async_update_entity(
                        entity_entry.entity_id, new_unique_id=new_uid
                    )

            # 3) Handle device registry: remove duplicate, update original
            old_device = dev_reg.async_get_device(
                identifiers={(DOMAIN, f"{old_hub}_{slave_id}")}
            )
            new_device = dev_reg.async_get_device(
                identifiers={(DOMAIN, f"{current_hub}_{slave_id}")}
            )
            if new_device and old_device and new_device.id != old_device.id:
                _LOGGER.info(
                    "Removing duplicate device '%s'", new_device.name
                )
                dev_reg.async_remove_device(new_device.id)
            if old_device:
                _LOGGER.info(
                    "Migrating device '%s' identifier: '%s_%s' -> '%s_%s'",
                    old_device.name,
                    old_hub, slave_id,
                    current_hub, slave_id,
                )
                dev_reg.async_update_device(
                    old_device.id,
                    new_identifiers={(DOMAIN, f"{current_hub}_{slave_id}")},
                )

            _LOGGER.info(
                "Migrated entry '%s': hub '%s' -> '%s'",
                config_entry.title,
                old_hub,
                current_hub,
            )

        # Update title to reflect new hub
        new_title = config_entry.title
        if old_hub and old_hub != current_hub:
            new_title = new_title.replace(
                f"at {old_hub}:", f"at {current_hub}:"
            )

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, title=new_title, version=3
        )

    _LOGGER.info(
        "Migration of entry '%s' to version %s successful",
        config_entry.title,
        config_entry.version,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""

    device_type = entry.data[DEVICE_TYPE]
    hub = entry.data[CONF_HUB]
    slave_id = entry.data[CONF_SLAVE]
    name = entry.data[CONF_NAME]

    coordinator = ClimavenetaCoordinator(hass, device_type, hub, slave_id, name)
    await coordinator.async_create()

    await coordinator.api.try_initial_communication()

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Climaveneta config entry."""

    # our components don't have unload methods so no need to look at return values
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)

    return True
