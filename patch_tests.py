import os
import glob
import re

test_files = glob.glob('bot/test_*.py')

for fpath in test_files:
    with open(fpath, 'r') as f:
        content = f.read()
    
    if "update_portfolio_balance_optimistic" not in content:
        content = content.replace(
            "@patch('bot.trading.engine.insert_trade')",
            "@patch('bot.trading.engine.insert_trade')\n    @patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)"
        )
        content = content.replace(
            "@patch('bot.trading.engine.insert_trade')\n@patch",
            "@patch('bot.trading.engine.insert_trade')\n@patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)\n@patch"
        )
        content = re.sub(r'def ([a-zA-Z0-9_]+)\(self, mock_insert, mock_upsert', r'def \1(self, mock_opt, mock_insert, mock_upsert', content)
        content = re.sub(r'def ([a-zA-Z0-9_]+)\(mock_insert, mock_upsert', r'def \1(mock_opt, mock_insert, mock_upsert', content)
        
        with open(fpath, 'w') as f:
            f.write(content)
