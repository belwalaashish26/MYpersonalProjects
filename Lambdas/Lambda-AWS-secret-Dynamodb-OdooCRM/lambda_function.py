import os
import json
import urllib.request
import urllib.error
import ssl
import logging
import boto3
from datetime import datetime
from decimal import Decimal
from http import cookiejar
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ssl_context = ssl.create_default_context()
dynamodb = boto3.resource("dynamodb")
secrets_client = boto3.client("secretsmanager")

cj = cookiejar.CookieJar()

_op_cache = None


def safe_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def load_secret():
    global _op_cache

    if _op_cache:
        return _op_cache

    secret_id = os.environ.get("ODOO_SECRET_ARN")
    if not secret_id:
        raise Exception("Missing ODOO_SECRET_ARN")

    resp = secrets_client.get_secret_value(SecretId=secret_id)

    if "SecretString" in resp:
        data = json.loads(resp["SecretString"])
    else:
        data = json.loads(resp["SecretBinary"].decode())

    required = ["ODOO_URL", "ODOO_DB", "ODOO_EMAIL", "ODOO_PASSWORD"]
    missing = [x for x in required if x not in data]
    if missing:
        raise Exception(f"Secret missing keys: {missing}")

    _op_cache = data
    return data


def http_post(url, payload, headers=None):
    headers = headers or {}
    headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj)
    )

    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        logger.error(f"Odoo HTTPError {e.code}: {err_body}")
        raise
    except Exception as e:
        logger.error("HTTP call failed", exc_info=True)
        raise


def lambda_handler(event, context):
    try:
        cfg = load_secret()

        odoo_url = cfg["ODOO_URL"].rstrip("/")
        db = cfg["ODOO_DB"]
        email = cfg["ODOO_EMAIL"]
        pwd = cfg["ODOO_PASSWORD"]

        table_name = os.environ["ODDO_RESPONSE_TABLE"]
        table = dynamodb.Table(table_name)

        # ----------------------------------
        # Step 1 — Authenticate
        # ----------------------------------
        login_url = f"{odoo_url}/web/session/authenticate"
        logger.info(f"Authenticating to {login_url}")

        login_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "login": email,
                "password": pwd,
                "db": db
            }
        }

        auth = http_post(login_url, login_payload)

        session = auth.get("result", {})
        if not session.get("uid"):
            raise Exception("Authentication failed: No UID returned")

        logger.info(f"Authenticated UID: {session['uid']}")

        # ----------------------------------
        # Step 2 — Call sale.order via call_kw
        # ----------------------------------
        rpc_url = f"{odoo_url}/web/dataset/call_kw"
        logger.info(f"Fetching sale.order from {rpc_url}")

        rpc_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "sale.order",
                "method": "search_read",
                "args": [],
                "kwargs": {
                    "fields": [
                        "id",
                        "name",
                        "partner_id",
                        "amount_total",
                        "state",
                        "date_order"
                    ],
                    "limit": 100,
                    "order": "id desc"
                }
            }
        }

        records = http_post(rpc_url, rpc_payload)

        orders = records.get("result", [])
        logger.info(f"Fetched {len(orders)} orders")

        # ----------------------------------
        # Step 3 — Save to DynamoDB
        # ----------------------------------
        for rec in orders:
            item = {
                "order_name": rec.get("name"),
                "order_id": str(rec.get("id")),
                "customer_id": str(rec.get("partner_id")[0]) if rec.get("partner_id") else None,
                "customer_name": rec.get("partner_id")[1] if rec.get("partner_id") else None,
                "amount_total": safe_decimal(rec.get("amount_total")),
                "state": rec.get("state"),
                "date_order": rec.get("date_order"),
                "response_status": "success",
                "last_updated_at": datetime.utcnow().isoformat() + "Z"
            }
            table.put_item(Item=item)

        return {
            "statusCode": 200,
            "records": orders
        }

    except Exception as e:
        logger.error("Fatal error", exc_info=True)
        return {
            "statusCode": 500,
            "error": str(e)
        }
