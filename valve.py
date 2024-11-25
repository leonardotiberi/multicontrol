from __future__ import annotations

from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity


async def async_setup_platform(  # noqa: D103
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if discovery_info is None:
        return

    nodes = await hass.data["multicontrol"]["coordinator"].getNodes()
    for idx, node in nodes.items():
        add_entities(
            [MulticontrolValve(hass.data["multicontrol"]["coordinator"], idx, node)]
        )


# https://developers.home-assistant.io/docs/core/entity/valve/
class MulticontrolValve(CoordinatorEntity, ValveEntity):  # noqa: D101
    def __init__(self, coordinator, idx, node) -> None:  # noqa: D107
        super().__init__(coordinator, context=idx)

        self.idx = idx
        self._available = False

        self._attr_name = f"Valvola riscaldamento {node["name"]}"
        self._attr_unique_id = f"multicontrol_valve_{idx}"

        self._attr_reports_position = False
        self._attr_device_class = ValveDeviceClass.WATER

        self.data = {}

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
