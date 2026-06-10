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

class TestTradingBot(unittest.TestCase):
    
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_trade_size_logic(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Initial portfolio
        mock_fetch.return_value = {"USD": 100000.0}
        mock_client.return_value = MagicMock()
        
        quotes = {
            "AAPL": {"current_price": 100.0},
            "GOOG": {"current_price": 100.0},
            "MSFT": {"current_price": 100.0}
        }
        decisions = {
            "AAPL": MockDecision("BUY", "test"),
            "GOOG": MockDecision("BUY", "test"),
            "MSFT": MockDecision("BUY", "test")
        }
        
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        print("\n--- Executed Trades ---")
        for t in executed_trades:
            print(f"{t['asset_symbol']}: {t['total_value_usd']}")
            
        self.assertEqual(executed_trades[0]['total_value_usd'], executed_trades[1]['total_value_usd'], 
                         "Trade sizes shrink due to sequential evaluation of balance!")

if __name__ == '__main__':
    unittest.main()
