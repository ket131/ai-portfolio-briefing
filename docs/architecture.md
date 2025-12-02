# System Architecture & Design Decisions

## High-Level Architecture
[Fill in diagram this afternoon - 15 min]

## Technology Stack
**Core:**
- LangGraph: Multi-agent orchestration
- Python 3.12

**Data Sources:**
- Yahoo Finance: Prices & News

**AI:**
- Claude Sonnet 4: $0.02/run

**Delivery:**
- Gmail SMTP
- [Add automation details after setup - 5 min]

## Key Design Decisions

### 1. Why LangGraph?
[Copy from my template above - 5 min]

### 2. Yahoo Finance vs Alpha Vantage
[Copy from my template above - 5 min]

### 3. Windows Task Scheduler vs Cloud
[Fill in after automation - 10 min]

### 4. Email vs Web Dashboard
[Copy from my template above - 5 min]

### 5. Logging Early
[Fill in from Day 5 reflections - 5 min]

### 6. Manual Portfolio Input vs Brokerage API

**Decision (MVP):** Manual share count input in code

**Alternative:** Sync from brokerage API (Schwab, TD, Alpaca, etc.)

**Why Manual for MVP:**
- ✅ Zero dependencies (no API setup)
- ✅ Fast implementation (5 minutes)
- ✅ Works immediately
- ✅ No rate limits or auth complexity
- ✅ Privacy (no broker credentials needed)

**Why Brokerage API for Production:**
- ✅ Real-time sync (no manual updates)
- ✅ Accurate cost basis
- ✅ Watchlist integration
- ✅ Multi-portfolio support
- ✅ Professional feature

**Timeline:**
- Week 1: Manual input (MVP) ✅
- Week 2: Broker API integration (if broker supports)

**Trade-off:** Speed to MVP vs automation
**Result:** Ship fast, enhance later
**Next:** Research broker API (Week 2)

## Performance Characteristics
**Current:**
- Execution: 24-26s
- Data: 8s (33%)
- News: 1.5s (6%)
- Analysis: 15s (61%)
- Cost: $0.017/run

## Deployment & Automation

### Automated Daily Execution

**Method:** Windows Task Scheduler
**Schedule:** Every weekday at 7:00 AM CT
**Execution:** ~26 seconds per run
**Reliability:** Wake computer if sleeping

### Implementation

**Batch Script:** `run_portfolio_analyzer.bat`
```batch
- Activates Python virtual environment
- Runs portfolio_agent_system.py
- Sends email via Gmail SMTP
- Deactivates venv
- Logs execution
```

**Task Scheduler Configuration:**
- **Name:** AI Portfolio Analyzer - Daily Briefing
- **Trigger:** Daily, 7:00 AM, weekdays only
- **Action:** Execute batch script
- **Conditions:** 
  - Wake computer to run
  - Run on AC or battery power
  - Retry 3 times if fails (1 min intervals)
- **Security:** Run whether user logged on or not

### Why Windows Task Scheduler?

**Decision:** Local scheduling vs cloud (AWS Lambda, Heroku Scheduler)

**Why Task Scheduler:**
- ✅ Free (no cloud costs)
- ✅ Simple (no deployment complexity)
- ✅ Reliable (Windows built-in)
- ✅ Privacy (data stays local)
- ✅ Fast setup (30 minutes)

**Trade-offs:**
- ⚠️ Requires computer on/awake at 7 AM
- ⚠️ Single point of failure (if computer off)
- ⚠️ Not scalable to multiple users

**Result:** Perfect for personal use case, cloud later if needed

### Monitoring

**Success indicators:**
- Email received daily at ~7:02 AM
- Last Run Result: 0x0 (success)
- execution_log.csv updated daily
- No error emails

**If task fails:**
- Automatic retry (3 attempts, 1 min apart)
- Check Task Scheduler History tab
- Review batch script output
- Verify .env credentials

### Cost Analysis

**Daily:** $0.02 per run
**Monthly:** $0.60 (30 runs)
**Yearly:** $7.30 (365 runs)

**Infrastructure:** $0 (local execution)
**Total:** <$8/year for daily AI portfolio analysis!