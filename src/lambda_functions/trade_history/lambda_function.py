"""
Trade History Lambda Function - Mock Trade Data Reporter with Filtering
Enhanced for AWS Chatbot Board Demonstration
Implements: Trade history retrieval → Filter processing → Constraint-based mock data generation → Structured response
Designed for Amazon Bedrock Agent integration with <2s response time
"""

import json
import sys
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from logger import get_logger


class TradeFilterEngine:
    """
    Filter engine for trade history queries
    
    Validates and processes filter parameters for trade history requests
    Supports ticker, trade type, price range, quantity range, and date range filtering
    """
    
    def __init__(self):
        self.logger = get_logger("TradeFilterEngine")
        self.supported_filters = ['tickers', 'tradeTypes', 'priceRange', 'quantityRange', 'dateRange']
        
        # Valid trade types
        self.valid_trade_types = ["BUY", "SELL"]
        
        # Valid ticker symbols (subset of common stocks)
        self.valid_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "JPM", "JNJ", "PG", "V", "UNH", "HD", "DIS", "PYPL", "ADBE", "CRM"
        ]
    
    def validate_filters(self, filters: dict) -> Dict[str, Any]:
        """
        Validate and normalize filter parameters
        
        Args:
            filters: Dictionary containing filter parameters
            
        Returns:
            Dictionary with validation result and normalized filters
        """
        if not filters:
            return {'valid': True, 'filters': {}, 'errors': []}
        
        errors = []
        normalized_filters = {}
        
        # Validate tickers
        if 'tickers' in filters:
            tickers = filters['tickers']
            if not isinstance(tickers, list):
                errors.append("tickers must be a list")
            else:
                invalid_tickers = [t for t in tickers if t not in self.valid_tickers]
                if invalid_tickers:
                    errors.append(f"Invalid tickers: {invalid_tickers}")
                else:
                    normalized_filters['tickers'] = tickers
        
        # Validate trade types
        if 'tradeTypes' in filters:
            trade_types = filters['tradeTypes']
            if not isinstance(trade_types, list):
                errors.append("tradeTypes must be a list")
            else:
                invalid_types = [t for t in trade_types if t not in self.valid_trade_types]
                if invalid_types:
                    errors.append(f"Invalid trade types: {invalid_types}")
                else:
                    normalized_filters['tradeTypes'] = trade_types
        
        # Validate price range
        if 'priceRange' in filters:
            price_range = filters['priceRange']
            if not isinstance(price_range, dict):
                errors.append("priceRange must be a dictionary")
            else:
                min_price = price_range.get('min')
                max_price = price_range.get('max')
                
                if min_price is not None and not isinstance(min_price, (int, float)):
                    errors.append("priceRange.min must be a number")
                if max_price is not None and not isinstance(max_price, (int, float)):
                    errors.append("priceRange.max must be a number")
                
                if min_price is not None and max_price is not None and min_price > max_price:
                    errors.append("priceRange.min cannot be greater than priceRange.max")
                
                if min_price is not None and min_price < 0:
                    errors.append("priceRange.min cannot be negative")
                
                if not errors:
                    normalized_filters['priceRange'] = {
                        'min': min_price if min_price is not None else 50.0,
                        'max': max_price if max_price is not None else 500.0
                    }
        
        # Validate quantity range
        if 'quantityRange' in filters:
            qty_range = filters['quantityRange']
            if not isinstance(qty_range, dict):
                errors.append("quantityRange must be a dictionary")
            else:
                min_qty = qty_range.get('min')
                max_qty = qty_range.get('max')
                
                if min_qty is not None and not isinstance(min_qty, int):
                    errors.append("quantityRange.min must be an integer")
                if max_qty is not None and not isinstance(max_qty, int):
                    errors.append("quantityRange.max must be an integer")
                
                if min_qty is not None and max_qty is not None and min_qty > max_qty:
                    errors.append("quantityRange.min cannot be greater than quantityRange.max")
                
                if min_qty is not None and min_qty < 1:
                    errors.append("quantityRange.min cannot be less than 1")
                
                if not errors:
                    normalized_filters['quantityRange'] = {
                        'min': min_qty if min_qty is not None else 1,
                        'max': max_qty if max_qty is not None else 100
                    }
        
        # Validate date range
        if 'dateRange' in filters:
            date_range = filters['dateRange']
            if not isinstance(date_range, dict):
                errors.append("dateRange must be a dictionary")
            else:
                start_date = date_range.get('start')
                end_date = date_range.get('end')
                
                if start_date is not None:
                    try:
                        datetime.strptime(start_date, '%Y-%m-%d')
                    except ValueError:
                        errors.append("dateRange.start must be in YYYY-MM-DD format")
                
                if end_date is not None:
                    try:
                        datetime.strptime(end_date, '%Y-%m-%d')
                    except ValueError:
                        errors.append("dateRange.end must be in YYYY-MM-DD format")
                
                if start_date and end_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        if start_dt > end_dt:
                            errors.append("dateRange.start cannot be after dateRange.end")
                    except ValueError:
                        pass  # Already caught above
                
                if not errors:
                    normalized_filters['dateRange'] = {
                        'start': start_date,
                        'end': end_date
                    }
        
        return {
            'valid': len(errors) == 0,
            'filters': normalized_filters,
            'errors': errors
        }
    
    def apply_filters_to_generation(self, filters: dict, generation_params: dict) -> dict:
        """
        Modify generation parameters based on filters
        
        Args:
            filters: Validated filter parameters
            generation_params: Current generation parameters
            
        Returns:
            Modified generation parameters
        """
        modified_params = generation_params.copy()
        
        # Apply date range filter if present
        if filters.get('dateRange'):
            date_range = filters['dateRange']
            if date_range.get('start'):
                modified_params['startDate'] = datetime.strptime(date_range['start'], '%Y-%m-%d')
            if date_range.get('end'):
                modified_params['endDate'] = datetime.strptime(date_range['end'], '%Y-%m-%d')
        
        return modified_params
    
    def should_generate_trade(self, trade_data: dict, filters: dict) -> bool:
        """
        Check if a trade should be generated based on filters
        
        Args:
            trade_data: Proposed trade data
            filters: Active filters
            
        Returns:
            True if trade should be generated, False otherwise
        """
        # This method is used for post-generation filtering if needed
        # For constraint-based generation, we apply filters during generation
        return True
    
    def generate_filter_summary(self, filters: dict) -> str:
        """
        Generate a human-readable summary of applied filters
        
        Args:
            filters: Applied filter parameters
            
        Returns:
            String summary of filters
        """
        if not filters:
            return "No filters applied"
        
        summary_parts = []
        
        if filters.get('tickers'):
            summary_parts.append(f"Tickers: {', '.join(filters['tickers'])}")
        
        if filters.get('tradeTypes'):
            summary_parts.append(f"Trade Types: {', '.join(filters['tradeTypes'])}")
        
        if filters.get('priceRange'):
            price_range = filters['priceRange']
            if price_range.get('min') and price_range.get('max'):
                summary_parts.append(f"Price Range: ${price_range['min']} - ${price_range['max']}")
            elif price_range.get('min'):
                summary_parts.append(f"Min Price: ${price_range['min']}")
            elif price_range.get('max'):
                summary_parts.append(f"Max Price: ${price_range['max']}")
        
        if filters.get('quantityRange'):
            qty_range = filters['quantityRange']
            if qty_range.get('min') and qty_range.get('max'):
                summary_parts.append(f"Quantity Range: {qty_range['min']} - {qty_range['max']}")
            elif qty_range.get('min'):
                summary_parts.append(f"Min Quantity: {qty_range['min']}")
            elif qty_range.get('max'):
                summary_parts.append(f"Max Quantity: {qty_range['max']}")
        
        if filters.get('dateRange'):
            date_range = filters['dateRange']
            if date_range.get('start') and date_range.get('end'):
                summary_parts.append(f"Date Range: {date_range['start']} to {date_range['end']}")
            elif date_range.get('start'):
                summary_parts.append(f"From: {date_range['start']}")
            elif date_range.get('end'):
                summary_parts.append(f"To: {date_range['end']}")
        
        return "; ".join(summary_parts) if summary_parts else "No filters applied"


