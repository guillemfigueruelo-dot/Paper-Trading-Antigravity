# Challenge Report

## Challenge Summary

**Overall risk assessment**: CRITICAL
**Verdict**: FAIL

## Challenges

### [High] Challenge 1: Sequential processing causes shrinking trade sizes
- **Assumption challenged**: That an allocation of 10% of USD balance yields equal sizing across a batch of simultaneous trade decisions.
- **Attack scenario**: Sending multiple `BUY` decisions in a single batch.
- **Blast radius**: The first asset processed gets exactly 10% of the initial USD balance. The second asset gets 10% of the *remaining* 90%, the third gets 10% of the *remaining* 81%, etc. This creates arbitrary size variations dependent purely on dictionary iteration order.
- **Mitigation**: Calculate the allocated USD based on the initial `usd_balance` captured *before* the batch processing loop starts, or explicitly split the allocation equally among all `BUY` signals.

### [Critical] Challenge 2: Race condition if executed concurrently
- **Assumption challenged**: That the system safely processes multiple assets concurrently.
- **Attack scenario**: Wrapping `process_decisions` in an async `run_in_executor` to process multiple assets concurrently.
- **Blast radius**: `portfolio["USD"]` is fetched at the beginning, mathematically modified, and then written back via `upsert`. When executed concurrently, multiple tasks read the same initial balance, subtract their individual allocations, and overwrite the DB. This results in lost balance updates, essentially creating free money.
- **Mitigation**: Move from direct upserts of absolute balances to atomic increments/decrements in the database (e.g., using an RPC in Supabase or SQL `UPDATE balance = balance - X`).


## Handoff Components

### 1. Observation
In `bot/trading/engine.py` (lines 41-53), the loop sequentially iterates over decisions:
```python
        usd_balance = float(portfolio["USD"])

        if action == "BUY":
            if usd_balance > 0:
                allocated_usd = usd_balance * 0.10
                ...
                    # Update local state
                    portfolio["USD"] = usd_balance - allocated_usd
```
I wrote `bot/test_engine.py` which mocks a 100k USD balance and returns `BUY` for AAPL, GOOG, and MSFT. The empirical output showed:
```
AAPL: 10000.0
GOOG: 9000.0
MSFT: 8100.0
AssertionError: 10000.0 != 9000.0 : Trade sizes shrink due to sequential evaluation of balance!
```

Additionally, to test concurrency, I wrote `bot/test_concurrency.py` simulating concurrent execution using `asyncio.gather`. Output verified the race condition:
```
--- Starting Trade Execution (Dry Run: False) ---
Initial USD Balance: $100000.00
ACTION: BUY 100.000000 AAPL for $10000.00
ACTION: BUY 100.000000 GOOG for $10000.00
Executed BUY in DB.
--- Final USD Balance: $90000.00 ---
Final DB USD Balance after concurrent processing: 90000.0
RACE CONDITION CONFIRMED: One update overwrote the other!
```

### 2. Logic Chain
1. The requirement is to evaluate the bot's ability to "process multiple assets concurrently and evaluate trade size logic correctly".
2. The current implementation in `process_decisions` is synchronous and processes sequentially.
3. Due to the sequential iteration mutating the local `portfolio["USD"]` state continuously, the 10% trade size logic inherently shrinks for each subsequent asset.
4. When attempting to wrap the logic to process concurrently, the lack of atomic database operations and atomic local state locking causes a critical race condition where multiple concurrent `upsert` operations overwrite the absolute USD balance.
5. Therefore, the bot fails both criteria: its trade size logic produces unintended arbitrary sizes, and it cannot safely process assets concurrently without losing state integrity.

### 3. Caveats
- I simulated the Supabase database state in memory during the concurrency tests rather than hitting a live database to avoid external dependencies, though the logic gap directly translates to the database layer due to the use of absolute `upsert` calls rather than atomic increments.

### 4. Conclusion
The bot **FAILS** the correctness verification. The trade sizing logic relies on a mutating balance during batch processing leading to arbitrary shrinkage. Furthermore, the bot is not thread-safe and will silently drop balance deductions (overwriting state) if made to run concurrently.

### 5. Verification Method
To independently verify the trade size shrinkage:
1. Run `python bot/test_engine.py` from the root workspace directory. You will see the sequential trade sizes (`10000.0`, `9000.0`, `8100.0`).
2. To independently verify the concurrency race condition, run `python bot/test_concurrency.py`. You will observe two $10,000 purchases occurring on a $100,000 balance, but the final balance remains $90,000 instead of $80,000.
