# MYpersonalProjects
Personal Projects 

**Project 1:**
Odoo(CRM tool) → AWS Lambda → DynamoDB Order Sync (Summary)

This AWS Lambda function integrates with an Odoo ERP backend using JSON-RPC, retrieves sale order records, normalizes the data, and stores the results in an AWS DynamoDB table for further processing. It can be then further used for any other applications which can interacts with DynamOdb and get the records from it.
All details of this project are in the other readme.MD file inside the lambda folder(please find there)
*****************************************************************************************************************************************************

**Project 2:**
This AWS Lambda function ingests CSV employee records, converts them into structured objects, and stores them in DynamoDB.
It supports three execution modes: Warmup, Test input, and S3-triggered ingestion.
All details of this project are in the other readme.MD file inside lambda folder(please find it there)
*****************************************************************************************************************************************************

**Project 3:**
AWS Lambda → Odoo Online ERP Integration (REST +AWS secret Manager + DynamoDB)

This Lambda function integrates with an Odoo Online SaaS database using Odoo's session-based REST API. It retrieves sale order records and stores them in an AWS DynamoDB table. Unlike XML-RPC or JSON-RPC, which are not fully supported on Odoo Online, this solution uses authentication and API access through browser-like endpoints.

**Key Features**

Credentials are stored in AWS Secrets Manager, not environment variables.

Authentication is performed using the Odoo REST endpoint /web/session/authenticate.

A session cookie is automatically managed and reused.

Model access is done through /web/dataset/call_kw.

Fetched sale order records are normalized and stored in DynamoDB.

IAM policies restrict access to only required AWS services.
