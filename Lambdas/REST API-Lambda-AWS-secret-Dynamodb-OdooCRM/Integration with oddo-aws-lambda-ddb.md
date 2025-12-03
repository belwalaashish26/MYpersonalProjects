Project-3

AWS Lambda → Odoo Online ERP Integration using  (REST + AWS seret Manager =DynamoDB)

This Lambda function integrates with an Odoo Online SaaS database using Odoo's session-based REST API. It retrieves sale order records and stores them in an AWS DynamoDB table. Unlike XML-RPC or JSON-RPC, which are not fully supported on Odoo Online, this solution uses authentication and API access through browser-like endpoints.

Key Features

Credentials are stored in AWS Secrets Manager, not environment variables.

Authentication is performed using the Odoo REST endpoint /web/session/authenticate.

A session cookie is automatically managed and reused.

Model access is done through /web/dataset/call_kw.

Fetched sale order records are normalized and stored in DynamoDB.

IAM policies restrict access to only required AWS services.

Architecture Flow

Lambda starts.

Reads Odoo credentials from AWS Secrets Manager.

Authenticates with Odoo using session authenticate.

Receives a session cookie and UID.

Queries sale orders via search_read.

Writes records into DynamoDB.

Returns the retrieved data.

Security Considerations

Sensitive values (URL, DB name, email, password) are stored in Secrets Manager.

No Odoo password or API key in Lambda environment variables.

IAM permissions are limited to:

secretsmanager:GetSecretValue

dynamodb:PutItem

Required AWS Resources
AWS Secrets Manager

Secret JSON format:

{
  "ODOO_URL": "https://example.odoo.com",
  "ODOO_DB": "DatabaseName",
  "ODOO_EMAIL": "user@example.com",
  "ODOO_PASSWORD": "your_odoo_password"
}

DynamoDB Table

Example

Table name: OddoResponseUpdateTable
Partition Key: order_name (string)
Sort Key: order_id (string)

Required IAM Policies
Secrets Manager Access
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:<region>:<account>:secret:<secret_name>"
}

DynamoDB Write Access
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:UpdateItem"
  ],
  "Resource": "arn:aws:dynamodb:<region>:<account>:table/<TableName>"
}

Why /web/session/authenticate Instead of /jsonrpc

Odoo Online does not allow unauthenticated JSON-RPC requests.
It returns static pages or 404 errors when accessed from cloud services.
Odoo Online expects authenticated browser-style requests, which must include a valid session cookie.

The correct approach is:

Authenticate using /web/session/authenticate

Use the returned session cookie to make API model calls

Perform operations using /web/dataset/call_kw

API Endpoints Used
Authentication
POST /web/session/authenticate

Model Query
POST /web/dataset/call_kw


Example request body for retrieving sale orders:

{
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

DynamoDB Record Format

Each stored record includes:

order_name

order_id

customer_id

customer_name

amount_total

state

date_order

response_status

last_updated_at

Why This Approach Works

Odoo Online blocks JSON-RPC without session context.

Password-based session authentication is supported.

The returned cookie behaves like a browser session.

call_kw is the official Odoo method for model manipulation.

Possible Extensions

Pagination using offset and limit

Sync of sale.order.line items

Sync of customer records (res.partner)

Customer creation

Sale order creation from external systems

Deployment using AWS SAM or Terraform