import os
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Assets to process
ASSETS = ["XAU/USD", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]

# Map logical symbol to Finnhub symbol
# XAU/USD is typically available via OANDA:XAU_USD on Finnhub
FINNHUB_SYMBOL_MAP = {
    "XAU/USD": "OANDA:XAU_USD",
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN"
}
