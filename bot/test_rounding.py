import unittest
from bot.trading.engine import process_decisions
from bot.clients.gemini_client import TradeDecision
from unittest.mock import patch, MagicMock

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

class TestRoundingBug(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    @patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)
    def test_rounding(self, mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
        mock_fetch.return_value = {'USD': 100.0}
        quotes = {'SYM1': {'current_price': 60.0}}
        decisions = {'SYM1': MockDecision('BUY', 'test')}
        process_decisions(quotes, decisions, dry_run=False)

        trade = mock_insert.call_args[0][1]
        quantity = trade['quantity']
        price = trade['price_usd']
        expected_cost = quantity * price
        actual_cost_deducted = trade['total_value_usd']
        self.assertAlmostEqual(expected_cost, actual_cost_deducted, places=6)

if __name__ == '__main__':
    unittest.main()