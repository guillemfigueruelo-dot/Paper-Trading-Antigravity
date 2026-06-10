import sys

with open(r"c:\Users\Figue\Desktop\Paper Trading Antigravity\bot\test_trade_logic.py", "rb") as f:
    data = f.read()

with open(r"c:\Users\Figue\Desktop\Paper Trading Antigravity\.agents\auditor_bot_m2\output.txt", "w") as f:
    f.write(repr(data))
