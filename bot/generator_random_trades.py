import sys
import os
import random
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

class TestTradeGenerator(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_random_trades_invariants(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Generate 100 assets
        assets = [f"SYM_{i}" for i in range(100)]
        
        # Initial portfolio
        initial_usd = 50000.0
        portfolio_state = {"USD": initial_usd}
        for a in assets:
            if random.random() > 0.5:
                portfolio_state[a] = random.uniform(10.0, 100.0)
                
        mock_fetch.return_value = dict(portfolio_state)
        mock_client.return_value = MagicMock()
        
        quotes = {a: {"current_price": random.uniform(1.0, 500.0)} for a in assets}
        
        # Generate random decisions
        decisions = {}
        for a in assets:
            action = random.choice(["BUY", "SELL", "HOLD"])
            decisions[a] = MockDecision(action, "random action")
            
        # Process
        process_decisions(quotes, decisions, dry_run=False)
        
        # Verify invariants
        executed_trades = [call[0][1] for call in mock_insert.call_args_list]
        
        total_usd_spent = sum(t['total_value_usd'] for t in executed_trades if t['trade_type'] == 'BUY')
        total_usd_gained = sum(t['total_value_usd'] for t in executed_trades if t['trade_type'] == 'SELL')
        
        # Is final balance logically consistent?
        # Since process_decisions mutates its local 'portfolio' dict, we can't easily assert the final value directly 
        # unless we mock upsert_portfolio_balance.
        final_usd = initial_usd
        upsert_calls = mock_upsert.call_args_list
        usd_updates = [call[0][2] for call in upsert_calls if call[0][1] == 'USD']
        if usd_updates:
            final_usd = usd_updates[-1]
            
        # Assert USD balance never drops below zero
        self.assertGreaterEqual(final_usd, 0.0, "USD balance dropped below zero!")
        
        # Assert logical consistency
        expected_usd = initial_usd - total_usd_spent + total_usd_gained
        self.assertAlmostEqual(final_usd, expected_usd, places=2, msg="USD balance updates do not match total spent/gained!")
        
        # Check if any BUY trade was $0.0 despite having USD
        # If initial_usd > 0, base_allocation > 0, so this might not happen unless USD runs out
        for t in executed_trades:
            if t['trade_type'] == 'BUY':
                self.assertGreaterEqual(t['total_value_usd'], 0.0)

if __name__ == '__main__':
    unittest.main()
