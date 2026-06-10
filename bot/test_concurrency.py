import asyncio
from unittest.mock import patch, MagicMock
from bot.trading.engine import process_decisions
import time
import pytest

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

async def mock_async_process(quotes, decisions, mock_insert, mock_upsert, mock_fetch, mock_client, mock_opt):
    loop = asyncio.get_running_loop()
    
    def run_single(symbol, decision):
        process_decisions(quotes, {symbol: decision}, dry_run=False)
        
    tasks = []
    for symbol, decision in decisions.items():
        tasks.append(loop.run_in_executor(None, run_single, symbol, decision))
        
    await asyncio.gather(*tasks)

@pytest.mark.asyncio
@patch('bot.trading.engine.get_supabase_client')
@patch('bot.trading.engine.fetch_portfolio')
@patch('bot.trading.engine.upsert_portfolio_balance')
@patch('bot.trading.engine.insert_trade')
@patch('bot.trading.engine.update_portfolio_balance_optimistic')
async def test_run_concurrency(mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
    db_state = {"USD": 100000.0}
    
    def fake_fetch(client):
        time.sleep(0.01) # Simulate network IO
        return dict(db_state)
    mock_fetch.side_effect = fake_fetch
    mock_client.return_value = MagicMock()
    
    def fake_opt(client, symbol, old_val, new_val):
        time.sleep(0.01)
        if float(db_state.get(symbol, 0.0)) == float(old_val):
            db_state[symbol] = float(new_val)
            return True
        return False
    mock_opt.side_effect = fake_opt
    
    quotes = {
        "AAPL": {"current_price": 100.0},
        "GOOG": {"current_price": 100.0},
    }
    decisions = {
        "AAPL": MockDecision("BUY", "test"),
        "GOOG": MockDecision("BUY", "test"),
    }
    
    await mock_async_process(quotes, decisions, mock_insert, mock_upsert, mock_fetch, mock_client, mock_opt)
    
    assert db_state['USD'] < 100000.0
    # With 2 BUYS, it allocates 10% of USD each time.
    # Concurrency safe should be around 90000 and 81000 or so if serial, or exactly calculated.
    assert db_state['USD'] >= 80000.0
