import asyncio
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from bot.trading.engine import process_decisions

class MockDecision:
    def __init__(self, action, justification="test"):
        self.action = action
        self.justification = justification

class TestTradeAllocation(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    def test_more_than_10_buys(self, mock_insert, mock_upsert, mock_fetch, mock_client):
        # Initial portfolio USD = 100,000. Base allocation = 10,000.
        mock_fetch.return_value = {"USD": 100000.0}
        mock_client.return_value = MagicMock()
        
        # 12 assets, all BUY
        quotes = {f"SYM_{i}": {"current_price": 100.0} for i in range(12)}
        decisions = {f"SYM_{i}": MockDecision("BUY") for i in range(12)}
        
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        # The first 10 trades will consume 10 * 10,000 = 100,000.
        # The 11th and 12th trades will be skipped due to insufficient balance.
        # This proves the allocation logic depends entirely on dictionary order!
        self.assertEqual(len(executed_trades), 10, "Only 10 trades should execute, 2 missed entirely!")
        
        for t in executed_trades:
            self.assertEqual(t['total_value_usd'], 10000.0)

if __name__ == "__main__":
    unittest.main()
