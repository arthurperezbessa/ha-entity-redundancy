from __future__ import annotations

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_FALLBACK, CONF_PRIMARY, UNAVAILABLE_STATES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([FallbackLight(entry)])


class FallbackLight(LightEntity):
    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._primary: str = entry.data[CONF_PRIMARY]
        self._fallback: str = entry.data[CONF_FALLBACK]
        self._attr_name: str = entry.data["name"]
        self._attr_unique_id: str = entry.entry_id

    @property
    def _active_entity(self) -> str:
        state = self.hass.states.get(self._primary)
        if state and state.state not in UNAVAILABLE_STATES:
            return self._primary
        return self._fallback

    @property
    def _active_state(self):
        return self.hass.states.get(self._active_entity)

    @property
    def is_on(self) -> bool | None:
        state = self._active_state
        if state and state.state not in UNAVAILABLE_STATES:
            return state.state == STATE_ON
        return None

    @property
    def brightness(self) -> int | None:
        state = self._active_state
        if state:
            return state.attributes.get(ATTR_BRIGHTNESS)
        return None

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        state = self._active_state
        if state:
            modes = state.attributes.get("supported_color_modes")
            if modes:
                return set(modes)
        return {ColorMode.ONOFF}

    @property
    def color_mode(self) -> ColorMode | None:
        state = self._active_state
        if state:
            return state.attributes.get("color_mode", ColorMode.ONOFF)
        return ColorMode.ONOFF

    @property
    def available(self) -> bool:
        primary_state = self.hass.states.get(self._primary)
        fallback_state = self.hass.states.get(self._fallback)
        primary_ok = primary_state and primary_state.state not in UNAVAILABLE_STATES
        fallback_ok = fallback_state and fallback_state.state not in UNAVAILABLE_STATES
        return bool(primary_ok or fallback_ok)

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "active_entity": self._active_entity,
            "primary_entity": self._primary,
            "fallback_entity": self._fallback,
        }

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "light", "turn_on", {"entity_id": self._active_entity, **kwargs}
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "light", "turn_off", {"entity_id": self._active_entity}
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._primary, self._fallback],
                self._handle_state_change,
            )
        )

    @callback
    def _handle_state_change(self, event) -> None:
        self.async_write_ha_state()
