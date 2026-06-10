import unittest
from bot.trading.engine import process_decisions
from bot.clients.gemini_client import TradeDecision
from unittest.mock import patch, MagicMock

class MockDecision:
    def __init__(self, action, justification):
        self.action = action
        self.justification = justification

class TestSellSmallBalance(unittest.TestCase):
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    @patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)
    def test_sell_dust(self, mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
        mock_fetch.return_value = {'USD': 100.0, 'SYM1': 0.0000004}
        quotes = {'SYM1': {'current_price': 60.0}}
        decisions = {'SYM1': MockDecision('SELL', 'test')}
        process_decisions(quotes, decisions, dry_run=False)

        self.assertEqual(mock_insert.call_count, 0, 'Dust trade should be skipped and not inserted')

if __name__ == '__main__':
    unittest.main()