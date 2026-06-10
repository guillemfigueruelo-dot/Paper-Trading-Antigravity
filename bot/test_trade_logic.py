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
    @patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)
    def test_trade_sizes_equal(self, mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
        db_state = {"USD": 100000.0}
        def fake_fetch(client):
            return dict(db_state)
        mock_fetch.side_effect = fake_fetch
        def fake_opt(client, symbol, old_val, new_val):
            if float(db_state.get(symbol, 0.0)) == float(old_val):
                db_state[symbol] = float(new_val)
                return True
            return False
        mock_opt.side_effect = fake_opt

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
            
        self.assertEqual(len(executed_trades), 3)
        self.assertEqual(executed_trades[0]['total_value_usd'], 10000.0)
        self.assertEqual(executed_trades[1]['total_value_usd'], 10000.0)
        self.assertEqual(executed_trades[2]['total_value_usd'], 10000.0)
        self.assertEqual(executed_trades[0]['total_value_usd'], executed_trades[1]['total_value_usd'])

    @patch('sys.stdout')
    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    def test_dry_run_updates_local_state(self, mock_fetch, mock_client, mock_stdout):
        mock_fetch.return_value = {"USD": 100000.0}
        mock_client.return_value = MagicMock()
        
        quotes = {
            "AAPL": {"current_price": 100.0},
        }
        decisions = {
            "AAPL": MockDecision("BUY", "test"),
        }
        
        # Calling process_decisions with dry_run=True should still decrease the local balance 
        # but not call the db inserts.
        process_decisions(quotes, decisions, dry_run=True)
        
        # In dry run, db inserts/upserts should not be called
        # We can check that the final balance printed to stdout reflects the updated local state
        # The base allocation is 10,000, so final balance should be 90,000.
        
        calls = mock_stdout.write.call_args_list
        output = "".join([c[0][0] for c in calls])
        self.assertIn("Final USD Balance: $90000.00", output)

    @patch('bot.trading.engine.get_supabase_client')
    @patch('bot.trading.engine.fetch_portfolio')
    @patch('bot.trading.engine.upsert_portfolio_balance')
    @patch('bot.trading.engine.insert_trade')
    @patch('bot.trading.engine.update_portfolio_balance_optimistic')
    def test_sell_proceeds_reinvested(self, mock_opt, mock_insert, mock_upsert, mock_fetch, mock_client):
        # We start with $0 USD, but we have 10 AAPL shares (worth $1000 total)
        db_state = {"USD": 0.0, "AAPL": 10.0}
        def fake_fetch(client):
            return dict(db_state)
        mock_fetch.side_effect = fake_fetch
        
        def fake_opt(client, symbol, old_val, new_val):
            if float(db_state.get(symbol, 0.0)) == float(old_val):
                db_state[symbol] = float(new_val)
                return True
            return False
        mock_opt.side_effect = fake_opt
        
        mock_client.return_value = MagicMock()
        
        quotes = {
            "AAPL": {"current_price": 100.0},
            "GOOG": {"current_price": 100.0},
        }
        decisions = {
            "AAPL": MockDecision("SELL", "sell to free up cash"),
            "GOOG": MockDecision("BUY", "buy with freed cash"),
        }
        
        # Dry run false to capture db inserts
        process_decisions(quotes, decisions, dry_run=False)
        
        executed_trades = []
        for call in mock_insert.call_args_list:
            trade_data = call[0][1]
            executed_trades.append(trade_data)
            
        self.assertEqual(len(executed_trades), 2)
        
        sell_trade = next(t for t in executed_trades if t['trade_type'] == 'SELL')
        buy_trade = next(t for t in executed_trades if t['trade_type'] == 'BUY')
        
        # Sold 10 AAPL at 100 = 1000 USD
        self.assertEqual(sell_trade['total_value_usd'], 1000.0)
        # Reinvested 10% of new balance (1000 * 0.10) = 100 USD
        self.assertEqual(buy_trade['total_value_usd'], 100.0)

if __name__ == '__main__':
    unittest.main()
