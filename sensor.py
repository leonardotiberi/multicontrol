from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
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
        if idx != "7CDFA198F1AE":
            continue

        if "caq_out_t" in node:
            add_entities(
                [
                    MulticontrolSensor(
                        hass.data["multicontrol"]["coordinator"],
                        idx,
                        "VMC Temperatura esterna",
                        f"multicontrol_out_t_{idx}",
                        SensorDeviceClass.TEMPERATURE,
                        "caq_out_t",
                        "°C",
                    )
                ]
            )
        if "caq_out_h" in node:
            add_entities(
                [
                    MulticontrolSensor(
                        hass.data["multicontrol"]["coordinator"],
                        idx,
                        "VMC Umidità esterna",
                        f"multicontrol_out_h_{idx}",
                        SensorDeviceClass.HUMIDITY,
                        "caq_out_h",
                        "%",
                    )
                ]
            )


# https://developers.home-assistant.io/docs/core/entity/sensor/
class MulticontrolSensor(CoordinatorEntity, SensorEntity):  # noqa: D101
    def __init__(
        self, coordinator, idx, name, unique_id, device_class, sensor, um
    ) -> None:  # noqa: D107
        super().__init__(coordinator, context=idx)

        self.idx = idx
        self._available = False

        self._attr_name = name
        self._attr_unique_id = unique_id

        self._attr_device_class = device_class
        self._attr_unit_of_measurement = um

        self.data = {}
        self.sensor = sensor

    @property
    def available(self) -> bool:  # noqa: D102
        return self.data.get("connected", False)

    @property
    def native_value(self) -> float:  # noqa: D102
        return self.data.get(self.sensor, 0)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.data = self.coordinator.data[self.idx]
        self.async_write_ha_state()
