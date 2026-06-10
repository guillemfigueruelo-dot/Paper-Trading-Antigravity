import aiohttp
import asyncio
import json
from pydantic import BaseModel
from bot.config import GEMINI_API_KEY

class TradeDecision(BaseModel):
    action: str
    justification: str

async def get_trade_decision(session: aiohttp.ClientSession, symbol: str, quote_data: dict):
    if not GEMINI_API_KEY:
        # Fallback if no key
        return TradeDecision(action="HOLD", justification="No Gemini API key")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Analyze the following market and historical candle data for {symbol}: {quote_data}. Decide whether to BUY, SELL, or HOLD. Provide a justification."
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": "You are a trading bot. You must respond with valid JSON matching the schema."}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "enum": ["BUY", "SELL", "HOLD"]
                    },
                    "justification": {
                        "type": "STRING"
                    }
                },
                "required": ["action", "justification"]
            }
        }
    }

    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                text_response = data["candidates"][0]["content"]["parts"][0]["text"]
                
                cleaned_text = text_response.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                parsed = json.loads(cleaned_text)
                return TradeDecision(action=parsed.get("action", "HOLD"), justification=parsed.get("justification", "Unknown"))
            else:
                text = await response.text()
                return TradeDecision(action="HOLD", justification=f"API Error {response.status}: {text}")
    except Exception as e:
        return TradeDecision(action="HOLD", justification=f"Exception: {str(e)}")

async def get_all_trade_decisions(quotes: dict):
    async with aiohttp.ClientSession() as session:
        tasks = []
        symbols = list(quotes.keys())
        for symbol in symbols:
            tasks.append(get_trade_decision(session, symbol, quotes[symbol]))
        
        results = await asyncio.gather(*tasks)
        return {symbols[i]: results[i] for i in range(len(symbols))}
