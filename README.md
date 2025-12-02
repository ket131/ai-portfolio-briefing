# AI Portfolio Briefing System

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)

AI-powered daily portfolio briefing system with intelligent change detection and attribution analysis. Delivers professional email briefings every morning with portfolio insights, market news, and detailed change tracking.

## 🚀 Overview

Automated portfolio intelligence system that combines real-time brokerage data, AI analysis, and smart change detection to deliver actionable investment insights daily.

**Key Capabilities:**
- 📊 **Real-time Portfolio Data** via Plaid API integration
- 🤖 **AI-Powered Analysis** using Claude Sonnet 4
- 📈 **Intelligent Change Detection** with attribution analysis
- 📧 **Professional Email Briefings** delivered daily at 7 AM CT
- ☁️ **Serverless Architecture** on AWS (Lambda, DynamoDB, EventBridge)

**Production Status:** 15+ days uptime, 100% delivery reliability

---

## ✨ Key Features

### 📊 Portfolio Change Detection

Daily snapshot storage and comparison system that tracks every change:

- **Automatic Snapshots:** Stores portfolio state daily in DynamoDB
- **Smart Comparison:** Compares today's portfolio with yesterday's snapshot
- **Position Tracking:** Identifies added, removed, and modified positions
- **Quantity Monitoring:** Detects changes in share counts
- **Price Movement:** Tracks price changes for each holding

**First Run Experience:**
```
📊 First Portfolio Snapshot
This is your first tracked portfolio snapshot.
Starting tomorrow, you'll see changes!
```

**Ongoing Change Detection:**
```
🔄 Portfolio Changes Since Yesterday

Total Change: ▲ $1,245.67 (+2.3%)
├─ Your Actions: +$500.00
└─ Market Moves: +$745.67

➕ Positions Added
AAPL - Apple Inc.
Bought 10.00 shares @ $175.50 = $1,755.00

📊 Positions Modified
GOOGL - Alphabet Inc.
Price up $5.25 (1.2%), Value: $15,234 → $15,867 (+$633)
```

---

### 💰 Smart Attribution Analysis

Advanced algorithm that separates portfolio value changes into two categories:

**User Actions (Buys/Sells):**
- Calculates impact of quantity changes
- Uses previous day's price to isolate user decisions
- Formula: `(today_qty - yesterday_qty) * yesterday_price`

**Market Movements (Price Changes):**
- Calculates impact of market fluctuations
- Uses yesterday's quantity to isolate market impact
- Formula: `(today_price - yesterday_price) * yesterday_qty`

**Example Attribution:**
```
Portfolio increased by $1,000:
├─ You bought 5 shares of AAPL @ $150 = +$750 (user action)
└─ AAPL price rose from $150 to $165 = +$250 (market move)
```

This clear separation helps you understand:
- What impact YOUR trading decisions had
- What impact THE MARKET had on your holdings
- How much value came from your actions vs market performance

---

### 🤖 AI-Powered Insights

Claude Sonnet 4 analyzes your portfolio and provides:

- **Portfolio Composition Analysis:** Sector allocation, diversification assessment
- **News Sentiment Evaluation:** Impact analysis of recent news on your holdings
- **Risk Assessment:** Concentration risk, sector exposure warnings
- **Actionable Recommendations:** Specific suggestions based on your portfolio
- **Market Context:** How broader market trends affect your positions

**AI Analysis Example:**
```
Your portfolio shows strong tech concentration (65%), with AAPL and GOOGL 
as largest positions. Recent tech sector news is mixed - while AAPL's new 
product launch is positive, regulatory concerns around big tech create 
headwinds. Consider rebalancing to reduce concentration risk.
```

---

### 📧 Professional Email Briefings

Clean, responsive HTML emails delivered daily:

**Email Sections:**
1. **Portfolio Summary**
   - Total value and account count
   - Holdings table with current prices
   - Overall portfolio performance

2. **Change Detection** (if changes detected)
   - Total change with user/market attribution
   - New positions added
   - Positions removed
   - Positions modified with details

3. **AI Insights**
   - Claude's analysis and recommendations
   - Contextualized to your specific holdings

4. **Market News**
   - Recent news about your holdings
   - Sentiment analysis for each article
   - Direct links to full articles

**Delivery:** 7:00 AM CT daily via SendGrid

---

## 🏗️ Architecture

### System Design

