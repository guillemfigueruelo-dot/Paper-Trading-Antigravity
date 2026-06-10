import asyncio
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from bot.trading.engine import process_decisions
from bot.clients.gemini_client import TradeDecision

async def mock_async_process(quotes, decisions, mock_insert, mock_upsert, mock_fetch, mock_client):
    loop = asyncio.get_running_loop()
    
    def run_single(symbol, decision):
        process_decisions(quotes, {symbol: decision}, dry_run=False)
        
    tasks = []
    for symbol, decision in decisions.items():
        tasks.append(loop.run_in_executor(None, run_single, symbol, decision))
        
    await asyncio.gather(*tasks)

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

@patch('bot.trading.engine.get_supabase_client')
@patch('bot.trading.engine.fetch_portfolio')
@patch('bot.trading.engine.upsert_portfolio_balance')
@patch('bot.trading.engine.insert_trade')
def run_concurrency_test(mock_insert, mock_upsert, mock_fetch, mock_client):
    db_state = {"USD": 100000.0}
    
    def fake_fetch(client):
        time.sleep(0.1) # Simulate network IO
        return dict(db_state)
    mock_fetch.side_effect = fake_fetch
    mock_client.return_value = MagicMock()
    
    def fake_upsert(client, symbol, balance):
        time.sleep(0.1) # Simulate network IO
        db_state[symbol] = balance
        if symbol == 'USD':
            db_state['USD'] = balance
    mock_upsert.side_effect = fake_upsert
    
    quotes = {
        "AAPL": {"current_price": 100.0},
        "GOOG": {"current_price": 100.0},
    }
    decisions = {
        "AAPL": MockDecision("BUY", "test"),
        "GOOG": MockDecision("BUY", "test"),
    }
    
    asyncio.run(mock_async_process(quotes, decisions, mock_insert, mock_upsert, mock_fetch, mock_client))
    
    print(f"Final DB USD Balance after concurrent processing: {db_state['USD']}")
    if db_state['USD'] == 90000.0:
        print("RACE CONDITION CONFIRMED: One update overwrote the other!")

if __name__ == '__main__':
    run_concurrency_test()
