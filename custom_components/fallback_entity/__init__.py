from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ENTITY_TYPE, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entity_type = entry.data[CONF_ENTITY_TYPE]
    await hass.config_entries.async_forward_entry_setups(entry, [entity_type])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entity_type = entry.data[CONF_ENTITY_TYPE]
    return await hass.config_entries.async_unload_platforms(entry, [entity_type])
