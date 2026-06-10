# Original User Request

## Initial Request — 2026-06-10T10:32:20+02:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Execute the implementation

Automated paper trading system consisting of a React/Vite dashboard, a Python trading bot executed via GitHub Actions, integrating Finnhub for market data, Google AI Studio for trade decisions, and Supabase for state management.

Working directory: c:/Users/Figue/Desktop/Paper Trading Antigravity
Integrity mode: development

## Requirements

### R1. Database Schema (Supabase)
Design the SQL schema and integration for two tables: `portfolio` (USD balances and asset quantities) and `trades` (complete history). Initial balance should be 100,000 USD. Provide the SQL initialization scripts.

### R2. Trading Bot (Python)
Develop an autonomous Python script that:
- Connects to Finnhub to fetch current prices and recent data for XAU/USD and a Top 5 US Stocks list (AAPL, TSLA, MSFT, GOOGL, AMZN).
- Sends market context to Gemini/OpenAI API to get a structured decision (BUY, SELL, HOLD) with a justification.
- Calculates order viability based on Supabase balances and logs the transaction.
- Is structured to process multiple assets simultaneously in a single run.

### R3. Frontend Dashboard (React/Vite)
Create a web dashboard configured for GitHub Pages deployment. It must read from Supabase to display: USD balance, asset portfolio, overall performance, and a table showing trade history with AI justifications.

### R4. Automation (GitHub Actions)
Generate the configuration YAML scripts to run the Python bot via cron jobs.

## Acceptance Criteria

### Automated Bot Verification
- [ ] Python script successfully queries Finnhub and AI API without authentication errors (assuming keys are provided in environment variables).
- [ ] Bot correctly inserts trade records into Supabase and updates the portfolio balance.
- [ ] Bot handles multiple concurrent assets correctly.
- [ ] Bot includes a `--dry-run` or mock mode for local testing without real API credentials.

### Frontend Verification
- [ ] React app successfully builds without errors (`npm run build`).
- [ ] UI components are structured to display data pulled from Supabase.
