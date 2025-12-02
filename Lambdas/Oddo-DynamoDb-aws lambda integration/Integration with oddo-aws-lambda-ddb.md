# MYpersonalProjects
Personal Projects 

Project 1:
Odoo(CRM tool) → AWS Lambda → DynamoDB Order Sync (Summary)

This AWS Lambda function integrates with an Odoo ERP backend using JSON-RPC, retrieves sale order records, normalizes the data, and stores the results in an AWS DynamoDB table for further processing. It can be then further used for any other applications which can interacts with DynamOdb and get the records from it.

🚀Overview

The Lambda performs the following high-level steps:

Authenticate to Odoo

Fetch up to last 100 sale orders

Flatten/normalize the Odoo order data

Store each record in DynamoDB

Record a status of the sync for each order

Return the processed orders list as API response

🧠 Key Concepts
🔹 Odoo RPC (JSON-RPC 2.0)

The function does not use a REST API.
It calls a remote method on the Odoo server using JSON-RPC:

“Execute the method search_read on the Odoo model sale.order.”

This allows direct access to Odoo ORM logic.

🔹 DynamoDB Storage Strategy

Each order is written individually with:

Partition Key (order_name) — String

Sort Key (order_id) — String

The record includes metadata fields such as sync status and timestamp.

🏗️ Process Flow
1. Load environment variables

The Lambda retrieves connection parameters from environment variables:

ODOO_URL = *
ODOO_DB = *
ODOO_EMAIL = *
ODOO_API_KEY = *
ODDO_RESPONSE_TABLE = *


⚠️ Sensitive values are never hardcoded.

2. Authenticate with Odoo

The function calls the authenticate RPC method to obtain a user ID (uid).

If authentication fails → the process stops.

3. Fetch sale orders

Using Odoo search_read RPC:

Query the latest orders

Return up to 100 results sorted by ID descending

Request specific fields only

This avoids large payloads and improves performance.

4. Normalize order objects

Odoo returns nested fields (e.g., partner info as an array).

The function:

Extracts user-friendly order data

Converts IDs to strings

Removes irrelevant metadata

5. Store each record in DynamoDB

Each normalized order record is saved individually with:

PK: order_name

SK: order_id

Flattened order attributes

Sync metadata

A response status based on the order processing result

No static response codes are used.

6. Error handling

The function captures and categorizes errors:

odoo_error — RPC failure

invalid_record — missing/incorrect data shape

dynamo_error — storage write issue

This allows safe logging and post-processing.

7. Return structured result

The Lambda returns:

{
  statusCode: 200,
  records: [ ...flattened order list... ]
}

🛡️ Security & Good Practices

✔️ No credentials in code
✔️ Data types converted safely (especially floats → Decimal)
✔️ RPC errors reported clearly
✔️ DynamoDB writes in a controlled manner
✔️ Supportable & maintainable workflow structure

📌 Dependencies

boto3 — DynamoDB access

urllib.request — RPC call transport

decimal.Decimal — safe numeric storage
