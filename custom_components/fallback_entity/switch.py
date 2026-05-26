from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ENTITY_TYPE,
    CONF_FALLBACK,
    CONF_PAIR_ID,
    CONF_PAIRS,
    CONF_PRIMARY,
    UNAVAILABLE_STATES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    pairs = entry.options.get(CONF_PAIRS, [])
    async_add_entities(
        [
            FallbackSwitch(entry.entry_id, pair)
            for pair in pairs
            if pair[CONF_ENTITY_TYPE] == "switch"
        ]
    )


class FallbackSwitch(SwitchEntity):
    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, entry_id: str, pair: dict) -> None:
        self._primary: str = pair[CONF_PRIMARY]
        self._fallback: str = pair[CONF_FALLBACK]
        self._attr_name: str = pair["name"]
        self._attr_unique_id: str = f"{entry_id}_{pair[CONF_PAIR_ID]}"

    @property
    def _active_entity(self) -> str:
        state = self.hass.states.get(self._primary)
        if state and state.state not in UNAVAILABLE_STATES:
            return self._primary
        return self._fallback

    @property
    def is_on(self) -> bool | None:
        state = self.hass.states.get(self._active_entity)
        if state and state.state not in UNAVAILABLE_STATES:
            return state.state == STATE_ON
        return None

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
            "switch", "turn_on", {"entity_id": self._active_entity}
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self._active_entity}
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
