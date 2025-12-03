# MYpersonalProjects
Personal Projects 

Project 1:
Odoo(CRM tool) → AWS Lambda → DynamoDB Order Sync (Summary)

This AWS Lambda function integrates with an Odoo ERP backend using JSON-RPC, retrieves sale order records, normalizes the data, and stores the results in an AWS DynamoDB table for further processing. It can be then further used for any other applications which can interacts with DynamOdb and get the records from it.
All details of this project are in the other readme.MD file inside the lambda folder(please find there)


Project 2:
This AWS Lambda function ingests CSV employee records, converts them into structured objects, and stores them in DynamoDB.
It supports three execution modes: Warmup, Test input, and S3-triggered ingestion.
All details of this project are in the other readme.MD file inside lambda folder(please find it there)
