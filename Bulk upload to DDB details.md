📥 S3 → DynamoDB CSV Loader (Lambda)

This AWS Lambda function ingests CSV employee records, converts them into structured objects, and stores them in DynamoDB.
It supports three execution modes: Warmup, Test input, and S3-triggered ingestion.

🔑 Key Responsibilities

✔️ Reads CSV rows
✔️ Converts emp_id to a numeric PK
✔️ Performs bulk inserts using DynamoDB batch_writer
✔️ Logs processing status, successes, and failures

🚀 Execution Modes
1️⃣ Warm-up / Pre-initialization

Used to keep the Lambda “hot” (e.g., via CloudWatch).

{"warmup": true}


🔹 Returns immediately without processing data.

2️⃣ Test Mode (Manual Invocation)

Pass CSV-like rows directly when testing in Lambda console:

{
  "test": true,
  "rows": [
    {"emp_id": "101", "name": "John", "dept": "IT"},
    {"emp_id": "102", "name": "Emma", "dept": "HR"}
  ]
}


🔹 No S3 required
🔹 Useful for debugging or local PoC

3️⃣ S3 Trigger Mode (Main)

Triggered by an S3 event when a .csv is uploaded.

Flow:

Extract bucket and file key from the event

Download the CSV

Convert rows → Python dicts

Insert items in DynamoDB

Example event source:

S3 Object Created trigger (Put / Upload)

🗄️ DynamoDB

Table name supplied via environment variable:

DYNAMO_TABLE_NAME=*****


Partition Key must be:

emp_id (Number)

Every CSV row becomes a DynamoDB item.

Example saved item:

{
  "emp_id": 101,
  "name": "John",
  "dept": "IT",
  ...
}

📦 CSV Input Format

CSV headers should match field names (case-sensitive).

Example:

emp_id,name,dept,location
101,John,IT,Bangalore
102,Emma,HR,Mumbai

🧾 Processing Rules
✔️ emp_id

Required

Must be a numeric value

Converted to int before storing

✔️ Other Fields

Stored as-is from CSV

No transformation applied

❌ Invalid Rows

Missing or non-numeric emp_id → skipped

Logged and counted in failed

🔧 Logging

The Lambda logs:

Startup

Trigger mode detected

DynamoDB writes

Warnings for invalid rows

Useful for debugging and tracking ingestion quality.

🛠️ AWS Services Used
Service	Purpose
AWS Lambda	Ingestion + processing
S3	CSV storage & event trigger
DynamoDB	Employee records storage
Boto3	AWS SDK to interact with S3/DynamoDB
🔐 IAM Permissions (Minimum)

s3:GetObject

dynamodb:PutItem

dynamodb:BatchWriteItem

logs:CreateLogGroup

logs:CreateLogStream

logs:PutLogEvents

🔁 Return Format

The response includes success & failure counts:

{
  "inserted": 125,
  "failed": 3
}

🧪 Testing Strategy

✔️ Use Test Mode for local validation
✔️ Upload sample CSVs to S3 buckets
✔️ Validate DynamoDB writes
✔️ Monitor CloudWatch logs for skipped rows

💡 Notes

No schema enforcement besides emp_id.

All CSV columns are dynamically mapped.

Batch writer optimizes write throughput but does not retry per item.