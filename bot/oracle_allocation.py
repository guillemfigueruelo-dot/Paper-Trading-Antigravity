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

class TestAllocationOracle(unittest.TestCase):
    
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_zero_initial_usd_blocks_buys_after_sells(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Initial portfolio has 0 USD, but 100 AAPL shares.
        mock_fetch.return_value = {"USD": 0.0, "AAPL": 100.0}
        mock_client.return_value = MagicMock()
        
        quotes = {
            "AAPL": {"current_price": 150.0},
            "MSFT": {"current_price": 200.0}
        }
        
        # We sell AAPL first, which should give us 150 * 100 = $15,000 USD.
        # Then we buy MSFT. Since we have $15,000, we should be able to allocate 10% of our portfolio or something.
        decisions = {
            "AAPL": MockDecision("SELL", "taking profits"),
            "MSFT": MockDecision("BUY", "reinvesting")
        }
        
        # Run engine
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        print("\n--- Executed Trades ---")
        for i, t in enumerate(executed_trades):
            print(f"Trade {i+1} {t['trade_type']} {t['asset_symbol']}: ${t['total_value_usd']}")
            if t['trade_type'] == 'BUY':
                self.assertGreater(t['total_value_usd'], 0.0, "BUY trade executed for $0.0 due to stale base_allocation!")

if __name__ == '__main__':
    unittest.main()
