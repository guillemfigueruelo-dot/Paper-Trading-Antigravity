import argparse
import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import 'bot' as a module if run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.config import ASSETS
from bot.clients.finnhub_client import fetch_all_quotes
from bot.clients.gemini_client import get_all_trade_decisions
from bot.trading.engine import process_decisions

async def main_async(dry_run: bool):
    print(f"Starting bot for assets: {ASSETS}")
    
    print("Fetching market data concurrently...")
    quotes = await fetch_all_quotes(ASSETS)
    
    # Check if there were errors in fetching
    for symbol, q in quotes.items():
        if "error" in q:
            print(f"Warning: Error fetching quote for {symbol}: {q['error']}")

    print("Querying Gemini for trade decisions concurrently...")
    decisions = await get_all_trade_decisions(quotes)
    
    print("Processing decisions sequentially...")
    process_decisions(quotes, decisions, dry_run=dry_run)
    
    print("Bot execution completed.")

def main():
    parser = argparse.ArgumentParser(description="Python Trading Bot")
    parser.add_argument("--dry-run", action="store_true", help="Run without updating Supabase")
    args = parser.parse_args()

    # Create a new event loop and run
    asyncio.run(main_async(args.dry_run))

if __name__ == "__main__":
    main()
