S3 → DynamoDB CSV Loader (Lambda)

This AWS Lambda function ingests CSV employee records, converts them into structured objects, and stores them in DynamoDB.
It supports three execution modes: Warmup, Test input, and S3-triggered ingestion.

Key Responsibilities

Reads CSV rows

Converts emp_id to a numeric partition key

Performs bulk inserts using DynamoDB batch_writer

Logs processing status, successes, and failures

Execution Modes
1. Warm-up / Pre-initialization

Used to keep the Lambda warm (for example, via CloudWatch).

Input:

{"warmup": true}


Returns immediately without processing data.

2. Test Mode (Manual Invocation)

Pass CSV-like rows directly when testing in the Lambda console:

{
  "test": true,
  "rows": [
    {"emp_id": "101", "name": "John", "dept": "IT"},
    {"emp_id": "102", "name": "Emma", "dept": "HR"}
  ]
}


No S3 required.
Useful for debugging or local proof-of-concept.

3. S3 Trigger Mode (Main)

Triggered by an S3 event when a .csv file is uploaded.

Flow:

Extract bucket and file key from the event

Download the CSV

Convert rows into Python dictionaries

Insert items into DynamoDB

Example event source:
S3 “Object Created” trigger (Put / Upload)

DynamoDB

Table name is supplied via environment variable:

DYNAMO_TABLE_NAME=*****


Partition Key must be:

emp_id (Number)


Every CSV row becomes a DynamoDB item.

Example saved item:

{ "emp_id": 101, "name": "John", "dept": "IT", ... }

CSV Input Format

CSV headers should match field names exactly (case-sensitive).

Example:

emp_id,name,dept,location
101,John,IT,Bangalore
102,Emma,HR,Mumbai

Processing Rules

emp_id

Required

Must be numeric

Converted to integer before storing

Other fields

Stored as-is from CSV

No transformation applied

Invalid rows

Missing or non-numeric emp_id are skipped

Logged and counted under failed rows

Logging

The Lambda logs:

Startup

Mode detected

DynamoDB writes

Warnings for invalid rows

This helps with debugging and monitoring data ingestion quality.

AWS Services Used
Service	Purpose
AWS Lambda	Ingestion and processing
S3	CSV storage and event trigger
DynamoDB	Employee records storage
Boto3	AWS SDK for S3/DynamoDB access
IAM Permissions (Minimum)

s3:GetObject

dynamodb:PutItem

dynamodb:BatchWriteItem

logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents

Return Format

The response includes counts for successful and failed rows:

{ "inserted": 125, "failed": 3 }

Testing Strategy

Use Test Mode for local validation

Upload sample CSVs to an S3 bucket

Validate DynamoDB writes

Monitor CloudWatch logs for skipped rows

Notes

No schema enforcement besides emp_id

All CSV columns are dynamically mapped

Batch writer optimizes throughput but does not retry individual items