```
┌─────────────────┐
│  EventBridge    │ Triggers daily at 7 AM CT
│  (Scheduler)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AWS Lambda     │ Python 3.11, Serverless execution
│  (portfolio-    │ 
│   worker)       │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│   DynamoDB      │  │  Secrets Mgr    │
│                 │  │                 │
│ • portfolio-    │  │ • Plaid creds   │
│   users         │  │ • API keys      │
│ • portfolio-    │  │ • SendGrid key  │
│   broker-creds  │  │                 │
│ • portfolio-    │  └─────────────────┘
│   history       │
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         External API Integrations            │
├─────────────────────────────────────────────┤
│ • Plaid API (portfolio data)                │
│ • Anthropic Claude API (AI analysis)        │
│ • Alpha Vantage API (market news)           │
│ • SendGrid API (email delivery)             │
└─────────────────────────────────────────────┘
```

### Data Flow

1. **Trigger:** EventBridge fires at 7:00 AM CT daily
2. **User Lookup:** Lambda queries DynamoDB for active users
3. **Portfolio Fetch:** Retrieves current holdings via Plaid API
4. **Change Detection:**
   - Queries DynamoDB for yesterday's snapshot
   - Compares today vs yesterday
   - Calculates attribution (user actions vs market moves)
5. **Snapshot Storage:** Stores today's portfolio in DynamoDB
6. **News Retrieval:** Fetches recent news for holdings via Alpha Vantage
7. **AI Analysis:** Sends portfolio + news to Claude for insights
8. **Email Generation:** Formats HTML email with all sections
9. **Delivery:** Sends email via SendGrid API

### AWS Infrastructure

**Compute:**
- AWS Lambda (Python 3.11)
- Memory: 512 MB
- Timeout: 15 minutes
- Concurrent executions: 1 (daily trigger)

**Storage:**
- Amazon DynamoDB (3 tables)
- On-demand billing
- Point-in-time recovery enabled

**Orchestration:**
- Amazon EventBridge
- Cron: `cron(0 13 * * ? *)` (7 AM CT = 13:00 UTC)

**Security:**
- AWS Secrets Manager (credential storage)
- IAM roles with least privilege
- VPC not required (public API calls)

---

## 📁 Project Structure

```
ai-portfolio-briefing/
├── lambda/
│   ├── lambda_function.py      # Main Lambda handler (975+ lines)
│   └── requirements.txt         # Python dependencies
├── docs/
│   ├── architecture.md          # Detailed system architecture
│   ├── prd.md                   # Product requirements document
│   ├── backlog.md              # Feature backlog and roadmap
│   ├── blog_post.md            # Technical blog post draft
│   └── tech_debt.md            # Known issues and improvements
├── screenshots/                 # System screenshots (TBD)
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                  # Git ignore rules
```

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.11
- AWS Lambda (serverless compute)
- boto3 (AWS SDK for Python)

**Data Storage:**
- Amazon DynamoDB (NoSQL database)
- Composite keys: `userId` (partition) + `date` (sort key)
- On-demand capacity mode

**AI/ML:**
- Anthropic Claude Sonnet 4 (primary AI)
- Prompt engineering for portfolio analysis
- Structured output parsing

**External APIs:**
- **Plaid** (brokerage integration) - Production access
- **Alpha Vantage** (financial news) - Premium tier
- **SendGrid** (email delivery) - Free tier
- **Anthropic** (AI analysis) - API access

**AWS Services:**
- Lambda (compute)
- DynamoDB (storage)
- EventBridge (scheduling)
- Secrets Manager (credentials)
- CloudWatch (monitoring & logs)

---

## 🚀 Deployment

### Prerequisites

**AWS Account:**
- Lambda execution permissions
- DynamoDB table creation
- Secrets Manager access
- EventBridge rule creation

**API Credentials:**
- Plaid API (Production environment)
- Anthropic API key
- SendGrid API key
- Alpha Vantage API key (optional for news)

### Step 1: Create DynamoDB Tables

**portfolio-users** table:
```
Partition key: userId (String)
Attributes: email, created_at, active
```

**portfolio-broker-creds** table:
```
Partition key: userId (String)
Attributes: access_token, item_id, broker, created_at
```

**portfolio-history** table:
```
Partition key: userId (String)
Sort key: date (String, format: YYYY-MM-DD)
Attributes: holdings (List), total_value (Number), account_count (Number), timestamp
```

### Step 2: Configure AWS Secrets Manager

Store these secrets:
```
portfolio-system/plaid/client_id
portfolio-system/plaid/secret
portfolio-system/anthropic/api_key
portfolio-system/sendgrid/api_key
portfolio-system/alphavantage/api_key
```

### Step 3: Deploy Lambda Function

1. **Create Lambda function:**
   - Runtime: Python 3.11
   - Architecture: x86_64
   - Memory: 512 MB
   - Timeout: 15 minutes

