from datetime import timedelta
import logging

from aiohttp import ClientSession
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(DOMAIN)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Required("username"): cv.string, vol.Required("password"): cv.string}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = MulticontrolCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MulticontrolCoordinator(DataUpdateCoordinator):
    session: ClientSession

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name="Zehnder Multicontrol",
            update_interval=timedelta(seconds=5),
        )
        self.session = async_get_clientsession(hass)

        self.username = entry.data["username"]
        self.password = entry.data["password"]
        self.api_url = "https://api.rainmaker.espressif.com/v1/"
        self.api_token = ""

    async def _async_update_data(self):
        return await self.getNodes()

    async def login(self) -> None:
        # LOGIN
        _LOGGER.debug("Login")
        async with self.session.post(
            self.api_url + "login2",
            json={"user_name": self.username, "password": self.password},
        ) as response:
            if response.status == 200:
                res = await response.json()
                self.api_token = res["accesstoken"]
            else:
                _LOGGER.error("Login fail")

    async def getNodes(self) -> any:
        await self.login()

        # GET PARAMS
        _LOGGER.debug("Get params nodes")
        headers = {"Authorization": self.api_token}
        async with self.session.get(
            self.api_url + "user/nodes?node_details=1", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
            else:
                _LOGGER.error("Ger params fail")
                return False

        nodes = {}
        for node in data["node_details"]:
            configs = {}
            for config in node["config"]["devices"][0]["params"]:
                configs[config["name"]] = config

            params = node["params"]["multicontrol"]
            nodes[node["id"]] = {
                "id": node["id"],
                "config": configs,
                "connected": node["status"]["connectivity"]["connected"],
                "name": params["Name"],
                "alarm": params["alarm"],
                "dehumidifier": params["dehumidifier"],
                "humidity": params["humidity"],
                "humidity_correction": params["humidity_correction"],
                "post_treatment_automatic": params["post_treatment_automatic"],
                "post_treatment_schedule": params["post_treatment_schedule"],
                "radiant": params["radiant"],
                "radiant_automatic": params["radiant_automatic"],
                "radiant_enabled": params["radiant_enabled"],
                "radiant_schedule": params["radiant_schedule"],
                "season": params["season"],
                "season_automatic": params["season_automatic"],
                "temp": params["temp"],
                "temp_setpoint": params["temp_setpoint"],
                # fan params
                "fan_speed": params.get("fan_speed"),
                "caq_out_t": params.get("caq_out_t"),
                "caq_out_h": params.get("caq_out_h"),
            }
        return nodes

    async def setTargetTemperature(self, idx, value) -> None:
        await self.login()

        _LOGGER.debug("Set target temperature")
        headers = {"Authorization": self.api_token}
        async with self.session.put(
            self.api_url + "user/nodes/params",
            headers=headers,
            json=[
                {"node_id": idx, "payload": {"multicontrol": {"temp_setpoint": value}}}
            ],
        ) as response:
            if response.status == 207:
                _LOGGER.info("Target temperature ok")
            else:
                _LOGGER.error("Ger params fail")

    async def setHeat(self, idx) -> None:
        await self.login()

        _LOGGER.debug("Set heat")
        headers = {"Authorization": self.api_token}
        async with self.session.put(
            self.api_url + "user/nodes/params",
            headers=headers,
            json=[
                {
                    "node_id": idx,
                    "payload": {"multicontrol": {"radiant_enabled": True}},
                }  # set season
            ],
        ) as response:
            if response.status == 207:
                _LOGGER.info("Set heat ok")
            else:
                _LOGGER.error("Ger params fail")

    async def setCool(self, idx) -> None:
        await self.login()

        _LOGGER.debug("Set heat")
        headers = {"Authorization": self.api_token}
        async with self.session.put(
            self.api_url + "user/nodes/params",
            headers=headers,
            json=[
                {
                    "node_id": idx,
                    "payload": {
                        "multicontrol": {"radiant_enabled": False}
                    },  # set season
                }
            ],
        ) as response:
            if response.status == 207:
                _LOGGER.info("Set cool ok")
            else:
                _LOGGER.error("Ger params fail")

    async def setOff(self, idx) -> None:
        await self.login()

        _LOGGER.debug("Set off")
        headers = {"Authorization": self.api_token}
        async with self.session.put(
            self.api_url + "user/nodes/params",
            headers=headers,
            json=[
                {
                    "node_id": idx,
                    "payload": {"multicontrol": {"radiant_enabled": False}},
                }
            ],
        ) as response:
            if response.status == 207:
                _LOGGER.info("Set off ok")
            else:
                _LOGGER.error("Ger params fail")

    async def setFanSpeed(self, idx, speed) -> None:
        await self.login()

        _LOGGER.debug("Set fan speed")
        headers = {"Authorization": self.api_token}
        async with self.session.put(
            self.api_url + "user/nodes/params",
            headers=headers,
            json=[
                {
                    "node_id": idx,
                    "payload": {"multicontrol": {"fan_speed": speed}},
                }
            ],
        ) as response:
            if response.status == 207:
                _LOGGER.info("Set fan speed ok")
            else:
                _LOGGER.error("Ger params fail")
