from __future__ import annotations

from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(  # noqa: D103
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    nodes = await coordinator.getNodes()

    entities = []
    for idx, node in nodes.items():
        entities.append(MulticontrolValve(coordinator, idx, node))

    async_add_entities(entities)


# https://developers.home-assistant.io/docs/core/entity/valve/
class MulticontrolValve(CoordinatorEntity, ValveEntity):  # noqa: D101
    def __init__(self, coordinator, idx, node) -> None:  # noqa: D107
        super().__init__(coordinator, context=idx)

        self.idx = idx
        self.name = f"Termostato {node['name']}"
        self._available = False

        self._attr_name = f"Valvola riscaldamento {node['name']}"
        self._attr_unique_id = f"multicontrol_valve_{idx}"

        self._attr_reports_position = False
        self._attr_device_class = ValveDeviceClass.WATER

        self.data = {}

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.idx)},
            name=self.name,
            manufacturer="Zehnder",
            model="Multicontrol",
        )

    @property
    def available(self) -> bool:  # noqa: D102
        return self.data.get("connected", False)

    @property
    def current_valve_position(self) -> ValveState:  # noqa: D102
        if self.data.get("radiant", False):
            return ValveState.OPEN
        return ValveState.CLOSED

    @property
    def is_closed(self) -> bool:  # noqa: D102
        if self.data.get("radiant", False):
            return False
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        self.data = self.coordinator.data[self.idx]
        self.async_write_ha_state()
