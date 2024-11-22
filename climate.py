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

        self._attr_name = f"Termostato {node["name"]}"
        self._attr_unique_id = f"multicontrol_climate_{idx}"

        self._attr_hvac_modes = ["off", "cool", "heat"]

        self._attr_temperature_unit = "°C"

        self._attr_target_temperature_high = 26 # cercare configurazione temp_setpoint_max
        self._attr_target_temperature_low = 14 # cercare configurazione temp_setpoint_max
        self._attr_target_temperature_step = 0.1  # cercare configurazione temp_step

        self._attr_max_temp = 26 # cercare configurazione temp_setpoint_max
        self._attr_min_temp = 14  # cercare configurazione temp_setpoint_min

        if node["config"]["fanSupport"]: # cercare fan_speed su config?
            self._attr_supported_features = (ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TARGET_TEMPERATURE)
        else:
            self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self.data = {} # unificare GetNodes e GetParams per ottenere subito i dati

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

    # async def async_set_fan_mode(self, fan_mode: str) -> None:
    #     outval = 4
    #     match fan_mode:
    #         case "low":
    #             outval = 1
    #         case "medium":
    #             outval = 2
    #         case "high":
    #             outval = 3
    #         case "auto":
    #             outval = 4
    #     await self.coordinator.setreg(2 + self.idx * 4, outval)
    #     await self.coordinator.async_request_refresh()
