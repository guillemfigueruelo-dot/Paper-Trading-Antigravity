import aiohttp
import asyncio
from bot.config import FINNHUB_API_KEY, FINNHUB_SYMBOL_MAP

import time

async def fetch_quote(session: aiohttp.ClientSession, symbol: str):
    finnhub_symbol = FINNHUB_SYMBOL_MAP.get(symbol, symbol)
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={finnhub_symbol}&token={FINNHUB_API_KEY}"
    
    to_time = int(time.time())
    from_time = to_time - (10 * 24 * 60 * 60)
    
    if "OANDA:" in finnhub_symbol or "FX:" in finnhub_symbol:
        asset_type = "forex"
    elif "BINANCE:" in finnhub_symbol or "KRAKEN:" in finnhub_symbol:
        asset_type = "crypto"
    else:
        asset_type = "stock"
        
    candle_url = f"https://finnhub.io/api/v1/{asset_type}/candle?symbol={finnhub_symbol}&resolution=D&from={from_time}&to={to_time}&token={FINNHUB_API_KEY}"
    
    try:
        quote_data = {}
        if asset_type == "stock":
            async with session.get(quote_url) as response:
                if response.status == 200:
                    quote_data = await response.json()
                else:
                    return {"symbol": symbol, "current_price": 0.0, "error": f"HTTP {response.status} on quote"}
                
        candles_data = {}
        async with session.get(candle_url) as candle_res:
            if candle_res.status == 200:
                candles_data = await candle_res.json()

        if asset_type == "stock":
            current_price = quote_data.get("c", 0.0)
        else:
            if candles_data.get("s") == "ok" and "c" in candles_data and len(candles_data["c"]) > 0:
                current_price = candles_data["c"][-1]
            else:
                current_price = 0.0

        # data returns c (current price), d, dp, h, l, o, pc
        return {
            "symbol": symbol, 
            "current_price": current_price, 
            "raw": quote_data,
            "candles": candles_data
        }
    except Exception as e:
        return {"symbol": symbol, "current_price": 0.0, "error": str(e)}

async def fetch_all_quotes(symbols: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_quote(session, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return {res["symbol"]: res for res in results}
