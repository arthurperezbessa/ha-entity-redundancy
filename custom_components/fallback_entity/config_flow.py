from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_ENTITY_TYPE, CONF_FALLBACK, CONF_PRIMARY, DOMAIN


class FallbackEntityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._entity_type: str | None = None

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            self._entity_type = user_input[CONF_ENTITY_TYPE]
            return await self.async_step_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENTITY_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["switch", "light"],
                            translation_key="entity_type",
                        )
                    ),
                }
            ),
        )

    async def async_step_entities(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            primary = user_input[CONF_PRIMARY]
            fallback = user_input[CONF_FALLBACK]
            if primary == fallback:
                errors["base"] = "same_entity"
            else:
                return self.async_create_entry(
                    title=user_input["name"],
                    data={
                        CONF_ENTITY_TYPE: self._entity_type,
                        CONF_PRIMARY: primary,
                        CONF_FALLBACK: fallback,
                        "name": user_input["name"],
                    },
                )

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): selector.TextSelector(),
                    vol.Required(CONF_PRIMARY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=self._entity_type)
                    ),
                    vol.Required(CONF_FALLBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=self._entity_type)
                    ),
                }
            ),
            errors=errors,
        )
