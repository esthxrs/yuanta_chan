"""
Trade History Lambda Function - Mock Trade Data Reporter
Enhanced for AWS Chatbot Board Demonstration
Implements: Trade history retrieval → Mock data generation → Structured response
Designed for Amazon Bedrock Agent integration with <2s response time
"""

import json
import sys
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from logger import get_logger


class TradeHistoryReporter:
    """
    Trade History Reporter for Investment Consultant queries
    
    Generates mock trade data for demonstration purposes
    Supports different query types and time frames
    Optimized for board demonstration with structured output
    """
    
    def __init__(self):
        self.logger = get_logger("TradeHistoryLambda")
        self.start_time = None
        
        # Mock user data for demonstration
        self.mock_user_id = "mock_ic_user_1"
        
        # Supported query types
        self.supported_query_types = ["allTrades"]
        
        # Mock ticker symbols for realistic data
        self.mock_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "JPM", "JNJ", "PG", "V", "UNH", "HD", "DIS", "PYPL", "ADBE", "CRM"
        ]
        
        # Mock trade types
        self.trade_types = ["BUY", "SELL"]
    
    def get_trade_history(self, query_type: str, time_frame: str = "this year", 
                         user_id: str = "mock_ic_user_1") -> Dict[str, Any]:
        """
        Retrieve mock trade history based on query parameters
        
        Args:
            query_type: Type of trade history requested ("allTrades")
            time_frame: Period for the query (e.g., "this year", "last month")
            user_id: User identifier (for future extensibility)
            
        Returns:
            Structured trade history data or error response
        """
        self.start_time = time.time()
        self.logger.info(f"🚀 Processing trade history request", 
                        context={
                            'queryType': query_type,
                            'timeFrame': time_frame,
                            'userId': user_id
                        })
        
        try:
            # Only support 'allTrades' query type
            if query_type != "allTrades":
                return self._format_error_response(
                    "InvalidQuery", 
                    f"Unsupported query type: {query_type}. Only 'allTrades' is supported."
                )
            
            # Generate mock trade data for 'allTrades'
            result = self._generate_all_trades(time_frame, user_id)
            
            # Add performance metrics
            total_time = time.time() - self.start_time
            result['performance'] = {
                'execution_time': round(total_time, 3),
                'query_type': query_type,
                'time_frame': time_frame,
                'records_returned': len(result.get('trades', []))
            }
            
            self.logger.info(f"✅ Trade history retrieved successfully", 
                           context={
                               'queryType': query_type,
                               'timeFrame': time_frame,
                               'executionTime': total_time,
                               'recordsReturned': len(result.get('trades', []))
                           })
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Trade history retrieval failed", error=e)
            return self._format_error_response(
                "InternalError", 
                f"Failed to retrieve trade history: {str(e)}"
            )
    
    def _generate_all_trades(self, time_frame: str, user_id: str) -> Dict[str, Any]:
        """
        Generate mock trade data for 'allTrades' query type
        """
        self.logger.info(f"📊 Generating mock trades for {time_frame}")
        
        # Determine date range based on time frame
        start_date, end_date = self._parse_time_frame(time_frame)
        
        # Generate random number of trades (5-15 for demonstration)
        num_trades = random.randint(5, 15)
        trades = []
        
        for i in range(num_trades):
            trade = self._generate_mock_trade(start_date, end_date)
            trades.append(trade)
        
        # Sort trades by date (most recent first)
        trades.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'queryType': 'allTrades',
            'timeFrame': time_frame,
            'userId': user_id,
            'trades': trades,
            'summary': {
                'total_trades': len(trades),
                'buy_trades': len([t for t in trades if t['type'] == 'BUY']),
                'sell_trades': len([t for t in trades if t['type'] == 'SELL']),
                'unique_tickers': len(set(t['ticker'] for t in trades)),
                'total_volume': sum(t['quantity'] for t in trades),
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                }
            },
            'message': f"Successfully retrieved {len(trades)} mock trades for {time_frame}."
        }
    
    def _generate_mock_trade(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate a single mock trade record
        """
        # Random date within the time frame
        days_between = (end_date - start_date).days
        random_days = random.randint(0, days_between)
        trade_date = start_date + timedelta(days=random_days)
        
        # Random trade parameters
        ticker = random.choice(self.mock_tickers)
        trade_type = random.choice(self.trade_types)
        quantity = random.randint(1, 100)
        price = round(random.uniform(50, 500), 2)
        
        return {
            'date': trade_date.strftime('%Y-%m-%d'),
            'ticker': ticker,
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'total_value': round(quantity * price, 2),
            'trade_id': f"TRADE_{trade_date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
        }
    
    def _parse_time_frame(self, time_frame: str) -> tuple:
        """
        Parse time frame string and return start/end dates
        """
        now = datetime.now()
        
        if time_frame.lower() == "this year":
            start_date = datetime(now.year, 1, 1)
            end_date = now
        elif time_frame.lower() == "last month":
            start_date = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_date = now.replace(day=1) - timedelta(days=1)
        elif time_frame.lower() == "last quarter":
            quarter_start = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start, day=1)
            if start_date > now:
                start_date = start_date.replace(year=start_date.year - 1)
            end_date = now
        elif time_frame.lower() == "last 6 months":
            start_date = now - timedelta(days=180)
            end_date = now
        else:
            # Default to this year
            start_date = datetime(now.year, 1, 1)
            end_date = now
        
        return start_date, end_date
    
    def _format_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """Format error response"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'error': error_type,
            'message': message,
            'queryType': None,
            'timeFrame': None,
            'userId': None,
            'performance': {
                'execution_time': round(total_time, 3),
                'status': 'Failed'
            },
            'timestamp': datetime.now().isoformat()
        }


