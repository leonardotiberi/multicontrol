from datetime import timedelta
import logging

from aiohttp import ClientSession

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
DOMAIN = "multicontrol"

_LOGGER = logging.getLogger(DOMAIN)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("username") :cv.string,
                vol.Required("password"): cv.string
            }
        )
    },
    extra = vol.ALLOW_EXTRA
)

async def async_setup(hass, config):
    hass.data["multicontrol"] = {"coordinator": MulticontrolCoordinator(hass, config)}
    hass.helpers.discovery.load_platform("climate", DOMAIN, {}, config)
    return True


class MulticontrolCoordinator(DataUpdateCoordinator):
    session: ClientSession

    def __init__(self, hass, config):
        super().__init__(
            hass,
            _LOGGER,
            name="Zehnder Multicontrol",
            update_interval=timedelta(seconds=5),
        )
        self.session = async_get_clientsession(hass)

        c = config.get(DOMAIN)
        if c is None:
            _LOGGER.error("Configurazione non trovataper il dominio {DOMAIN}")

        self.username = c["username"]
        self.password = c["password"]
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
            params = node["params"]["multicontrol"]
            nodes[node["id"]] = {
                "id": node["id"],
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
                {"node_id": idx, "payload": {"multicontrol": {"radiant_enabled": True}}} # set season
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
                    "payload": {"multicontrol": {"radiant_enabled": False}}, # set season
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
