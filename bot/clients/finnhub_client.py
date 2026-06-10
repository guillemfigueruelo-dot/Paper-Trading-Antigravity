import aiohttp
import asyncio
from bot.config import FINNHUB_API_KEY, FINNHUB_SYMBOL_MAP

async def fetch_quote(session: aiohttp.ClientSession, symbol: str):
    finnhub_symbol = FINNHUB_SYMBOL_MAP.get(symbol, symbol)
    url = f"https://finnhub.io/api/v1/quote?symbol={finnhub_symbol}&token={FINNHUB_API_KEY}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # data returns c (current price), d, dp, h, l, o, pc
                return {"symbol": symbol, "current_price": data.get("c", 0.0), "raw": data}
            else:
                return {"symbol": symbol, "current_price": 0.0, "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"symbol": symbol, "current_price": 0.0, "error": str(e)}

async def fetch_all_quotes(symbols: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_quote(session, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return {res["symbol"]: res for res in results}
