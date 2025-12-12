"""
Portfolio Briefing Observability Logger, v1, 12/12/2025

Lightweight logging solution for tracking:
- Agent execution metrics
- Token usage and costs
- Errors and failures
- Overall performance

Uses Python's built-in logging (zero dependencies)
Logs to CloudWatch for querying and analysis
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger('portfolio_briefing')
logger.setLevel(logging.INFO)


class PortfolioLogger:
    """
    Lightweight observability logger for portfolio briefing system.
    
    Tracks metrics for interview talking point:
    "I added observability to track agent performance, costs, and errors"
    """
    
    def __init__(self, user_email: str):
        """
        Initialize logger for a briefing run.
        
        Args:
            user_email: Email of user being processed
        """
        self.user_email = user_email
        self.run_id = f"{user_email}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.metrics = {
            'run_id': self.run_id,
            'user': user_email,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'agents': {},
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors': [],
            'status': 'started'
        }
        
        logger.info(f"[BRIEFING_START] {json.dumps({'run_id': self.run_id, 'user': user_email})}")
    
    def log_portfolio_fetch(self, holdings_count: int, total_value: float):
        """
        Log portfolio data fetch.
        
        Args:
            holdings_count: Number of holdings
            total_value: Total portfolio value
        """
        logger.info(f"[PORTFOLIO_FETCH] {json.dumps({
            'run_id': self.run_id,
            'holdings_count': holdings_count,
            'total_value': total_value
        })}")
        
        self.metrics['portfolio'] = {
            'holdings_count': holdings_count,
            'total_value': total_value
        }
    
    def log_news_fetch(self, articles_count: int):
        """
        Log news fetch.
        
        Args:
            articles_count: Number of articles fetched
        """
        logger.info(f"[NEWS_FETCH] {json.dumps({
            'run_id': self.run_id,
            'articles_count': articles_count
        })}")
        
        self.metrics['news'] = {
            'articles_count': articles_count
        }
    
    def log_ai_analysis(self, analysis_length: int, estimated_tokens: int = None, estimated_cost: float = None):
        """
        Log AI analysis generation.
        
        Args:
            analysis_length: Character count of analysis
            estimated_tokens: Estimated token count (optional)
            estimated_cost: Estimated cost in USD (optional)
        """
        # Rough token estimation if not provided: ~4 chars per token
        if estimated_tokens is None:
            estimated_tokens = analysis_length // 4
        
        # Rough cost estimation if not provided: Claude Sonnet ~$3 per 1M input tokens, ~$15 per 1M output tokens
        # Assuming 50/50 input/output for safety, use average of ~$9 per 1M tokens
        if estimated_cost is None:
            estimated_cost = (estimated_tokens / 1_000_000) * 9.0
        
        logger.info(f"[AI_ANALYSIS] {json.dumps({
            'run_id': self.run_id,
            'analysis_length': analysis_length,
            'estimated_tokens': estimated_tokens,
            'estimated_cost': estimated_cost
        })}")
        
        self.metrics['ai_analysis'] = {
            'analysis_length': analysis_length,
            'estimated_tokens': estimated_tokens,
            'estimated_cost': estimated_cost
        }
        
        # Update totals
        self.metrics['total_tokens'] += estimated_tokens
        self.metrics['total_cost'] += estimated_cost
    
    def log_portfolio_changes(self, has_changes: bool, added: int = 0, removed: int = 0, changed: int = 0):
        """
        Log portfolio changes detection.
        
        Args:
            has_changes: Whether changes were detected
            added: Number of added positions
            removed: Number of removed positions
            changed: Number of changed positions
        """
        logger.info(f"[PORTFOLIO_CHANGES] {json.dumps({
            'run_id': self.run_id,
            'has_changes': has_changes,
            'added': added,
            'removed': removed,
            'changed': changed
        })}")
        
        self.metrics['portfolio_changes'] = {
            'has_changes': has_changes,
            'added': added,
            'removed': removed,
            'changed': changed
        }
    
    def log_error(self, error_type: str, error_message: str, component: str = None):
        """
        Log an error.
        
        Args:
            error_type: Type of error (e.g., 'PlaidAPIError', 'AlphaVantageError')
            error_message: Error message
            component: Component where error occurred (e.g., 'portfolio_fetch', 'ai_analysis')
        """
        error_data = {
            'run_id': self.run_id,
            'error_type': error_type,
            'error_message': error_message,
            'component': component,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.error(f"[ERROR] {json.dumps(error_data)}")
        
        self.metrics['errors'].append(error_data)
        self.metrics['status'] = 'error'
    
    def log_success(self, email_sent: bool = True):
        """
        Log successful completion.
        
        Args:
            email_sent: Whether email was successfully sent
        """
        self.metrics['status'] = 'success' if email_sent else 'partial_success'
        self.metrics['email_sent'] = email_sent
        self.metrics['end_time'] = datetime.now(timezone.utc).isoformat()
        
        # Calculate duration
        start = datetime.fromisoformat(self.metrics['start_time'])
        end = datetime.fromisoformat(self.metrics['end_time'])
        duration_seconds = (end - start).total_seconds()
        self.metrics['duration_seconds'] = duration_seconds
        
        logger.info(f"[BRIEFING_SUCCESS] {json.dumps({
            'run_id': self.run_id,
            'user': self.user_email,
            'duration_seconds': duration_seconds,
            'total_tokens': self.metrics['total_tokens'],
            'total_cost': self.metrics['total_cost'],
            'email_sent': email_sent
        })}")
    
    def log_summary(self):
        """
        Log final summary of entire briefing run.
        Call this at the very end to get complete metrics.
        """
        logger.info(f"[BRIEFING_SUMMARY] {json.dumps(self.metrics)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary of all metrics
        """
        return self.metrics


def log_lambda_start(event: Dict[str, Any]):
    """
    Log Lambda function start.
    
    Args:
        event: Lambda event data
    """
    logger.info(f"[LAMBDA_START] {json.dumps({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trigger': event.get('source', 'unknown'),
        'event_type': event.get('detail-type', 'unknown')
    })}")


def log_lambda_complete(user_count: int, successful: int, failed: int, duration_seconds: float):
    """
    Log Lambda function completion.
    
    Args:
        user_count: Total users processed
        successful: Successfully processed
        failed: Failed to process
        duration_seconds: Total execution time
    """
    logger.info(f"[LAMBDA_COMPLETE] {json.dumps({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_count': user_count,
        'successful': successful,
        'failed': failed,
        'duration_seconds': duration_seconds,
        'success_rate': (successful / user_count * 100) if user_count > 0 else 0
    })}")


# Example CloudWatch Insights queries for analyzing logs:
"""
# Find all errors in last 24 hours:
fields @timestamp, @message
| filter @message like /\[ERROR\]/
| sort @timestamp desc
| limit 100

# Calculate average cost per briefing:
fields @timestamp, @message
| filter @message like /\[BRIEFING_SUCCESS\]/
| parse @message '{"total_cost": *,' as total_cost
| stats avg(total_cost) as avg_cost, sum(total_cost) as total_cost

# Track portfolio changes:
fields @timestamp, @message
| filter @message like /\[PORTFOLIO_CHANGES\]/
| parse @message '{"has_changes": *,' as has_changes
| stats count() by has_changes

# Monitor success rate:
fields @timestamp, @message
| filter @message like /\[LAMBDA_COMPLETE\]/
| parse @message '{"success_rate": *,' as success_rate
| stats avg(success_rate) as avg_success_rate
"""