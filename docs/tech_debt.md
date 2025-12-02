# Technical Debt & Future Improvements

## High Priority (Week 2-3)
[Will discover today as we work - add items as we go]
## High Priority (Week 2-3)

### 1. Brokerage API Integration ⭐
**Issue:** Share counts manually hardcoded in MY_PORTFOLIO
**Current:** User inputs {"AAPL": 10, "TSLA": 5} in code
**Better:** Auto-sync from brokerage account
**Impact:** HIGH - eliminates manual updates, enables productization
**Effort:** 2-3 hours (varies by broker)
**Complexity:** Medium (OAuth, API keys, rate limits)

**Benefits:**
- Real-time portfolio sync
- Accurate cost basis
- Watchlist integration  
- Multi-portfolio support
- True production feature

**Considerations:**
- Broker API availability (TD, Schwab, Alpaca best)
- Security (OAuth flow, credential storage)
- Rate limits (may need caching)
- Error handling (API downtime)

**Why Not Now:**
- Current manual input works fine for MVP
- Want to validate use case first
- API integration deserves focused attention
- Blog can ship without it (add as "future enhancement")

**Timeline:** Week 2 (Day 7-8)

## Medium Priority (Week 4+)
[Add as we think of them]

## Low Priority (Nice to Have)
[Add as we think of them]

## Not Debt, Just Decisions
- Real-time updates (don't need)
- Mobile app (email works)
- Multi-user (single user)
[Add more as we think of them]
```

---

## ⏰ **Updated Day 6 Timeline:**
```
09:00 - Create 3 skeleton files (5 min) ← NOW
09:05 - Set up Task Scheduler automation (30 min)
09:35 - Document automation in Architecture (10 min)
09:45 - Fill in PRD success metrics (10 min)
09:55 - Create blog outline (30 min)
10:25 - BREAK (10 min)
10:35 - Take screenshots (30 min)
11:05 - Fill in Architecture diagram (15 min)
11:20 - Draft blog intro (30 min)
11:50 - DONE for morning!

AFTERNOON (Optional - 1 hour):
- Polish blog draft
- Fill in remaining doc sections
- Start writing blog content