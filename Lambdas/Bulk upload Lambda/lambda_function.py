import os
import json
import boto3
import csv
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    logger.info("Lambda execution started")

    # Warm-up event
    if "warmup" in event:
        logger.warning("Warm-up event detected, skipping CSV processing")
        return {"status": "warmup_ok"}

    # Test mode — manual input rows
    if "test" in event:
        logger.info("Running TEST MODE with custom rows")
        rows = event.get("rows", [])
        return insert_rows(rows)

    # S3 Trigger mode
    try:
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
    except Exception as e:
        logger.error("Event is not a valid S3 trigger")
        logger.debug(json.dumps(event))
        raise e

    logger.info(f"Reading CSV from s3://{bucket}/{key}")

    # Read CSV from S3
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    csv_lines = obj["Body"].read().decode("utf-8").splitlines()
    reader = csv.DictReader(csv_lines)

    return insert_rows(list(reader))


def insert_rows(rows):
    success = 0
    failed = 0

    with table.batch_writer() as batch:
        for row in rows:
            raw_emp_id = row.get("emp_id")

            if not raw_emp_id:
                logger.warning(f"Missing emp_id. Skipping row: {row}")
                failed += 1
                continue

            # Convert emp_id to integer for DynamoDB number key
            try:
                row["emp_id"] = int(str(raw_emp_id).strip())
            except Exception:
                logger.error(f"emp_id must be numeric. Received: {raw_emp_id}")
                failed += 1
                continue

            try:
                logger.info(f"Writing item to DynamoDB: {row}")
                batch.put_item(Item=row)
                success += 1
            except ClientError as e:
                logger.error(f"Failed to insert item into DynamoDB: {row}")
                logger.exception(e)
                failed += 1

    logger.info(f"Insert completed. Success={success}, Failed={failed}")
    return {"inserted": success, "failed": failed}