2. **Upload code:**
   ```bash
   cd lambda
   zip -r function.zip lambda_function.py
   aws lambda update-function-code --function-name portfolio-worker --zip-file fileb://function.zip
   ```

3. **Install dependencies as Lambda Layer:**
   ```bash
   pip install -r requirements.txt -t python/
   zip -r layer.zip python/
   aws lambda publish-layer-version --layer-name portfolio-deps --zip-file fileb://layer.zip
   ```

4. **Configure environment variables:**
   ```
   ENVIRONMENT=production
   REGION=us-east-1
   ```

5. **Set IAM role permissions:**
   - DynamoDB: Query, GetItem, PutItem, Scan
   - Secrets Manager: GetSecretValue
   - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents

### Step 4: Setup EventBridge Trigger

Create EventBridge rule:
```
Name: portfolio-daily-trigger
Schedule expression: cron(0 13 * * ? *)
Target: portfolio-worker Lambda function
```

**Note:** `cron(0 13 * * ? *)` = 7:00 AM Central Time (13:00 UTC)

### Step 5: Test Deployment

**Manual test:**
```bash
aws lambda invoke --function-name portfolio-worker response.json
```

**Check logs:**
```bash
aws logs tail /aws/lambda/portfolio-worker --follow
```

**Expected output:**
```
Portfolio worker started at 2025-12-02 13:00:00
Found 1 active user(s)
Fetching portfolio data for user@example.com
Portfolio fetched: 29 holdings, $XXX,XXX.XX total value
Fetching yesterday's portfolio for change detection
✅ Changes detected: +$1,234.56 total change
✅ Portfolio snapshot stored for user-xxx on 2025-12-02
✅ Email sent successfully via SendGrid to user@example.com
```

---

## 📊 Change Detection Algorithm

### Storage Schema

Each daily snapshot in DynamoDB:
```python
{
    'userId': 'user-12345',
    'date': '2025-12-02',
    'holdings': [
        {
            'ticker': 'AAPL',
            'name': 'Apple Inc.',
            'quantity': 10.0,
            'price': 175.50,
            'value': 1755.00
        },
        # ... more holdings
    ],
    'total_value': 53151.72,
    'account_count': 2,
    'timestamp': '2025-12-02T13:00:00Z'
}
```

### Comparison Logic

**Step 1: Fetch both snapshots**
```python
today_portfolio = fetch_current_portfolio()  # From Plaid
yesterday_portfolio = get_previous_portfolio(user_id, days_ago=1)  # From DynamoDB
```

**Step 2: Create lookup dictionaries**
```python
today_positions = {holding['ticker']: holding for holding in today_portfolio['holdings']}
yesterday_positions = {holding['ticker']: holding for holding in yesterday_portfolio['holdings']}
```

**Step 3: Identify changes**
```python
added_tickers = set(today_positions.keys()) - set(yesterday_positions.keys())
removed_tickers = set(yesterday_positions.keys()) - set(today_positions.keys())
common_tickers = set(today_positions.keys()) & set(yesterday_positions.keys())
```

**Step 4: Calculate attribution**

For each common ticker:
```python
# User action: quantity change valued at yesterday's price
user_action = (today_qty - yesterday_qty) * yesterday_price

# Market move: price change valued at yesterday's quantity  
market_move = (today_price - yesterday_price) * yesterday_qty

# Total change for this position
total_change = user_action + market_move
```

**Step 5: Aggregate results**
```python
total_user_actions = sum(all user_action values) + added_value - removed_value
total_market_moves = sum(all market_move values)
total_change = total_user_actions + total_market_moves
```

### Edge Cases Handled

- **First run:** No previous snapshot → Show "First Portfolio Snapshot" message
- **No changes:** No adds/removes/modifications → Show "No changes detected"
- **New positions:** Entire value attributed to user actions
- **Removed positions:** Entire value attributed to user actions (negative)
- **Fractional shares:** Full decimal precision maintained
- **Multiple accounts:** Aggregates across all connected accounts

---

## 💡 Future Enhancements

**Phase 2 (Planned):**
- [ ] User-configurable delivery time and timezone preferences
- [ ] Weekly and monthly comparison views
- [ ] Historical performance charting
- [ ] Cost basis tracking (if available via Plaid)
- [ ] Sector allocation analysis over time
- [ ] Performance attribution dashboard

**Phase 3 (Roadmap):**
- [ ] Smart alerts for significant changes (>5% moves)
- [ ] Interactive web dashboard (React frontend)
- [ ] Mobile app with push notifications
- [ ] Multi-user support with family accounts
- [ ] Integration with tax preparation tools