class TradeHistoryReporter:
    """
    Trade History Reporter for Investment Consultant queries
    
    Generates mock trade data for demonstration purposes
    Supports different query types, time frames, and filtering
    Optimized for board demonstration with structured output
    """
    
    def __init__(self):
        self.logger = get_logger("TradeHistoryLambda")
        self.start_time = None
        
        # Mock user data for demonstration
        self.mockUserId = "mock_ic_user_1"
        
        # Supported query types
        self.supportedQueryTypes = ["allTrades"]
        
        # Mock ticker symbols for realistic data
        self.mockTickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "JPM", "JNJ", "PG", "V", "UNH", "HD", "DIS", "PYPL", "ADBE", "CRM"
        ]
        
        # Mock trade types
        self.tradeTypes = ["BUY", "SELL"]
        
        # Initialize filter engine
        self.filterEngine = TradeFilterEngine()
    
    def getTradeHistory(self, queryType: str, timeFrame: str = "this year", 
                         userId: str = "mock_ic_user_1", filters: Optional[dict] = None) -> Dict[str, Any]:
        """
        Retrieve mock trade history based on query parameters and filters
        
        Args:
            queryType: Type of trade history requested ("allTrades")
            timeFrame: Period for the query (e.g., "this year", "last month")
            userId: User identifier (for future extensibility)
            filters: Optional filter parameters for trade filtering
            
        Returns:
            Structured trade history data or error response
        """
        self.start_time = time.time()
        self.logger.info(f"🚀 Processing trade history request", 
                        context={
                            'queryType': queryType,
                            'timeFrame': timeFrame,
                            'userId': userId,
                            'hasFilters': filters is not None
                        })
        
        try:
            # Only support 'allTrades' query type
            if queryType != "allTrades":
                return self._format_error_response(
                    "InvalidQuery", 
                    f"Unsupported query type: {queryType}. Only 'allTrades' is supported."
                )
            
            # Validate filters if provided
            if filters:
                validationResult = self.filterEngine.validate_filters(filters)
                if not validationResult['valid']:
                    return self._format_error_response(
                        "InvalidFilters",
                        f"Filter validation failed: {'; '.join(validationResult['errors'])}"
                    )
                validatedFilters = validationResult['filters']
            else:
                validatedFilters = {}
            
            # Generate mock trade data for 'allTrades' with filters
            result = self._generateAllTradesWithFilters(timeFrame, userId, validatedFilters)
            
            # Add performance metrics
            totalTime = time.time() - self.start_time
            result['performance'] = {
                'executionTime': round(totalTime, 3),
                'queryType': queryType,
                'timeFrame': timeFrame,
                'recordsReturned': len(result.get('trades', [])),
                'filtersApplied': bool(validatedFilters)
            }
            
            self.logger.info(f"✅ Trade history retrieved successfully", 
                           context={
                               'queryType': queryType,
                               'timeFrame': timeFrame,
                               'executionTime': totalTime,
                               'recordsReturned': len(result.get('trades', [])),
                               'filtersApplied': bool(validatedFilters)
                           })
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Trade history retrieval failed", error=e)
            return self._format_error_response(
                "InternalError", 
                f"Failed to retrieve trade history: {str(e)}"
            )
    
    def _generateAllTradesWithFilters(self, timeFrame: str, userId: str, filters: dict) -> Dict[str, Any]:
        """
        Generate mock trade data for 'allTrades' query type with filtering
        """
        self.logger.info(f"📊 Generating mock trades for {timeFrame} with filters: {bool(filters)}")
        
        # Determine date range based on time frame and filters
        startDate, endDate = self._parseTimeFrame(timeFrame)
        
        # Apply date range filter if present
        if filters.get('dateRange'):
            dateRange = filters['dateRange']
            if dateRange.get('start'):
                startDate = datetime.strptime(dateRange['start'], '%Y-%m-%d')
            if dateRange.get('end'):
                endDate = datetime.strptime(dateRange['end'], '%Y-%m-%d')
        
        # Generate random number of trades (5-15 for demonstration)
        numTrades = random.randint(5, 15)
        trades = []
        
        for i in range(numTrades):
            trade = self._generate_mock_trade_with_filters(startDate, endDate, filters)
            if trade:  # Only add if trade was generated successfully
                trades.append(trade)
        
        # Sort trades by date (most recent first)
        trades.sort(key=lambda x: x['date'], reverse=True)
        
        return self._format_filtered_response(trades, filters, {
            'queryType': 'allTrades',
            'timeFrame': timeFrame,
            'userId': userId,
            'startDate': startDate,
            'endDate': endDate
        })
    
    def _generate_mock_trade_with_filters(self, start_date: datetime, end_date: datetime, filters: dict) -> Optional[Dict[str, Any]]:
        """
        Generate a single mock trade that satisfies filter constraints
        """
        # Random date within the time frame
        daysBetween = (end_date - start_date).days
        if daysBetween < 0:
            return None  # Invalid date range
        
        # Handle case where startDate and endDate are the same
        if daysBetween == 0:
            randomDays = 0
        else:
            randomDays = random.randint(0, daysBetween)
        trade_date = start_date + timedelta(days=randomDays)
        
        # Apply ticker filter
        if filters.get('tickers'):
            ticker = random.choice(filters['tickers'])
        else:
            ticker = random.choice(self.mockTickers)
        
        # Apply trade type filter
        if filters.get('tradeTypes'):
            trade_type = random.choice(filters['tradeTypes'])
        else:
            trade_type = random.choice(self.tradeTypes)
        
        # Apply price range filter
        priceRange = filters.get('priceRange', {})
        minPrice = priceRange.get('min', 50.0)
        maxPrice = priceRange.get('max', 500.0)
        price = round(random.uniform(minPrice, maxPrice), 2)
        
        # Apply quantity range filter
        qtyRange = filters.get('quantityRange', {})
        minQty = qtyRange.get('min', 1)
        maxQty = qtyRange.get('max', 100)
        quantity = random.randint(minQty, maxQty)
        
        return {
            'date': trade_date.strftime('%Y-%m-%d'),
            'ticker': ticker,
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'totalValue': round(quantity * price, 2),
            'tradeId': f"TRADE_{trade_date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
        }
    
    def _format_filtered_response(self, trades: List[Dict], filters: dict, original_params: dict) -> Dict[str, Any]:
        """
        Format response with filter summary
        """
        # Generate filter summary
        filter_summary = self.filterEngine.generate_filter_summary(filters)
        
        return {
            'queryType': original_params['queryType'],
            'timeFrame': original_params['timeFrame'],
            'userId': original_params['userId'],
            'filters': filters,
            'trades': trades,
            'summary': {
                'totalTrades': len(trades),
                'buyTrades': len([t for t in trades if t['type'] == 'BUY']),
                'sellTrades': len([t for t in trades if t['type'] == 'SELL']),
                'uniqueTickers': len(set(t['ticker'] for t in trades)),
                'totalVolume': sum(t['quantity'] for t in trades),
                'filterSummary': filter_summary,
                'dateRange': {
                    'start': original_params['startDate'].strftime('%Y-%m-%d'),
                    'end': original_params['endDate'].strftime('%Y-%m-%d')
                }
            },
            'message': f"Successfully retrieved {len(trades)} filtered trades for {original_params['timeFrame']}."
        }
    
    def _generateAllTrades(self, timeFrame: str, userId: str) -> Dict[str, Any]:
        """
        Generate mock trade data for 'allTrades' query type (legacy method for backward compatibility)
        """
        return self._generateAllTradesWithFilters(timeFrame, userId, {})
    
    def _generateMockTrade(self, startDate: datetime, endDate: datetime) -> Dict[str, Any]:
        """
        Generate a single mock trade record (legacy method for backward compatibility)
        """
        trade = self._generate_mock_trade_with_filters(startDate, endDate, {})
        if trade is None:
            # Fallback to a basic trade if filter generation fails
            return {
                'date': startDate.strftime('%Y-%m-%d'),
                'ticker': 'AAPL',
                'type': 'BUY',
                'quantity': 10,
                'price': 150.0,
                'totalValue': 1500.0,
                'tradeId': f"TRADE_{startDate.strftime('%Y%m%d')}_0001"
            }
        return trade
    
    def _parseTimeFrame(self, timeFrame: str) -> Tuple[datetime, datetime]:
        """
        Parse time frame string and return start/end dates
        """
        now = datetime.now()
        
        if timeFrame.lower() == "this year":
            startDate = datetime(now.year, 1, 1)
            endDate = now
        elif timeFrame.lower() == "last month":
            startDate = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            endDate = now.replace(day=1) - timedelta(days=1)
        elif timeFrame.lower() == "last quarter":
            quarterStart = ((now.month - 1) // 3) * 3 + 1
            startDate = now.replace(month=quarterStart, day=1)
            if startDate > now:
                startDate = startDate.replace(year=startDate.year - 1)
            endDate = now
        elif timeFrame.lower() == "last 6 months":
            startDate = now - timedelta(days=180)
            endDate = now
        else:
            # Default to this year
            startDate = datetime(now.year, 1, 1)
            endDate = now
        
        return startDate, endDate
    
    def _format_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """Format error response"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'error': error_type,
            'message': message,
            'queryType': None,
            'timeFrame': None,
            'userId': None,
            'filtersJson': None,
            'performance': {
                'executionTime': round(total_time, 3),
                'status': 'Failed'
            },
            'timestamp': datetime.now().isoformat()
        }


# Lambda handler function
def lambda_handler(event, context):
    """
    AWS Lambda handler for trade history reporting with filtering
    Supports API Gateway, direct Lambda, and Bedrock Action Group integration.
    """
    logger = get_logger("TradeHistoryLambda")
    print(f"DEBUG: Full event received by Lambda: {json.dumps(event, indent=2)}")

    # Bedrock Action Group response fields
    actionGroup = event.get('actionGroup', 'TradeHistoryActionGroup')
    function = event.get('function', 'trade_history')
    messageVersion = event.get('messageVersion', '1.0')

    try:
        # --- Parameter Extraction ---
        # Try Bedrock Action Group style (parameters list)
        user_id = time_frame = query_type = filters_json_str = request_id = None
        is_bedrock = False
        if 'parameters' in event and isinstance(event['parameters'], list):
            is_bedrock = True
            for param in event['parameters']:
                if param.get('name') == 'userId' and param.get('value') is not None:
                    user_id = param.get('value')
                elif param.get('name') == 'timeFrame' and param.get('value') is not None:
                    time_frame = param.get('value')
                elif param.get('name') == 'queryType' and param.get('value') is not None:
                    query_type = param.get('value')
                elif param.get('name') == 'filtersJson' and param.get('value') is not None:
                    filters_json_str = param.get('value')
                elif param.get('name') == 'requestId' and param.get('value') is not None:
                    request_id = param.get('value')
        # Fallback to direct keys (API Gateway, curl, etc.)
        user_id = user_id or event.get('userId', 'mock_ic_user_1')
        time_frame = time_frame or event.get('timeFrame', 'this year')
        query_type = query_type or event.get('queryType', 'allTrades')
        filters_json_str = filters_json_str or event.get('filtersJson', None)
        request_id = request_id or event.get('requestId', f'req-{int(time.time())}')

        # For API Gateway, check if body is present and parse it
        is_api_gateway = False
        if (('httpMethod' in event or 'requestContext' in event) and 'body' in event):
            is_api_gateway = True
            try:
                body = json.loads(event.get('body', '{}'))
                user_id = body.get('userId', user_id)
                time_frame = body.get('timeFrame', time_frame)
                query_type = body.get('queryType', query_type)
                filters_json_str = body.get('filtersJson', filters_json_str)
                request_id = body.get('requestId', request_id)
            except Exception as e:
                logger.error("Failed to parse API Gateway body", error=e)
                if is_bedrock:
                    error_details = {'error': 'InvalidRequest', 'message': 'Invalid JSON in request body'}
                    responseBody_for_error = {"TEXT": {"body": json.dumps(error_details)}}
                    return {
                        'messageVersion': messageVersion,
                        'response': {
                            'actionGroup': actionGroup,
                            'function': function,
                            'functionResponse': {'responseBody': responseBody_for_error}
                        }
                    }
                else:
                    return {
                        "statusCode": 400,
                        "body": json.dumps({'error': 'InvalidRequest', 'message': 'Invalid JSON in request body'}),
                        "headers": {"Content-Type": "application/json"}
                    }

        # Parse filtersJson string if present
        filters = None
        if filters_json_str:
            try:
                filters = json.loads(filters_json_str)
            except Exception as e:
                logger.error("Failed to parse filtersJson", context={'filtersJson': filters_json_str}, error=e)
                filters = None

        logger.info(f"🚀 Processing trade history request", 
                   context={
                       'requestId': request_id, 
                       'queryType': query_type, 
                       'timeFrame': time_frame,
                       'userId': user_id,
                       'hasFilters': filters is not None,
                       'isApiGateway': is_api_gateway,
                       'isBedrock': is_bedrock
                   })

        # --- Main Logic ---
        reporter = TradeHistoryReporter()
        result = reporter.getTradeHistory(query_type, time_frame, user_id, filters)

        # --- Response Formatting ---
        if is_bedrock:
            responseBody_for_success = {"TEXT": {"body": json.dumps(result, default=str)}}
            action_response = {
                'actionGroup': actionGroup,
                'function': function,
                'functionResponse': {'responseBody': responseBody_for_success}
            }
            final_response = {
                'messageVersion': messageVersion,
                'response': action_response
            }
            print(f"DEBUG: Final Lambda Bedrock success response: {json.dumps(final_response, indent=2)}")
            return final_response
        elif is_api_gateway:
            return {
                "statusCode": 200,
                "body": json.dumps(result),
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return result

    except Exception as e:
        logger.error(f"❌ Lambda execution failed", 
                    context={'requestId': event.get('requestId', 'unknown')}, 
                    error=e)
        # Error formatting for Bedrock
        analyzer = None
        try:
            analyzer = TradeHistoryReporter()
        except:
            pass
        error_details = {'error': 'InternalError', 'message': str(e)}
        error_type_str = query_type if 'query_type' in locals() and query_type is not None else 'unknown'
        if analyzer and hasattr(analyzer, '_format_error_response'):
            error_details = analyzer._format_error_response(error_type_str, str(e))
        responseBody_for_error = {"TEXT": {"body": json.dumps(error_details, default=str)}}
        if 'is_bedrock' in locals() and is_bedrock:
            error_action_response = {
                'actionGroup': actionGroup,
                'function': function,
                'functionResponse': {'responseBody': responseBody_for_error}
            }
            final_error_response = {
                'messageVersion': messageVersion,
                'response': error_action_response
            }
            print(f"DEBUG: Final Lambda Bedrock error response: {json.dumps(final_error_response, indent=2)}")
            return final_error_response
        elif 'is_api_gateway' in locals() and is_api_gateway:
            return {
                "statusCode": 500,
                "body": json.dumps(error_details),
                "headers": {"Content-Type": "application/json"}
            }
        else:
            return error_details


# For local testing and board demonstration
if __name__ == "__main__":
    # Test cases for board demonstration including filter functionality (filtersJson schema)
    testCases = [
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
            "filtersJson": json.dumps({
                "tickers": ["AAPL", "MSFT"],
                "tradeTypes": ["BUY"]
            }),
            "requestId": "board-demo-003"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "last 6 months",
            "userId": "mock_ic_user_1",
            "filtersJson": json.dumps({
                "priceRange": {"min": 100.0, "max": 300.0},
                "quantityRange": {"min": 10, "max": 50}
            }),
            "requestId": "board-demo-004"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "this year",
            "userId": "mock_ic_user_1",
            "filtersJson": json.dumps({
                "tickers": ["TSLA"],
                "tradeTypes": ["SELL"],
                "priceRange": {"min": 200.0},
                "dateRange": {"start": "2025-01-01", "end": "2025-06-30"}
            }),
            "requestId": "board-demo-005"
        },
        {
            "queryType": "allTrades",
            "timeFrame": "last month",
            "userId": "mock_ic_user_1",
            "filtersJson": "{\"tickers\": [\"TSLA\"], \"tradeTypes\": [\"BUY\"], \"priceRange\": {\"min\": 100.0, \"max\": 500.0}, \"quantityRange\": {\"min\": 10, \"max\": 100}, \"dateRange\": {\"start\": \"2025-06-01\", \"end\": \"2025-06-30\"}}",
            "requestId": "test-filtersjson-001"
        }
    ]
    
    print("🎯 AWS Chatbot Trade History with Filters - Board Demonstration")
    print("=" * 70)
    
    for i, testEvent in enumerate(testCases, 1):
        print(f"\n📊 Test Case {i}: {testEvent['queryType']} ({testEvent['timeFrame']})")
        # Print filtersJson for demonstration
        if testEvent.get('filtersJson'):
            print(f"🔍 filtersJson: {testEvent['filtersJson']}")
        print("-" * 50)
        
        result = lambda_handler(testEvent, None)
        
        if 'error' in result:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"✅ Success: {result.get('message', 'Trade history retrieved')}")
            perf = result.get('performance', {})
            print(f"⏱️  Execution Time: {perf.get('executionTime', 0)}s")
            trades = result.get('trades', [])
            summary = result.get('summary', {})
            print(f"📈 Trades Found: {len(trades)}")
            print(f"💰 Buy/Sell: {summary.get('buyTrades', 0)}/{summary.get('sellTrades', 0)}")
            if summary.get('filterSummary'):
                print(f"🔍 Filter Summary: {summary['filterSummary']}")
            print(f"🎯 Sample Trades:")
            for trade in trades[:3]:  # Show first 3 trades
                print(f"   {trade['date']}: {trade['type']} {trade['quantity']} {trade['ticker']} @ ${trade['price']}")
    
    print("\n" + "=" * 70)
    print("🚀 Board Demonstration Complete - Trade History Tool with Filters Ready!") 