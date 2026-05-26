from __future__ import annotations

import json
import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ENTITY_TYPE,
    CONF_FALLBACK,
    CONF_PAIR_ID,
    CONF_PAIRS,
    CONF_PRIMARY,
    DOMAIN,
)

_ENTITY_DOMAINS = ["switch", "light"]

_PAIR_FORM_SCHEMA = vol.Schema(
    {
        vol.Required("name"): selector.TextSelector(),
        vol.Required(CONF_ENTITY_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(options=_ENTITY_DOMAINS)
        ),
        vol.Required(CONF_PRIMARY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=_ENTITY_DOMAINS)
        ),
        vol.Required(CONF_FALLBACK): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=_ENTITY_DOMAINS)
        ),
    }
)


def _build_pair(user_input: dict, pair_id: str | None = None) -> dict:
    return {
        CONF_PAIR_ID: pair_id or str(uuid.uuid4()),
        "name": user_input["name"],
        CONF_ENTITY_TYPE: user_input[CONF_ENTITY_TYPE],
        CONF_PRIMARY: user_input[CONF_PRIMARY],
        CONF_FALLBACK: user_input[CONF_FALLBACK],
    }


class FallbackEntityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow: creates the entry and adds the first pair."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_PRIMARY] == user_input[CONF_FALLBACK]:
                errors["base"] = "same_entity"
            else:
                return self.async_create_entry(
                    title="Fallback Entity",
                    data={},
                    options={CONF_PAIRS: [_build_pair(user_input)]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_PAIR_FORM_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FallbackEntityOptionsFlow:
        return FallbackEntityOptionsFlow()


class FallbackEntityOptionsFlow(config_entries.OptionsFlow):
    """Options flow: add / edit / remove / import-JSON entity pairs."""

    def __init__(self) -> None:
        self._edit_pair_id: str | None = None

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        pairs = self.config_entry.options.get(CONF_PAIRS, [])
        menu_options = (
            ["add_entity", "edit_entity", "remove_entity", "import_json"]
            if pairs
            else ["add_entity", "import_json"]
        )
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    # ------------------------------------------------------------------ ADD --

    async def async_step_add_entity(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_PRIMARY] == user_input[CONF_FALLBACK]:
                errors["base"] = "same_entity"
            else:
                pairs = [
                    *self.config_entry.options.get(CONF_PAIRS, []),
                    _build_pair(user_input),
                ]
                return self.async_create_entry(
                    data={**self.config_entry.options, CONF_PAIRS: pairs}
                )

        return self.async_show_form(
            step_id="add_entity",
            data_schema=_PAIR_FORM_SCHEMA,
            errors=errors,
        )

    # ----------------------------------------------------------------- EDIT --

    async def async_step_edit_entity(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Step 1 of edit: choose which pair to edit."""
        pairs = self.config_entry.options.get(CONF_PAIRS, [])

        if user_input is not None:
            self._edit_pair_id = user_input[CONF_PAIR_ID]
            return await self.async_step_edit_entity_form()

        return self.async_show_form(
            step_id="edit_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PAIR_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": p[CONF_PAIR_ID], "label": p["name"]}
                                for p in pairs
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_edit_entity_form(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Step 2 of edit: change the pair's fields (pre-filled)."""
        pairs = self.config_entry.options.get(CONF_PAIRS, [])
        current = next(p for p in pairs if p[CONF_PAIR_ID] == self._edit_pair_id)
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[CONF_PRIMARY] == user_input[CONF_FALLBACK]:
                errors["base"] = "same_entity"
            else:
                new_pairs = [
                    _build_pair(user_input, pair_id=self._edit_pair_id)
                    if p[CONF_PAIR_ID] == self._edit_pair_id
                    else p
                    for p in pairs
                ]
                return self.async_create_entry(
                    data={**self.config_entry.options, CONF_PAIRS: new_pairs}
                )

        return self.async_show_form(
            step_id="edit_entity_form",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=current["name"]): selector.TextSelector(),
                    vol.Required(
                        CONF_ENTITY_TYPE, default=current[CONF_ENTITY_TYPE]
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_ENTITY_DOMAINS)
                    ),
                    vol.Required(
                        CONF_PRIMARY, default=current[CONF_PRIMARY]
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=_ENTITY_DOMAINS)
                    ),
                    vol.Required(
                        CONF_FALLBACK, default=current[CONF_FALLBACK]
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=_ENTITY_DOMAINS)
                    ),
                }
            ),
            errors=errors,
        )

    # --------------------------------------------------------------- REMOVE --

    async def async_step_remove_entity(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        pairs = self.config_entry.options.get(CONF_PAIRS, [])

        if user_input is not None:
            new_pairs = [p for p in pairs if p[CONF_PAIR_ID] != user_input[CONF_PAIR_ID]]
            return self.async_create_entry(
                data={**self.config_entry.options, CONF_PAIRS: new_pairs}
            )

        return self.async_show_form(
            step_id="remove_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PAIR_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": p[CONF_PAIR_ID], "label": p["name"]}
                                for p in pairs
                            ]
                        )
                    )
                }
            ),
        )

    # ----------------------------------------------------------- IMPORT JSON --

    async def async_step_import_json(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                items = json.loads(user_input["json_data"])
                if not isinstance(items, list):
                    raise TypeError("Expected a JSON array")

                new_pairs = list(self.config_entry.options.get(CONF_PAIRS, []))
                for item in items:
                    if item.get(CONF_PRIMARY) == item.get(CONF_FALLBACK):
                        errors["base"] = "same_entity"
                        break
                    new_pairs.append(
                        _build_pair(
                            {
                                "name": item["name"],
                                CONF_ENTITY_TYPE: item[CONF_ENTITY_TYPE],
                                CONF_PRIMARY: item[CONF_PRIMARY],
                                CONF_FALLBACK: item[CONF_FALLBACK],
                            }
                        )
                    )

                if not errors:
                    return self.async_create_entry(
                        data={**self.config_entry.options, CONF_PAIRS: new_pairs}
                    )

            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                errors["base"] = "invalid_json"

        return self.async_show_form(
            step_id="import_json",
            data_schema=vol.Schema(
                {
                    vol.Required("json_data"): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True,
                            type=selector.TextSelectorType.TEXT,
                        )
                    )
                }
            ),
            errors=errors,
        )
