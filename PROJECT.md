# Project: Automated Paper Trading System
# Scope: Global Project Architecture

## Architecture
- **Database (Supabase)**: `portfolio` (USD balances, asset quantities), `trades` (trade history).
- **Backend (Python Bot)**: Python script fetching data from Finnhub, using Google AI Studio (Gemini) for trading decisions, and updating Supabase. Support for dry-run.
- **Frontend (React/Vite)**: Dashboard displaying Supabase data (balance, portfolio, history, justifications), configured for GitHub Pages deployment.
- **Automation (GitHub Actions)**: YAML configs to schedule the Python bot via cron.

## Code Layout
- /db: SQL scripts for Supabase.
- /bot: Python bot source code, requirements.txt, .env.example.
- /dashboard: React/Vite application.
- /.github/workflows: GitHub Actions YAML files.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Database Initialization | SQL schema for `portfolio` and `trades` | none | DONE |
| 2 | Python Trading Bot | Bot connecting Finnhub, Gemini, and Supabase | M1 | IN_PROGRESS (804aab2f) |
| 3 | React/Vite Dashboard | Frontend app reading from Supabase | M1 | DONE |
| 4 | GitHub Actions Setup | Cron configuration for bot | M2 | DONE |
| 5 | Final E2E Test Pass | 100% E2E test suite pass | M1, M2, M3, M4 | PLANNED |
| 6 | Adversarial Hardening | Tier 5 tests & fixes | M5 | PLANNED |

## Interface Contracts
### Bot ↔ Database
- Bot queries `portfolio` for USD balances and asset holdings.
- Bot inserts trade records into `trades` table.
- Bot updates `portfolio` balance and asset holdings after trade.
### Dashboard ↔ Database
- Dashboard reads `portfolio` and `trades` to display current state and history.
### Bot ↔ External APIs
- Finnhub API for market data (XAU/USD, AAPL, TSLA, MSFT, GOOGL, AMZN).
- Google AI Studio API for trade decisions (BUY, SELL, HOLD + justification).
