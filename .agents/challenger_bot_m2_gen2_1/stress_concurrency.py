import asyncio
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification="test"):
        self.action = action
        self.justification = justification

class TestStressConcurrency(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_concurrent_processing_race_condition(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Stress test to show race condition if we attempt concurrent execution
        db_state = {"USD": 100000.0}
        
        def fake_fetch(client):
            time.sleep(0.05) # Simulate IO
            return dict(db_state)
            
        def fake_upsert(client, symbol, balance):
            time.sleep(0.05) # Simulate IO
            db_state[symbol] = balance
            if symbol == 'USD':
                db_state['USD'] = balance
                
        mock_fetch.side_effect = fake_fetch
        mock_upsert.side_effect = fake_upsert
        mock_client.return_value = MagicMock()
        
        # 50 concurrent BUY decisions
        quotes = {f"SYM_{i}": {"current_price": 100.0} for i in range(50)}
        decisions = {f"SYM_{i}": MockDecision("BUY") for i in range(50)}
        
        async def run_concurrently():
            loop = asyncio.get_running_loop()
            def run_single(symbol, decision):
                process_decisions(quotes, {symbol: decision}, dry_run=False)
            
            tasks = [loop.run_in_executor(None, run_single, s, d) for s, d in decisions.items()]
            await asyncio.gather(*tasks)
            
        asyncio.run(run_concurrently())
        
        # If processed correctly and sequentially, 50 buys of $10,000 each
        # should deduct exactly 10 times and hit 0. 
        # But concurrently, they all fetch $100k, calculate $10k, and set to $90k!
        self.assertEqual(db_state['USD'], 90000.0, "Race condition proved: Final balance is $90k despite 50 trades!")

if __name__ == "__main__":
    unittest.main()
