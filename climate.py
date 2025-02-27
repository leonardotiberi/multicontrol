from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE
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
            [MulticontrolClimate(hass.data["multicontrol"]["coordinator"], idx, node)]
        )


class MulticontrolClimate(CoordinatorEntity, ClimateEntity):  # noqa: D101
    def __init__(self, coordinator, idx, node) -> None:  # noqa: D107
        super().__init__(coordinator, context=idx)

        self.idx = idx
        self._available = False

        fan_support = node["config"].get("fan_speed", None) is not None
        if node["name"] == "Lavanderia":
            print(fan_support)
            print(node["config"])

        self._attr_name = f"Termostato {node["name"]}"
        self._attr_unique_id = f"multicontrol_climate_{idx}"

        self._attr_hvac_modes = ["off", "cool", "heat"]

        self._attr_temperature_unit = "°C"

        self._attr_target_temperature_high = (
            26  # cercare configurazione temp_setpoint_max
        )
        self._attr_target_temperature_low = (
            14  # cercare configurazione temp_setpoint_max
        )
        self._attr_target_temperature_step = 0.1  # cercare configurazione temp_step

        self._attr_max_temp = 26  # cercare configurazione temp_setpoint_max
        self._attr_min_temp = 14  # cercare configurazione temp_setpoint_min

        if fan_support:
            self._attr_fan_modes = ("off", "low", "medium", "high")
            self._attr_supported_features = (
                ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE
            )
        else:
            self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self.data = {}

    @property
    def available(self) -> bool:  # noqa: D102
        return self.data.get("connected", False)

    @property
    def target_temperature(self) -> float | None:  # noqa: D102
        return self.data.get("temp_setpoint", None)

    @property
    def current_temperature(self) -> float | None:  # noqa: D102
        return self.data.get("temp", None)

    @property
    def target_humidity(self) -> float | None:  # noqa: D102
        return self.data.get("humidity_correction", None)

    @property
    def current_humidity(self) -> float | None:  # noqa: D102
        return self.data.get("humidity", None)

    @property
    def hvac_mode(self) -> HVACMode | None:  # noqa: D102
        if self.data.get("radiant_enabled", False):
            if self.data.get("season", None) == 1:
                return HVACMode.HEAT
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def fan_mode(self):
        speed = self.data.get("fan_speed", 0)
        print(speed)
        print(self.data)
        if speed == 1:
            return "low"
        elif speed == 2:
            return "medium"
        elif speed == 3:
            return "high"
        return "off"

    @callback
    def _handle_coordinator_update(self) -> None:
        self.data = self.coordinator.data[self.idx]
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:  # noqa: D102
        match hvac_mode:
            case HVACMode.COOL:
                await self.coordinator.setCool(self.idx)
            case HVACMode.HEAT:
                await self.coordinator.setHeat(self.idx)
            case HVACMode.OFF:
                await self.coordinator.setOff(self.idx)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:  # noqa: D102
        if ATTR_TEMPERATURE not in kwargs:
            raise ValueError("Temperatura non specificata")

        target_temperature = kwargs[ATTR_TEMPERATURE]
        await self.coordinator.setTargetTemperature(
            self.idx,
            target_temperature,
        )
        self._attr_target_temperature = target_temperature
        await self.coordinator.async_request_refresh()

    @property
    def fan_mode(self) -> str:
        speed = self.data.get("fan_speed", 0)
        return ["off", "low", "medium", "high"][speed]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        mode = 0
        match fan_mode:
            case "low":
                mode = 1
            case "medium":
                mode = 2
            case "high":
                mode = 3
        await self.coordinator.setFanSpeed(self.idx, mode)
        self._attr_fan_mode = fan_mode
        await self.coordinator.async_request_refresh()