**Phase 4 (Vision):**
- [ ] Multi-agent system with LangGraph
- [ ] Predictive analysis using historical patterns
- [ ] Automated rebalancing suggestions
- [ ] Integration with robo-advisors
- [ ] Social features (portfolio comparison, leaderboards)

See `docs/backlog.md` for detailed feature specifications.

---

## 📈 Production Metrics

**Reliability:**
- 15+ consecutive days uptime
- 100% successful daily briefings
- 0 failed email deliveries
- Average execution time: 45 seconds

**Performance:**
- Cold start: ~2 seconds
- Warm execution: ~30-45 seconds
- DynamoDB latency: <10ms
- Email delivery: <5 seconds

**Cost (Monthly):**
- Lambda: ~$0.01 (15 invocations @ 512MB)
- DynamoDB: ~$0.05 (30 writes, 30 reads)
- Secrets Manager: ~$0.40 (1 secret)
- Data transfer: ~$0.01
- **Total: ~$0.47/month** (excludes API costs)

**API Costs (Monthly):**
- Plaid: $0 (free tier for personal use)
- Anthropic Claude: ~$2-3 (30 requests @ ~1000 tokens each)
- SendGrid: $0 (free tier, <100 emails/day)
- Alpha Vantage: $0 (free tier, <500 requests/day)
- **Total API: ~$2-3/month**

**Grand Total: ~$3/month for fully automated portfolio intelligence**

---

## 🔒 Security & Privacy

**Data Protection:**
- All credentials stored in AWS Secrets Manager
- No API keys in code or environment variables
- Plaid access tokens encrypted at rest
- DynamoDB encryption enabled

**Access Control:**
- IAM roles with least privilege principle
- No public endpoints (Lambda behind EventBridge)
- CloudWatch logs do not contain sensitive data

**Privacy:**
- Portfolio data never leaves AWS (except for API calls)
- Email delivery via secure HTTPS
- No third-party analytics or tracking

**Compliance:**
- Follows Plaid security best practices
- SOC 2 compliant infrastructure (AWS)
- GDPR-ready (data deletion supported)

---

## 🤝 Contributing

This is a personal portfolio project demonstrating production-quality code and system design. Feel free to fork and adapt for your own use!

**If you'd like to collaborate:**
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request with detailed description

**Areas where contributions are welcome:**
- Additional brokerage integrations (beyond Plaid)
- Alternative email providers (beyond SendGrid)
- Frontend dashboard development
- Mobile app development
- Additional analysis algorithms

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

**Summary:** You are free to use, modify, and distribute this code for personal or commercial use, with attribution.

---

## 👤 Author

**Ketan Patel** - Product Manager with 15+ years experience building AI-powered systems, e-commerce platforms, and consumer technology products.

**Background:**
- Director of Product Management (Mobile Internet Startup)
- Chief Product Owner, Nokia Xpress browser (Nokia, 5 scrum teams)
- Product Manager (BMW, 7 years)
- CTO (GetBetty, 3 years)
- Product Manager (Amazon, 3+ years - GenAI)

**Skills Demonstrated in This Project:**
- ✅ Serverless architecture design (AWS Lambda, DynamoDB, EventBridge)
- ✅ Multi-API integration (Plaid, Claude, SendGrid, Alpha Vantage)
- ✅ Production system deployment and monitoring
- ✅ AI/LLM implementation and prompt engineering
- ✅ Data modeling and algorithm design
- ✅ User-centric product thinking
- ✅ Full-stack development (backend focus)
- ✅ Technical writing and documentation

**Currently:** Seeking AI Product Manager roles at innovative companies building the future of AI-powered products.

---

## 🔗 Links

- **GitHub Repository:** https://github.com/ket131/ai-portfolio-briefing
- **LinkedIn:** https://www.linkedin.com/in/ketanpatel131
- **Portfolio:** [AI Portfolio Dashboard (Beta)](https://your-lovable-link.com)
- **Blog Post:** See `docs/blog_post.md` for detailed technical write-up

---

## 📧 Contact

**For questions, collaboration, or job opportunities:**
- Email: kbp131@gmail.com
- LinkedIn: https://www.linkedin.com/in/ketanpatel131
- GitHub: [@ket131](https://github.com/ket131)

---

## 🙏 Acknowledgments

**APIs & Services:**
- Plaid for excellent brokerage data API
- Anthropic for Claude AI API
- SendGrid for reliable email delivery
- Alpha Vantage for financial news data

**Inspiration:**
- Personal need for automated portfolio intelligence
- Desire to apply GenAI to real-world financial use cases
- Portfolio project to demonstrate production-quality PM + technical skills

---

**⭐ If you found this project interesting or useful, please give it a star!**

Built with ❤️ and ☕ by Ketan Patel, November 2025