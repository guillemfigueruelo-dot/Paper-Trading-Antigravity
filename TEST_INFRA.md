# E2E Test Infra: Paper Trading Antigravity

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.
- Progressive Testability: Earliest milestones (e.g. DB script, dry-run CLI) should be testable without the full stack.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| F1 | Database Schema | ORIGINAL_REQUEST R1 | 5 | 5 | ✓ |
| F2 | Finnhub Data Fetching | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| F3 | AI Trading Decision | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| F4 | Trade Execution & Logging | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| F5 | Multi-asset Processing | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| F6 | Dry-Run Mode | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| F7 | Frontend Dashboard | ORIGINAL_REQUEST R3 | 5 | 5 | ✓ |
| F8 | GitHub Actions Automation | ORIGINAL_REQUEST R4 | 5 | 5 | ✓ |

## Test Architecture
- **Test runner**: `pytest`
- **Location**: `tests/e2e/`
- **Invocation**: `pytest tests/e2e/`
- **Pass/fail semantics**: Exit code 0 indicates full pass. Exit code > 0 indicates failure.
- **Test case format**: Pytest test functions (`test_*.py`). Tests interact with the bot via CLI subprocess calls, and with the database via direct queries (using a test Supabase instance or local postgres). The frontend is tested via Playwright. External APIs (Finnhub, Gemini/OpenAI) will be mocked via HTTP interceptors or mock servers during testing, unless end-to-end integration is explicitly desired.
- **Directory layout**:
  - `tests/e2e/tier1_feature/`
  - `tests/e2e/tier2_boundary/`
  - `tests/e2e/tier3_pairwise/`
  - `tests/e2e/tier4_realworld/`
  - `tests/e2e/conftest.py`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full daily cron run with simulated volatile market (triggers BUYS and SELLS) | F1, F2, F3, F4, F5, F8 | High |
| 2 | Bot execution with insufficient funds (ensures proper viability checking) | F1, F2, F3, F4, F5 | Medium |
| 3 | Dry-run mode over a full set of assets, ensuring no state mutations occur | F1, F2, F3, F5, F6 | Medium |
| 4 | User verifies dashboard after a week of automated trading activity | F1, F4, F7 | High |
| 5 | AI consistently returns HOLD for all assets (quiet market scenario) | F1, F2, F3, F4, F5 | Medium |

## Coverage Thresholds
- **Tier 1**: ≥5 per feature (Total: 40 tests)
- **Tier 2**: ≥5 per feature (where boundaries exist) (Total: 40 tests)
- **Tier 3**: pairwise coverage of major feature interactions (Total: ~15 tests)
- **Tier 4**: ≥5 realistic application scenarios (Total: 5 tests)
- **Total Minimum Expected**: ~100 tests
