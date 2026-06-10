import os
import glob
import re

test_files = glob.glob('bot/test_*.py')

for fpath in test_files:
    with open(fpath, 'r') as f:
        content = f.read()

    # Revert the previous bad indents
    content = content.replace("    @patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)", "@patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)")

    # Find the indent before @patch('bot.trading.engine.insert_trade')
    new_content = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "@patch('bot.trading.engine.update_portfolio_balance_optimistic'" in line:
            # We already fixed it roughly, let's fix its indent properly based on the next line or previous
            if i > 0 and "insert_trade" in lines[i-1]:
                indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                lines[i] = " " * indent + "@patch('bot.trading.engine.update_portfolio_balance_optimistic', return_value=True)"
    
    with open(fpath, 'w') as f:
        f.write('\n'.join(lines))
