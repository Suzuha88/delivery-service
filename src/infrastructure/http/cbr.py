from json import loads as json_loads

from aiohttp import ClientSession

CBR_RATES_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


async def fetch_rub_exchange_rate() -> float:
    async with ClientSession() as session, session.get(CBR_RATES_URL) as resp:
        resp.raise_for_status()
        resp_text = await resp.text()
        resp_dict = json_loads(resp_text)

        return resp_dict["Valute"]["USD"]["Value"]
