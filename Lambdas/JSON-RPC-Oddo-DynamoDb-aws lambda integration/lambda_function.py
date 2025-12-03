import os
import json
import urllib.request
import ssl
import logging
import boto3
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ssl_context = ssl.create_default_context()
dynamodb = boto3.resource("dynamodb")


def safe_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except:
        return None


def json_rpc_call(url, method, params):
    """Safely perform RPC call and detect Odoo errors"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        raise Exception(f"HTTP error: {e}")

    result = json.loads(raw)

    if "error" in result:
        raise Exception(f"Odoo RPC Error: {result['error']}")

    return result["result"]


def flatten_order(order):
    partner = order.get("partner_id") or [None, None]

    return {
        "order_id": str(order.get("id")),
        "order_name": order.get("name"),
        "customer_id": partner[0],
        "customer_name": partner[1],
        "amount_total": order.get("amount_total"),
        "state": order.get("state"),
        "date_order": order.get("date_order")
    }


def lambda_handler(event, context):
    logger.info("Lambda started")

    # Shortcut test event
    if event.get("test", False):
        return {"statusCode": 200, "message": "Test OK"}

    required_env = [
        "ODOO_URL",
        "ODOO_DB",
        "ODOO_EMAIL",
        "ODOO_API_KEY",
        "ODDO_RESPONSE_TABLE"
    ]

    missing = [e for e in required_env if not os.environ.get(e)]
    if missing:
        return {"statusCode": 500, "error": f"Missing ENV vars: {missing}"}

    odoo_url = os.environ["ODOO_URL"].rstrip("/")
    odoo_db = os.environ["ODOO_DB"]
    odoo_email = os.environ["ODOO_EMAIL"]
    odoo_api_key = os.environ["ODOO_API_KEY"]
    table_name = os.environ["ODDO_RESPONSE_TABLE"]

    table = dynamodb.Table(table_name)
    rpc_url = f"{odoo_url}/jsonrpc"

    try:
        # 1. Authenticate
        uid = json_rpc_call(
            rpc_url,
            "call",
            {
                "service": "common",
                "method": "authenticate",
                "args": [odoo_db, odoo_email, odoo_api_key, {}]
            }
        )

        logger.info(f"Authenticated UID: {uid}")

        # 2. Fetch Orders
        records = json_rpc_call(
            rpc_url,
            "call",
            {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    odoo_db,
                    uid,
                    odoo_api_key,
                    "sale.order",
                    "search_read",
                    [],
                    {
                        "fields": [
                            "id",
                            "name",
                            "partner_id",
                            "amount_total",
                            "state",
                            "date_order"
                        ],
                        "order": "id desc",
                        "limit": 100
                    }
                ]
            }
        )

        logger.info(f"Fetched orders count: {len(records)}")

        flattened = []
        for order in records:
            try:
                data = flatten_order(order)
                data["response_status"] = "success"
                flattened.append(data)
            except Exception:
                flattened.append({
                    "order_id": str(order.get("id")),
                    "order_name": order.get("name"),
                    "response_status": "invalid_record"
                })

        # 3. Write to DynamoDB
        for row in flattened:
            try:
                item = {
                    "order_name": row["order_name"],  # PK String
                    "order_id": row["order_id"],      # SK String
                    "customer_id": str(row.get("customer_id")) if row.get("customer_id") else None,
                    "customer_name": row.get("customer_name"),
                    "amount_total": safe_decimal(row.get("amount_total")),
                    "state": row.get("state"),
                    "date_order": row.get("date_order"),
                    "response_status": row["response_status"],
                    "last_updated_at": datetime.utcnow().isoformat() + "Z"
                }
                table.put_item(Item=item)
            except Exception as dynamo_err:
                logger.error(f"DynamoDB error for order {row['order_name']}: {dynamo_err}")
                table.put_item(Item={
                    "order_name": row.get("order_name"),
                    "order_id": row.get("order_id"),
                    "response_status": "dynamo_error",
                    "last_updated_at": datetime.utcnow().isoformat() + "Z"
                })

        return {
            "statusCode": 200,
            "records": flattened
        }

    except Exception as e:
        logger.error("Fatal error", exc_info=True)
        return {
            "statusCode": 500,
            "error": str(e)
        }
