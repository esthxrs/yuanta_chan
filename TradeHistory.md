# Quant Trade History Query Lambda – PRD

## Overview

The **Quant Trade History Query Tool** is an AWS Lambda function (written in Python) that provides comprehensive trade history insights for the Quant platform. It enables an AWS Bedrock Agent (chatbot) to answer user questions such as *"What are all my trades this year?"* by retrieving and filtering the user's trade data, and summarizing key metrics. The function applies realistic constraints and validation to the query parameters, ensuring the results are credible.

This Lambda is deployed using AWS CDK (Infrastructure as Code) and integrates with the Bedrock Agent via a YAML-defined interface. The agent's NLP component interprets natural language questions and maps them to a **predefined query type** with parameters, which are passed to the Lambda in a structured format (JSON event). Currently, the system uses **mocked trade data** for demonstration purposes, so no live database integration is required. Performance is not a primary concern at this stage, but the function includes logging and metrics to monitor its behavior.

> **Note:** Due to AWS Action Group limitations, the function now accepts all filter options as a single JSON string parameter called `filtersJson`.

## Key Features

### Supported Query Type

- **Trade History Query (**``**)** – Retrieves the user's trade history for a specified timeframe, with optional filters. *(Future expansions may introduce additional query types, such as a dedicated query for trade frequency or portfolio summaries.)*

### Advanced Filtering

- **Ticker Filtering** – Filter results by specific stock symbols (e.g. AAPL, MSFT).
- **Trade Type Filtering** – Filter by BUY or SELL transactions.
- **Price Range Filtering** – Limit trades to a specified price range.
- **Quantity Range Filtering** – Filter by number of shares.
- **Date Range Filtering** – Constrain trades to specific dates.

### Time Frame Support

- **"this year"** – Year-to-date (Jan 1 to today).
- **"last month"** – Previous calendar month.
- **"last quarter"** – Last 3-month period.
- **"last 6 months"** – Last 180 days.

### Summary Statistics

- **Total Trades**
- **Buy vs Sell Count**
- **Unique Tickers**
- **Total Volume**
- **Filter Summary**
- **Effective Date Range**

### Robust Validation & Error Handling

- Validates tickers, types, ranges, and date formats.
- Returns clear error messages for unsupported or invalid queries.
- Structured logging with execution metadata.

## Input Schema

```json
{
  "queryType": "allTrades",
  "timeFrame": "this year",
  "userId": "mock_ic_user_1",
  "filtersJson": "{\"tickers\":[\"AAPL\",\"MSFT\"],\"tradeTypes\":[\"BUY\"],\"priceRange\":{\"min\":100.0,\"max\":500.0},\"quantityRange\":{\"min\":10,\"max\":100},\"dateRange\":{\"start\":\"2025-01-01\",\"end\":\"2025-06-30\"}}",
  "requestId": "req-1234567890"
}
```

YAML (Bedrock Agent Input):

```yaml
action: QuantTradeHistoryTool
action_input:
  queryType: "allTrades"
  timeFrame: "this year"
  userId: "mock_ic_user_1"
  filtersJson: '{"tickers": ["AAPL", "MSFT"], "tradeTypes": ["BUY"], "priceRange": {"min": 100.0, "max": 500.0}, "quantityRange": {"min": 10, "max": 100}, "dateRange": {"start": "2025-01-01", "end": "2025-06-30"}}'
```

## Output Schema

```json
{
  "queryType": "allTrades",
  "timeFrame": "last quarter",
  "userId": "mock_ic_user_1",
  "filters": {
    "tickers": ["AAPL", "MSFT"],
    "tradeTypes": ["BUY"]
  },
  "trades": [
    {
      "date": "2025-01-15",
      "ticker": "AAPL",
      "type": "BUY",
      "quantity": 25,
      "price": 175.50,
      "totalValue": 4387.50,
      "tradeId": "TRADE_20250115_1234"
    }
  ],
  "summary": {
    "totalTrades": 1,
    "buyTrades": 1,
    "sellTrades": 0,
    "uniqueTickers": 1,
    "totalVolume": 25,
    "filterSummary": "Tickers: AAPL, MSFT; Trade Types: BUY",
    "dateRange": {
      "start": "2025-01-01",
      "end": "2025-03-31"
    }
  },
  "message": "Successfully retrieved 1 filtered trades for last quarter.",
  "performance": {
    "executionTime": 0.045,
    "queryType": "allTrades",
    "timeFrame": "last quarter",
    "recordsReturned": 1,
    "filtersApplied": true
  }
}
```

## Error Handling

```json
{
  "error": "InvalidFilters",
  "message": "Filter validation failed: Invalid tickers: ['INVALID']",
  "queryType": "allTrades",
  "timeFrame": "this year",
  "userId": "mock_ic_user_1",
  "filtersJson": "{\"tickers\":[\"INVALID\"]}",
  "performance": {
    "executionTime": 0.002,
    "status": "Failed"
  },
  "timestamp": "2025-01-15T10:30:45.123Z"
}
```

## Supported Tickers

- AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, NFLX
- JPM, JNJ, PG, V, UNH, HD, DIS, PYPL, ADBE, CRM

## Validation Rules

- Tickers must be valid and supported.
- Trade types must be "BUY" or "SELL".
- Price/quantity ranges must be numeric and min ≤ max.
- Date ranges must be YYYY-MM-DD and start ≤ end.
- All filter options must be passed as a JSON string in the `filtersJson` parameter.

## Performance

- <2 seconds response time
- 5–15 trades per request (mocked)
- CloudWatch structured logging
- Execution metadata returned in output

## Use Cases

1. *"What are all my trades this year?"* → Basic query
2. *"Show me AAPL trades from last month."* → Ticker + timeframe filter
3. *"What were my BUY trades over $100 this quarter?"* → Type + price filter
4. *"How often do I buy and sell?"* → Agent interprets count summary from Lambda

## Deployment

- AWS Lambda (Python)
- Infrastructure-as-Code via AWS CDK
- YAML format interface with Bedrock Agent
- Ready for extension to real-time data backend

## Status

✅ Demo version complete with mock data and filtering 🚧 Future: real data backend, queryType expansion, performance tuning
