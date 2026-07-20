from json import loads as json_loads

from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_random_exponential

CBR_RATES_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


@retry(stop=stop_after_attempt(10), wait=wait_random_exponential())
async def fetch_rub_exchange_rate() -> float:
    async with ClientSession() as session, session.get(CBR_RATES_URL) as resp:
        resp.raise_for_status()
        resp_text = await resp.text()
        resp_dict = json_loads(resp_text)

        return resp_dict["Valute"]["USD"]["Value"]
