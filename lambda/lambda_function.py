"""
AWS Lambda Function: portfolio-worker
Purpose: Generate and send daily AI-powered portfolio briefings
Triggers: EventBridge (7 AM CT daily)
Process: Fetch portfolio → Get news → AI analysis → Send email
# Version: 1.0.0
# Last Updated: 2024-11-10
# Uses Plaid for data fetching, sends daily briefings via SES
# CI/CD Test v2 - Deployed automatically via GitHub Actions on Dec 4, 2025
# Langfuse observability integration - Dec 11, 2025
"""
import json
import boto3
import requests
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from langfuse import Langfuse  # ← ADD THIS LINE

# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Email, To, Content
# import weave  # ← removed on 12/2/2025 due to incomplete integration - package size limit hit

# Initialize Langfuse observability
langfuse = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host="https://cloud.langfuse.com"
)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ses_client = boto3.client('ses', region_name='us-east-1')

# DynamoDB tables
users_table = dynamodb.Table('portfolio-users')
creds_table = dynamodb.Table('portfolio-broker-creds')
history_table = dynamodb.Table('portfolio-history')  # ← ADD THIS
insights_history_table = dynamodb.Table('portfolio-insights-history')  # ← ADD THIS (for future)

# ===== PORTFOLIO CHANGE DETECTION FUNCTIONS =====
# (Added Dec 1, 2025 - Change tracking feature)

