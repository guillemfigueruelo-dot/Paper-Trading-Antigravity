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

class TestTradeLogic(unittest.TestCase):

    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_dry_run_updates_local_state(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # We hold a reference to the mock portfolio to inspect local state updates
        mock_portfolio = {"USD": 100000.0}
        mock_fetch.return_value = mock_portfolio
        mock_client.return_value = MagicMock()
        
        quotes = {
            "AAPL": {"current_price": 100.0},
            "GOOG": {"current_price": 200.0}
        }
        decisions = {
            "AAPL": MockDecision("BUY", "Test dry run AAPL"),
            "GOOG": MockDecision("BUY", "Test dry run GOOG")
        }
        
        # Execute in dry-run mode
        process_decisions(quotes, decisions, dry_run=True)
        
        # Verify NO external database calls were made
        mock_insert.assert_not_called()
        mock_upsert.assert_not_called()
        
        # Verify local state was STILL updated correctly (No Facade)
        # Initial: 100k. AAPL allocation: 10k -> USD=90k. GOOG allocation: 10k -> USD=80k.
        self.assertEqual(mock_portfolio["USD"], 80000.0)
        self.assertEqual(mock_portfolio["AAPL"], 100.0) # 10k / 100
        self.assertEqual(mock_portfolio["GOOG"], 50.0)  # 10k / 200

if __name__ == '__main__':
    unittest.main()