# Lambda handler function
def lambda_handler(event, context):
    """
    AWS Lambda handler for trade history reporting
    Optimized for board demonstration of AWS chatbot capabilities
    
    Expected event format:
    {
        "queryType": "allTrades",
        "timeFrame": "this year",
        "userId": "mock_ic_user_1"
    }
    """
    logger = get_logger("TradeHistoryLambda")
    
    try:
        # Extract parameters from event
        query_type = event.get('queryType', '')
        time_frame = event.get('timeFrame', 'this year')
        user_id = event.get('userId', 'mock_ic_user_1')
        request_id = event.get('requestId', f'req-{int(time.time())}')
        
        logger.info(f"🚀 Processing trade history request", 
                   context={
                       'requestId': request_id, 
                       'queryType': query_type, 
                       'timeFrame': time_frame,
                       'userId': user_id
                   })
        
        if not query_type:
            raise ValueError("Missing required parameter: queryType")
        
        # Process trade history request
        reporter = TradeHistoryReporter()
        result = reporter.get_trade_history(query_type, time_frame, user_id)
        
        # Check if result contains error
        if 'error' in result:
            response = {
                'statusCode': 400,
                'body': json.dumps(result, default=str),
                'headers': {
                    'Content-Type': 'application/json',
                    'X-Request-ID': request_id,
                    'X-Function': 'TradeHistoryTool'
                }
            }
        else:
            response = {
                'statusCode': 200,
                'body': json.dumps(result, default=str),
                'headers': {
                    'Content-Type': 'application/json',
                    'X-Request-ID': request_id,
                    'X-Function': 'TradeHistoryTool',
                    'X-Execution-Time': str(result.get('performance', {}).get('execution_time', 0))
                }
            }
        
        execution_time = result.get('performance', {}).get('execution_time', 0)
        logger.info(f"✅ Trade history request completed successfully", 
                   context={
                       'requestId': request_id, 
                       'queryType': query_type,
                       'executionTime': execution_time,
                       'recordsReturned': result.get('performance', {}).get('records_returned', 0)
                   })
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Lambda execution failed", 
                    context={'requestId': event.get('requestId', 'unknown')}, 
                    error=e)
        
        error_response = {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'InternalError',
                'message': str(e),
                'queryType': event.get('queryType', 'unknown'),
                'timeFrame': event.get('timeFrame', 'unknown'),
                'userId': event.get('userId', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }),
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': event.get('requestId', 'unknown'),
                'X-Function': 'TradeHistoryTool'
            }
        }
        
        return error_response


# For local testing and board demonstration
if __name__ == "__main__":
    # Test cases for board demonstration
    test_cases = [
        {
            "queryType": "allTrades",
            "timeFrame": "this year",
            "userId": "mock_ic_user_1",
            "requestId": "board-demo-001"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "last month",
            "userId": "mock_ic_user_1",
            "requestId": "board-demo-002"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "last quarter",
            "userId": "mock_ic_user_1",
            "requestId": "board-demo-003"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "last 6 months",
            "userId": "mock_ic_user_1",
            "requestId": "board-demo-004"
        }
    ]
    
    print("🎯 AWS Chatbot Trade History - Board Demonstration")
    print("=" * 60)
    
    for i, test_event in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}: {test_event['queryType']} ({test_event['timeFrame']})")
        print("-" * 40)
        
        result = lambda_handler(test_event, None)
        
        if result['statusCode'] == 200:
            data = json.loads(result['body'])
            perf = data.get('performance', {})
            
            print(f"✅ Success: {data.get('message', 'Trade history retrieved')}")
            print(f"⏱️  Execution Time: {perf.get('execution_time', 0)}s")
            
            trades = data.get('trades', [])
            summary = data.get('summary', {})
            print(f"📈 Trades Found: {len(trades)}")
            print(f"💰 Buy/Sell: {summary.get('buy_trades', 0)}/{summary.get('sell_trades', 0)}")
            print(f"🎯 Sample Trades:")
            for trade in trades[:]:  # Show first 3 trades
                print(f"   {trade['date']}: {trade['type']} {trade['quantity']} {trade['ticker']} @ ${trade['price']}")
        else:
            data = json.loads(result['body'])
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("🚀 Board Demonstration Complete - Trade History Tool Ready!") 