def store_portfolio_snapshot(user_id: str, portfolio_data: dict) -> bool:
    """Store today's portfolio snapshot in DynamoDB"""
    try:
        # history_table = dynamodb.Table('portfolio-history') ADDED new tables above 
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Convert float values to Decimal for DynamoDB
        holdings_for_dynamo = []
        for holding in portfolio_data['holdings']:
            holdings_for_dynamo.append({
                'ticker': holding['ticker'],
                'name': holding['name'],
                'quantity': Decimal(str(holding['quantity'])),
                'price': Decimal(str(holding['price'])),
                'value': Decimal(str(holding['value']))
            })
        
        # Store snapshot
        history_table.put_item(
            Item={
                'userId': user_id,
                'date': today,
                'holdings': holdings_for_dynamo,
                'total_value': Decimal(str(portfolio_data['total_value'])),
                'account_count': portfolio_data['account_count'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        print(f"✅ Portfolio snapshot stored for {user_id} on {today}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing portfolio snapshot: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_previous_portfolio(user_id: str, days_ago: int = 1):
    """Retrieve portfolio from N days ago"""
    try:
        # history_table = dynamodb.Table('portfolio-history') - ADDED under dynamoDB tables above
        target_date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        response = history_table.get_item(
            Key={
                'userId': user_id,
                'date': target_date
            }
        )
        
        item = response.get('Item')
        
        if not item:
            print(f"ℹ️ No portfolio snapshot found for {user_id} on {target_date}")
            return None
        
        # Convert Decimal back to float
        holdings_converted = []
        for holding in item['holdings']:
            holdings_converted.append({
                'ticker': holding['ticker'],
                'name': holding['name'],
                'quantity': float(holding['quantity']),
                'price': float(holding['price']),
                'value': float(holding['value'])
            })
        
        return {
            'holdings': holdings_converted,
            'total_value': float(item['total_value']),
            'account_count': item['account_count'],
            'date': item['date']
        }
        
    except Exception as e:
        print(f"❌ Error retrieving previous portfolio: {str(e)}")
        return None


def detect_portfolio_changes(today_portfolio: dict, yesterday_portfolio) -> dict:
    """Compare today's portfolio with yesterday's and detect changes"""
    
    # If no yesterday data, this is first run
    if not yesterday_portfolio:
        return {
            'has_changes': False,
            'is_first_run': True,
            'positions_added': [],
            'positions_removed': [],
            'positions_changed': [],
            'total_value_change': 0,
            'attribution': {'user_actions': 0, 'market_movements': 0}
        }
    
    # Create lookup dictionaries
    today_dict = {h['ticker']: h for h in today_portfolio['holdings']}
    yesterday_dict = {h['ticker']: h for h in yesterday_portfolio['holdings']}
    
    today_tickers = set(today_dict.keys())
    yesterday_tickers = set(yesterday_dict.keys())
    
    # Detect changes
    added_tickers = today_tickers - yesterday_tickers
    removed_tickers = yesterday_tickers - today_tickers
    common_tickers = today_tickers & yesterday_tickers
    
    positions_added = []
    positions_removed = []
    positions_changed = []
    
    user_action_value = 0
    market_movement_value = 0
    
    # Process added positions
    for ticker in added_tickers:
        holding = today_dict[ticker]
        positions_added.append({
            'ticker': ticker,
            'name': holding['name'],
            'quantity': holding['quantity'],
            'price': holding['price'],
            'value': holding['value']
        })
        user_action_value += holding['value']
    
    # Process removed positions
    for ticker in removed_tickers:
        holding = yesterday_dict[ticker]
        positions_removed.append({
            'ticker': ticker,
            'name': holding['name'],
            'quantity': holding['quantity'],
            'price': holding['price'],
            'value': holding['value']
        })
        user_action_value -= holding['value']
    
    # Process common positions
    for ticker in common_tickers:
        today_h = today_dict[ticker]
        yesterday_h = yesterday_dict[ticker]
        
        quantity_diff = today_h['quantity'] - yesterday_h['quantity']
        price_diff = today_h['price'] - yesterday_h['price']
        
        if abs(quantity_diff) > 0.001 or abs(price_diff) > 0.01:
            # User action: quantity change at yesterday's price
            if abs(quantity_diff) > 0.001:
                user_action_value += quantity_diff * yesterday_h['price']
            
            # Market movement: price change on yesterday's quantity
            if abs(price_diff) > 0.01:
                market_movement_value += price_diff * yesterday_h['quantity']
            
            positions_changed.append({
                'ticker': ticker,
                'name': today_h['name'],
                'yesterday': yesterday_h,
                'today': today_h,
                'quantity_diff': quantity_diff,
                'price_diff': price_diff,
                'value_diff': today_h['value'] - yesterday_h['value']
            })
    
    total_change = today_portfolio['total_value'] - yesterday_portfolio['total_value']
    total_change_pct = (total_change / yesterday_portfolio['total_value'] * 100) if yesterday_portfolio['total_value'] > 0 else 0
    
    return {
        'has_changes': bool(positions_added or positions_removed or positions_changed),
        'is_first_run': False,
        'positions_added': positions_added,
        'positions_removed': positions_removed,
        'positions_changed': positions_changed,
        'total_value_change': total_change,
        'total_value_change_pct': total_change_pct,
        'attribution': {
            'user_actions': user_action_value,
            'market_movements': market_movement_value
        },
        'summary': {
            'added_count': len(positions_added),
            'removed_count': len(positions_removed),
            'changed_count': len(positions_changed)
        }
    }


def format_changes_html(changes: dict) -> str:
    """Format portfolio changes as HTML for email"""
    
    if changes['is_first_run']:
        return """
        <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p style="margin: 0; color: #1e40af;">
                <strong>📊 First Portfolio Snapshot</strong><br>
                This is your first tracked portfolio snapshot. Starting tomorrow, you'll see changes!
            </p>
        </div>
        """
    
    if not changes['has_changes']:
        return """
        <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p style="margin: 0; color: #166534;">
                <strong>✅ No Portfolio Changes</strong><br>
                All positions unchanged from yesterday.
            </p>
        </div>
        """
    
    # Build changes HTML
    html = '<div style="margin: 30px 0;">'
    html += '<h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">🔄 Portfolio Changes Since Yesterday</h2>'
    
    # Summary box
    total_change = changes['total_value_change']
    change_pct = changes['total_value_change_pct']
    user_actions = changes['attribution']['user_actions']
    market_moves = changes['attribution']['market_movements']
    
    change_color = '#22c55e' if total_change >= 0 else '#ef4444'
    change_symbol = '▲' if total_change >= 0 else '▼'
    
    html += f"""
    <div style="background: #f9fafb; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
        <div style="margin-bottom: 15px;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">Total Change</p>
            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: {change_color};">
                {change_symbol} ${abs(total_change):,.2f} ({change_pct:+.2f}%)
            </p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <p style="margin: 0; color: #6b7280; font-size: 13px;">Your Actions</p>
                <p style="margin: 5px 0 0 0; font-size: 18px; color: #1f2937;">${user_actions:+,.2f}</p>
            </div>
            <div>
                <p style="margin: 0; color: #6b7280; font-size: 13px;">Market Moves</p>
                <p style="margin: 5px 0 0 0; font-size: 18px; color: #1f2937;">${market_moves:+,.2f}</p>
            </div>
        </div>
    </div>
    """
    
    # Positions added
    if changes['positions_added']:
        html += '<div style="margin-bottom: 20px;"><h3 style="color: #059669; margin-bottom: 10px;">➕ Positions Added</h3>'
        for pos in changes['positions_added']:
            html += f"""
            <div style="background: #f0fdf4; border-left: 3px solid #22c55e; padding: 10px; margin-bottom: 10px; border-radius: 3px;">
                <strong>{pos['ticker']}</strong> - {pos['name']}<br>
                <span style="color: #6b7280; font-size: 14px;">
                    Bought {pos['quantity']:.2f} shares @ ${pos['price']:.2f} = ${pos['value']:,.2f}
                </span>
            </div>
            """
        html += '</div>'
    
    # Positions removed
    if changes['positions_removed']:
        html += '<div style="margin-bottom: 20px;"><h3 style="color: #dc2626; margin-bottom: 10px;">➖ Positions Removed</h3>'
        for pos in changes['positions_removed']:
            html += f"""
            <div style="background: #fef2f2; border-left: 3px solid #ef4444; padding: 10px; margin-bottom: 10px; border-radius: 3px;">
                <strong>{pos['ticker']}</strong> - {pos['name']}<br>
                <span style="color: #6b7280; font-size: 14px;">
                    Sold {pos['quantity']:.2f} shares @ ${pos['price']:.2f} = ${pos['value']:,.2f}
                </span>
            </div>
            """
        html += '</div>'
    
    # Positions changed (show top 5)
    if changes['positions_changed']:
        html += '<div style="margin-bottom: 20px;"><h3 style="color: #2563eb; margin-bottom: 10px;">📊 Positions Modified</h3>'
        for pos in changes['positions_changed'][:5]:
            change_parts = []
            if abs(pos['quantity_diff']) > 0.001:
                action = "bought" if pos['quantity_diff'] > 0 else "sold"
                change_parts.append(f"{action} {abs(pos['quantity_diff']):.2f} shares")
            if abs(pos['price_diff']) > 0.01:
                direction = "up" if pos['price_diff'] > 0 else "down"
                pct = abs(pos['price_diff'] / pos['yesterday']['price'] * 100) if pos['yesterday']['price'] > 0 else 0
                change_parts.append(f"price {direction} ${abs(pos['price_diff']):.2f} ({pct:.1f}%)")
            
            html += f"""
            <div style="background: #eff6ff; border-left: 3px solid #3b82f6; padding: 10px; margin-bottom: 10px; border-radius: 3px;">
                <strong>{pos['ticker']}</strong> - {pos['name']}<br>
                <span style="color: #6b7280; font-size: 14px;">
                    {", ".join(change_parts)}<br>
                    Value: ${pos['yesterday']['value']:,.2f} → ${pos['today']['value']:,.2f} ({pos['value_diff']:+,.2f})
                </span>
            </div>
            """
        
        if len(changes['positions_changed']) > 5:
            html += f'<p style="color: #6b7280; font-size: 13px;">+ {len(changes["positions_changed"]) - 5} more modified</p>'
        
        html += '</div>'
    
    html += '</div>'
    return html

# ===== END CHANGE DETECTION FUNCTIONS =====

def get_secrets():
    """Retrieve API credentials from AWS Secrets Manager"""
    try:
        # Plaid credentials
        plaid_response = secrets_client.get_secret_value(
            SecretId='plaid-production-credentials'
        )
        plaid_secrets = json.loads(plaid_response['SecretString'])
        
        # Alpha Vantage API key (you'll need to add this to Secrets Manager)
        # For now, we'll use environment variable
        alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
        
        # Claude API key (you'll need to add this to Secrets Manager)
        claude_api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        return {
            'plaid_client_id': plaid_secrets['PLAID_CLIENT_ID'],
            'plaid_secret': plaid_secrets['PLAID_SECRET'],
            'alpha_vantage_key': alpha_vantage_key,
            'claude_api_key': claude_api_key
        }
    except Exception as e:
        print(f"Error retrieving secrets: {str(e)}")
        raise

def get_active_users():
    """Fetch all active users from DynamoDB"""
    try:
        response = users_table.scan(
            FilterExpression='isActive = :active',
            ExpressionAttributeValues={':active': True}
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        raise

def get_user_credentials(user_id):
    """Fetch user's Plaid access token"""
    try:
        response = creds_table.get_item(
            Key={'userId': user_id}
        )
        return response.get('Item', {})
    except Exception as e:
        print(f"Error fetching credentials for {user_id}: {str(e)}")
        raise

def fetch_portfolio_data(access_token, client_id, secret):
    """Fetch portfolio holdings from Plaid Investments API"""
    
    url = "https://production.plaid.com/investments/holdings/get"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    payload = {
        'client_id': client_id,
        'secret': secret,
        'access_token': access_token
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract holdings
        holdings = data.get('holdings', [])
        securities = data.get('securities', [])
        accounts = data.get('accounts', [])
        
        # Create securities lookup
        securities_dict = {s['security_id']: s for s in securities}
        
        # Process holdings
        portfolio = []
        total_value = 0
        
        for holding in holdings:
            security_id = holding.get('security_id')
            security = securities_dict.get(security_id, {})
            
            ticker = security.get('ticker_symbol', 'N/A')
            name = security.get('name', 'Unknown')
            quantity = holding.get('quantity', 0)
            price = holding.get('institution_price', 0)
            value = holding.get('institution_value', quantity * price)
            
            if ticker != 'N/A':  # Only include securities with tickers
                portfolio.append({
                    'ticker': ticker,
                    'name': name,
                    'quantity': float(quantity),
                    'price': float(price),
                    'value': float(value)
                })
                total_value += float(value)
        
        # Sort by value descending
        portfolio.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            'holdings': portfolio,
            'total_value': total_value,
            'account_count': len(accounts)
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching portfolio: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def fetch_news_for_holdings(holdings, api_key, max_holdings=5):
    """Fetch relevant news for top holdings using Alpha Vantage"""
    
    if not api_key:
        print("No Alpha Vantage API key provided, skipping news")
        return []
    
    news_items = []
    
    # Get news for top holdings only
    top_holdings = holdings[:max_holdings]
    
    for holding in top_holdings:
        ticker = holding['ticker']
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ticker,
                'apikey': api_key,
                'limit': 3  # Get top 3 articles per ticker
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'feed' in data:
                for article in data['feed'][:2]:  # Use top 2 articles
                    news_items.append({
                        'ticker': ticker,
                        'title': article.get('title', ''),
                        'summary': article.get('summary', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', ''),
                        'sentiment': article.get('overall_sentiment_label', 'Neutral')
                    })
            
            # Respect rate limits (5 calls per minute for free tier)
            import time
            time.sleep(12)  # Wait 12 seconds between calls
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {str(e)}")
            continue
    
    return news_items
# @weave.op()  # ← ADD THIS DECORATOR -> removed on 12/2/2025 due to incomplete integration - package size limit hit
def generate_briefing_with_claude(portfolio_data, news_items, api_key):
    """Generate AI-powered briefing using Claude API"""
    
    if not api_key:
        return generate_basic_briefing(portfolio_data, news_items)
    
    # Prepare portfolio summary
    holdings_summary = []
    for holding in portfolio_data['holdings'][:10]:  # Top 10
        holdings_summary.append(
            f"• {holding['ticker']} ({holding['name']}): "
            f"{holding['quantity']:.2f} shares @ ${holding['price']:.2f} = ${holding['value']:,.2f}"
        )
    
    # Prepare news summary
    news_summary = []
    for item in news_items[:5]:  # Top 5 news items
        news_summary.append(
            f"• [{item['ticker']}] {item['title']} ({item['sentiment']})"
        )
    
    # Create prompt for Claude
    prompt = f"""You are a financial analyst creating a daily portfolio briefing. Analyze the following portfolio and news, then provide insights.

PORTFOLIO SUMMARY:
Total Value: ${portfolio_data['total_value']:,.2f}
Number of Holdings: {len(portfolio_data['holdings'])}

TOP HOLDINGS:
{chr(10).join(holdings_summary)}

RECENT NEWS:
{chr(10).join(news_summary) if news_summary else 'No recent news available'}

Please provide a brief, actionable portfolio briefing with:
1. Portfolio Overview (2-3 sentences about the portfolio composition)
2. Key Movements (any notable changes based on news sentiment)
3. Market Context (what's happening in the broader market)
4. Actionable Insights (1-2 specific recommendations)

Keep it concise, professional, and actionable. Total length: ~200 words."""

    try:
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 1000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        analysis = data['content'][0]['text']
        return analysis
        
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return generate_basic_briefing(portfolio_data, news_items)

def generate_basic_briefing(portfolio_data, news_items):
    """Generate basic briefing without AI (fallback)"""
    
    briefing = f"""Portfolio Overview:
    
Your portfolio currently holds {len(portfolio_data['holdings'])} positions with a total value of ${portfolio_data['total_value']:,.2f}.

Top Holdings:
"""
    
    for holding in portfolio_data['holdings'][:5]:
        percentage = (holding['value'] / portfolio_data['total_value'] * 100) if portfolio_data['total_value'] > 0 else 0
        briefing += f"• {holding['ticker']}: ${holding['value']:,.2f} ({percentage:.1f}%)\n"
    
    if news_items:
        briefing += "\nRecent News:\n"
        for item in news_items[:3]:
            briefing += f"• [{item['ticker']}] {item['title']}\n"
    
    return briefing

def format_email_html(user_email, portfolio_data, news_items, analysis, changes=None):
    """Format briefing as HTML email"""
    
    # Format holdings table
    holdings_rows = ""
    for i, holding in enumerate(portfolio_data['holdings'][:10], 1):
        percentage = (holding['value'] / portfolio_data['total_value'] * 100) if portfolio_data['total_value'] > 0 else 0
        holdings_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{holding['ticker']}</strong></td>
            <td>{holding['name'][:30]}</td>
            <td align="right">{holding['quantity']:.2f}</td>
            <td align="right">${holding['price']:.2f}</td>
            <td align="right">${holding['value']:,.2f}</td>
            <td align="right">{percentage:.1f}%</td>
        </tr>
        """
    
    # Format news items
    news_html = ""
    if news_items:
        for item in news_items[:5]:
            sentiment_color = {
                'Bullish': '#22c55e',
                'Bearish': '#ef4444',
                'Neutral': '#6b7280'
            }.get(item.get('sentiment', 'Neutral'), '#6b7280')
            
            news_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; background: #f9fafb; border-radius: 5px;">
                <strong style="color: #1f2937;">[{item['ticker']}]</strong>
                <span style="color: {sentiment_color}; font-size: 12px;">● {item['sentiment']}</span><br>
                <a href="{item['url']}" style="color: #2563eb; text-decoration: none;">{item['title']}</a><br>
                <span style="color: #6b7280; font-size: 13px;">{item['source']}</span>
            </div>
            """
    else:
        news_html = "<p>No recent news available for your holdings.</p>"
    
    # Create HTML email
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 28px;">📊 PortfolioBrief AI</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Your Daily Portfolio Briefing</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
        
        <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin-bottom: 30px; border-radius: 5px;">
            <h2 style="margin: 0 0 10px 0; color: #1e40af;">💼 Portfolio Summary</h2>
            <p style="font-size: 24px; font-weight: bold; margin: 0; color: #1f2937;">
                ${portfolio_data['total_value']:,.2f}
            </p>
            <p style="color: #6b7280; margin: 5px 0 0 0;">
                {len(portfolio_data['holdings'])} holdings across {portfolio_data['account_count']} account(s)
            </p>
        </div>
        
        <div style="margin-bottom: 30px;">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">🤖 AI Insights</h2>
            <div style="background: #ffffff; padding: 20px; border-radius: 5px; border: 1px solid #e5e7eb;">
                {analysis.replace(chr(10), '<br>')}
            </div>
        </div>
        
        {format_changes_html(changes) if changes else ''}

        <div style="margin-bottom: 30px;">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">📈 Top Holdings</h2>
            <table style="width: 100%; border-collapse: collapse; background: white;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e5e7eb;">#</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e5e7eb;">Ticker</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e5e7eb;">Name</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">Shares</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">Price</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">Value</th>
                        <th style="padding: 10px; text-align: right; border-bottom: 2px solid #e5e7eb;">%</th>
                    </tr>
                </thead>
                <tbody>
                    {holdings_rows}
                </tbody>
            </table>
        </div>
        
        <div style="margin-bottom: 30px;">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">📰 Market News</h2>
            {news_html}
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e5e7eb; color: #6b7280; font-size: 14px;">
            <p>This briefing was generated by PortfolioBrief AI using real-time data from your brokerage accounts.</p>
    
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <p style="margin: 0; color: #92400e; font-size: 13px;">
                    <strong>⚠️ AI-Generated Content:</strong> This briefing includes AI-generated insights that should not be considered financial advice. The analysis is for informational purposes only. Always consult with a qualified financial advisor before making investment decisions.
                </p>
            </div>
    
            <p style="margin-top: 10px;">
                <strong>Data Sources:</strong> Plaid (Portfolio) · Alpha Vantage (News) · Claude AI (Analysis)
            </p>
            <p style="margin-top: 10px;">
                Questions or feedback? Reply to this email.
            </p>
        </div>
        
    </body>
    </html>
    """
    
    return html

def format_email_text(user_email, portfolio_data, news_items, analysis):
    """Format briefing as plain text email (fallback)"""
    
    text = f"""
PortfolioBrief AI - Daily Portfolio Briefing
{datetime.now().strftime('%A, %B %d, %Y')}

========================================
PORTFOLIO SUMMARY
========================================

Total Value: ${portfolio_data['total_value']:,.2f}
Holdings: {len(portfolio_data['holdings'])}
Accounts: {portfolio_data['account_count']}

========================================
AI INSIGHTS
========================================

{analysis}

========================================
TOP HOLDINGS
========================================

"""
    
    for i, holding in enumerate(portfolio_data['holdings'][:10], 1):
        percentage = (holding['value'] / portfolio_data['total_value'] * 100) if portfolio_data['total_value'] > 0 else 0
        text += f"{i}. {holding['ticker']} - ${holding['value']:,.2f} ({percentage:.1f}%)\n"
    
    if news_items:
        text += "\n========================================\n"
        text += "MARKET NEWS\n"
        text += "========================================\n\n"
        
        for item in news_items[:5]:
            text += f"[{item['ticker']}] {item['title']}\n"
            text += f"Sentiment: {item['sentiment']} | Source: {item['source']}\n"
            text += f"{item['url']}\n\n"
    
    text += """
========================================
⚠️ DISCLAIMER: This briefing includes AI-generated insights for informational 
purposes only and should not be considered financial advice. Always consult 
with a qualified financial advisor before making investment decisions.

Powered by Plaid, Alpha Vantage, and Claude AI
Questions? Reply to this email.
"""
    
    return text

# reverting t0 the old send_briefing_email using SES and removing new fuction that uses SendGrid for sending email - 12/3/2025

def send_briefing_email(user_email, html_body, text_body):
     """Send briefing email via SES"""
    
     sender = "kbp131@gmail.com"  # Your verified SES sender
     subject = f"📊 Your Portfolio Briefing - {datetime.now().strftime('%b %d, %Y')}"
    
     try:
         response = ses_client.send_email(
             Source=sender,
             Destination={
                 'ToAddresses': [user_email]
             },
             Message={
                 'Subject': {
                     'Data': subject,
                     'Charset': 'UTF-8'
                 },
                 'Body': {
                     'Text': {
                         'Data': text_body,
                         'Charset': 'UTF-8'
                     },
                     'Html': {
                         'Data': html_body,
                         'Charset': 'UTF-8'
                     }
                 }
             }
         )
         print(f"Briefing sent to {user_email}: {response['MessageId']}")
         return True
        
     except Exception as e:
         print(f"Error sending email to {user_email}: {str(e)}")
         return False
'''
# new send_briefing_email function using SendGrid - 12/3/2025
def send_briefing_email(user_email, html_body, text_body):
    """Send briefing email via SendGrid"""
    try:
        # Get SendGrid API key from environment variable
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
        if not sendgrid_api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            raise ValueError("SendGrid API key not configured")
        
        # Get subject line
        subject = f"Your Portfolio Briefing - {datetime.now().strftime('%b %d, %Y')}"
        
        # Create SendGrid message with both HTML and plain text
        message = Mail(
            from_email=Email('kbp131@gmail.com'),
            to_emails=To(user_email),
            subject=subject
        )
        message.add_content(Content("text/plain", text_body))  # Plain text version
        message.add_content(Content("text/html", html_body))   # HTML version
        
        # Send via SendGrid
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(f"Email sent via SendGrid to {user_email}: status={response.status_code}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to send email via SendGrid: {str(e)}")
        raise
'''
def lambda_handler(event, context):
    """
    Main Lambda handler for portfolio worker
    
    Triggered by: EventBridge (daily at 7 AM CT)
    
    Process:
    1. Fetch all active users
    2. For each user:
       - Get portfolio from Plaid
       - Fetch relevant news
       - Generate AI analysis
       - Send briefing email
    """
    
    # Create Langfuse trace for this run
    trace = langfuse.trace(
        name="portfolio_daily_briefing",
        user_id="ketan",
        tags=["production", "daily"],
        metadata={
            "trigger": event.get("source", "eventbridge"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }   
    )
    
    print("Starting portfolio briefing generation...")
    print(f"Portfolio worker started at {datetime.now(timezone.utc).isoformat()}")
    
    try:
        # Get API credentials
        secrets = get_secrets()
        
        # Get all active users
        users = get_active_users()
        print(f"Found {len(users)} active user(s)")
        
        if not users:
            print("No active users found")
            trace.update(
                output={"status": "success", "message": "No active users"},
                metadata={"completed": True}
            )
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No active users'})
            }
        
        # Process each user
        results = []
        
        for user in users:
            user_id = user['userId']
            user_email = user['email']
            
            print(f"Processing briefing for {user_email}")
            
            try:
                # Get user's Plaid credentials
                creds = get_user_credentials(user_id)
                access_token = creds.get('plaidAccessToken')
                
                if not access_token:
                    print(f"No access token for {user_email}, skipping")
                    continue
                
                # Fetch portfolio data
                print(f"Fetching portfolio data for {user_email}")
                portfolio_data = fetch_portfolio_data(
                    access_token,
                    secrets['plaid_client_id'],
                    secrets['plaid_secret']
                )
                
                print(f"Portfolio fetched: {len(portfolio_data['holdings'])} holdings, ${portfolio_data['total_value']:,.2f}")
                
                # ===== PORTFOLIO CHANGE DETECTION START =====
                
                # Get yesterday's portfolio for comparison
                print(f"Fetching yesterday's portfolio for change detection")
                yesterday_portfolio = get_previous_portfolio(user_id, days_ago=1)
                
                # Detect portfolio changes
                print(f"Detecting portfolio changes")
                portfolio_changes = detect_portfolio_changes(portfolio_data, yesterday_portfolio)
                
                # Log what we found
                if portfolio_changes['is_first_run']:
                    print(f"📊 First snapshot - no previous data to compare")
                elif portfolio_changes['has_changes']:
                    print(f"✅ Changes detected: {portfolio_changes['summary']}")
                    print(f"   - Added: {portfolio_changes['summary']['added_count']}")
                    print(f"   - Removed: {portfolio_changes['summary']['removed_count']}")
                    print(f"   - Changed: {portfolio_changes['summary']['changed_count']}")
                else:
                    print(f"ℹ️ No portfolio changes detected")
                
                # Store today's snapshot for tomorrow's comparison
                print(f"Storing today's portfolio snapshot")
                snapshot_stored = store_portfolio_snapshot(user_id, portfolio_data)
                
                if not snapshot_stored:
                    print(f"⚠️ Warning: Failed to store snapshot, but continuing with briefing...")
                
                # ===== PORTFOLIO CHANGE DETECTION END =====
                
                # Fetch news for top holdings
                print(f"Fetching news for top holdings")
                news_items = fetch_news_for_holdings(
                    portfolio_data['holdings'],
                    secrets['alpha_vantage_key']
                )
                
                print(f"News fetched: {len(news_items)} articles")
                
                # Generate AI analysis
                print(f"Generating AI analysis")
                analysis = generate_briefing_with_claude(
                    portfolio_data,
                    news_items,
                    secrets['claude_api_key']
                )
                
                print(f"Analysis generated: {len(analysis)} characters")
                
                # Format emails
                html_body = format_email_html(user_email, portfolio_data, news_items, analysis, portfolio_changes)
                text_body = format_email_text(user_email, portfolio_data, news_items, analysis)
                
                # Send email
                success = send_briefing_email(user_email, html_body, text_body)
                
                results.append({
                    'user': user_email,
                    'success': success,
                    'holdings': len(portfolio_data['holdings']),
                    'news': len(news_items)
                })
                
            except Exception as e:
                print(f"Error processing {user_email}: {str(e)}")
                import traceback
                traceback.print_exc()
                
                results.append({
                    'user': user_email,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r.get('success'))
        print(f"Completed: {successful}/{len(results)} briefings sent successfully")
        
        # Log success to Langfuse
        trace.update(
            output={
                "status": "success",
                "users_processed": len(results),
                "successful": successful
            },
            metadata={"completed": True}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(results)} users',
                'successful': successful,
                'results': results
            })
        }
        
    except Exception as e:
        print(f"Fatal error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log error to Langfuse
        trace.update(
            output={"status": "error", "error": str(e)},
            metadata={"completed": False}
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    
    finally:
        # Ensure Langfuse sends the data
        langfuse.flush()