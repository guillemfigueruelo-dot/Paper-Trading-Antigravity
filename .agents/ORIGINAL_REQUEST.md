# Original User Request

## Initial Request — 2026-06-10T16:36:21Z

# Teamwork Project Prompt — Draft

> Status: Launched (Phase 2 - Bugfixes & Polish)
> Goal: Fix current errors, verify deployment, and ensure complete stability

Automated paper trading system consisting of a React/Vite dashboard, a Python trading bot executed via GitHub Actions, integrating Finnhub for market data, Google AI Studio for trade decisions, and Supabase for state management. 

Working directory: c:/Users/Figue/Desktop/Paper Trading Antigravity
Integrity mode: development

## Requirements

### R1. Database Schema (Supabase)
Ensure the SQL schema and integration for two tables: `portfolio` and `trades` are completely robust and working.

### R2. Trading Bot (Python)
Refine the autonomous Python script that:
- Connects to Finnhub to fetch current prices and recent data for XAU/USD and a Top 5 US Stocks list (AAPL, TSLA, MSFT, GOOGL, AMZN).
- Sends market context to Gemini/OpenAI API to get a structured decision (BUY, SELL, HOLD) with a justification.
- Calculates order viability based on Supabase balances and logs the transaction.
- Is structured to process multiple assets simultaneously in a single run.

### R3. Frontend Dashboard (React/Vite)
Refine the web dashboard configured for GitHub Pages deployment. Ensure it reads from Supabase to display: USD balance, asset portfolio, overall performance, and a table showing trade history.

### R4. Automation (GitHub Actions)
Ensure the configuration YAML scripts to run the Python bot via cron jobs and deploy the dashboard are correct.

### R5. FIX DEPLOYMENT (404 ERROR)
The GitHub Pages deployment is currently returning a 404 error on `https://guillemfigueruelo-dot.github.io/Paper-Trading-Antigravity/`.
- Fix the `vite.config.ts` so `base` is correctly set to `'/Paper-Trading-Antigravity/'`.
- Ensure the GitHub Actions deployment workflow is correctly building and uploading the `dist` folder.
- Ensure any routing (if used) supports GitHub pages.

## Acceptance Criteria

### Automated Bot Verification
- [ ] Python script successfully queries Finnhub and AI API without authentication errors.
- [ ] Bot correctly inserts trade records into Supabase and updates the portfolio balance.
- [ ] Bot handles multiple concurrent assets correctly.

### Frontend Verification
- [ ] React app successfully builds without errors (`npm run build`).
- [ ] UI components are structured to display data pulled from Supabase.
- [ ] The Vite configuration `base` path matches the GitHub Pages repository name to avoid 404 errors.
