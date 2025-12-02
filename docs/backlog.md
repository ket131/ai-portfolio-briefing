# AI Portfolio Analyzer - Product Backlog

## Current Status
- MVP: ✅ Complete (3-agent news-enhanced system)
- Observability: ✅ Complete (logging, metrics, CSV)
- Use Case: Email briefing (24s execution acceptable)

---

## P0 - Must Have (Week 2)
**Ship these before moving to optimization:**

1. [ ] Email Integration
   - Send analysis via email
   - Schedule daily runs
   - Est: 2-3 hours

2. [ ] Better Output Formatting
   - Cleaner markdown
   - Mobile-friendly
   - Est: 1-2 hours

3. [ ] Documentation
   - README.md
   - Setup instructions
   - Blog post draft
   - Est: 2-3 hours

---

## P1 - Should Have (Week 3)
**Add if time permits:**

1. [ ] Portfolio Value Tracking
   - Calculate total portfolio value
   - Track daily changes
   - Historical value chart
   - Est: 2-3 hours

2. [ ] Risk Metrics
   - Portfolio beta
   - Volatility score
   - Sector concentration
   - Est: 3-4 hours

3. [ ] Export Options
   - PDF export
   - CSV export
   - Email attachment
   - Est: 2-3 hours

---

## P2 - Nice to Have (Week 4+)
**Future enhancements:**

1. [ ] Historical Tracking
   - Store daily results
   - Performance over time
   - Trend analysis
   - Est: 4-5 hours

2. [ ] Multiple Portfolios
   - Support different portfolios
   - Compare performance
   - Est: 3-4 hours

3. [ ] Alerts & Notifications
   - Price alerts
   - News alerts
   - Threshold notifications
   - Est: 3-4 hours

---

## P3 - Performance Optimization
**ONLY if use case changes (web app, real-time):**

### When to Optimize:
- Moving to web interface (user waiting)
- Real-time dashboard requirement
- >100 stocks in portfolio (scale issue)
- Multiple users (load issue)

### Optimization Targets:
1. [ ] Async Parallel Data Fetching
   - Current: 7.7s sequential
   - Target: 2-3s parallel
   - Savings: ~5s (20% faster)
   - Effort: 2-3 hours
   - ROI: High IF users are waiting

2. [ ] Streaming Claude Response
   - Current: Wait 15s, then see results
   - Target: Start seeing results at 2s
   - Perceived speed: 3x faster
   - Effort: 1-2 hours
   - ROI: High for web UI

3. [ ] Caching Strategy
   - Cache prices for 5 min
   - Cache news for 30 min
   - Savings: Near-instant repeat runs
   - Effort: 2-3 hours
   - ROI: Medium (only helps repeated runs)

4. [ ] Prompt Optimization
   - Reduce token count
   - Faster Claude processing
   - Savings: 2-3s
   - Effort: 2-3 hours
   - ROI: Low (small gain, risks quality)

### Decision Criteria:
- Email use case: Don't optimize (24s is fine!)
- Web dashboard: Do #1 and #2 (high ROI)
- Chat interface: Do all of them (required)

---

## Icebox - Maybe Never
**Ideas to track but probably won't build:**

- Machine learning predictions
- Options trading analysis
- Cryptocurrency support
- Mobile app
- Social features

---

## Decision Log

### 2025-11-04: Performance Optimization Deprioritized
**Context:** Collected performance data (24s avg execution)
**Decision:** Don't optimize yet - 24s is acceptable for email use case
**Reasoning:** 
- User not actively waiting (batch/email)
- 2-3 hours optimization effort better spent on features
- Will revisit if building web interface
**Trade-off:** Speed vs feature completeness (chose features)
**Result:** Ship features faster, validate use case, optimize later if needed

---

## Metrics to Track
- Execution time (target: <30s for email, <10s for web)
- Cost per run (target: <$0.05)
- User satisfaction (collect feedback)
- Feature usage (what gets used?)
