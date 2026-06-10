import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

class TestStressTradingBot(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_over_allocation(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Initial portfolio
        mock_fetch.return_value = {"USD": 100000.0}
        mock_client.return_value = MagicMock()
        
        quotes = {f"SYM{i}": {"current_price": 100.0} for i in range(15)}
        decisions = {f"SYM{i}": MockDecision("BUY", "test") for i in range(15)}
        
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        print("\n--- Executed Trades ---")
        for i, t in enumerate(executed_trades):
            print(f"Trade {i+1} {t['asset_symbol']}: {t['total_value_usd']}")
            
        total_spent = sum(t['total_value_usd'] for t in executed_trades)
        print(f"Total spent: {total_spent}")
        self.assertTrue(total_spent <= 100000.0, "Spent more than we had!")
        
        # We expect only 10 trades to be executed fully, 
        # or maybe the 11th executed for $0, wait, `process_decisions` skips if allocated_usd <= 0?
        # Let's see what happens.
        
if __name__ == '__main__':
    unittest.main()
