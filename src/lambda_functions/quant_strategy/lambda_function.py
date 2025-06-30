import json
from datetime import datetime
from logger import get_logger

logger = get_logger("QuantStrategyLambda")

def strategy_decision_tool(event):
    """
    Explains why a strategy did or did not take action at a specific time.
    Input: {"strategy_id": str, "timestamp": str}
    Output: {"action_taken": bool, "reason": str, "next_window": str}
    """
    strategy_id = event.get("strategy_id", "unknown")
    timestamp = event.get("timestamp", datetime.now().isoformat())
    # Stubbed logic for demonstration
    if strategy_id == "dyn_rebal":
        return {
            "action_taken": False,
            "reason": "Momentum below entry threshold; no signal triggered.",
            "next_window": "2025-06-14T11:00:00Z"
        }
    else:
        return {
            "action_taken": True,
            "reason": "Entry signal triggered; all conditions met.",
            "next_window": "2025-06-14T11:30:00Z"
        }

def strategy_metrics_tool(event):
    """
    Returns current metrics for a given strategy (e.g., AUM, return).
    Input: {"strategy_id": str, "metric": str}
    Output: {"aum": int, "currency": str, "as_of": str, "accounts": int}
    """
    strategy_id = event.get("strategy_id", "unknown")
    metric = event.get("metric", "aum")
    # Stubbed logic for demonstration
    if strategy_id == "rev_grid" and metric == "aum":
        return {
            "aum": 245000000,
            "currency": "THB",
            "as_of": "2025-06-14T11:45:00Z",
            "accounts": 12
        }
    else:
        return {
            "aum": 10000000,
            "currency": "THB",
            "as_of": datetime.now().isoformat(),
            "accounts": 1
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Quant Strategy Q&A
    Routes to the correct tool based on 'action' in the event.
    """
    logger.info("Received event", context=event)
    action = event.get("action")
    try:
        if action == "decision":
            result = strategy_decision_tool(event)
            status_code = 200
        elif action == "metrics":
            result = strategy_metrics_tool(event)
            status_code = 200
        else:
            result = {"error": "Invalid action. Use 'decision' or 'metrics'."}
            status_code = 400
        response = {
            "statusCode": status_code,
            "body": json.dumps(result),
            "headers": {"Content-Type": "application/json"}
        }
        logger.info("Lambda execution successful", context=response)
        return response
    except Exception as e:
        logger.error("Lambda execution failed", context=event, error=e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        } 