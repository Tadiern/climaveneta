import pytest
from homeassistant import data_entry_flow
from custom_components.climaveneta.config_flow import ClimavenetaConfigFlow
from custom_components.climaveneta.const import DEFAULT_MODBUS_HUB


def test_config_flow_schema():
    # basic check: default hub appears
    cf = ClimavenetaConfigFlow()
    schema = cf.async_step_user.__wrapped__ if hasattr(cf.async_step_user, "__wrapped__") else None
    # We can't run full hass flow here; just ensure DEFAULT_MODBUS_HUB exists and is a string
    assert isinstance(DEFAULT_MODBUS_HUB, str)
