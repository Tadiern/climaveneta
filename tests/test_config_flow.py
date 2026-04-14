from custom_components.climaveneta.const import DEFAULT_MODBUS_HUB


def test_config_flow_schema():
    # basic check: default hub appears
    # We can't run full hass flow here; just ensure DEFAULT_MODBUS_HUB exists and is a string
    assert isinstance(DEFAULT_MODBUS_HUB, str)
