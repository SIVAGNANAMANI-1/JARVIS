# JARVIS AI — AWS Cloud Infrastructure Deployment Guide

## 1. Overview
The JARVIS cloud backend is provisioned using **AWS Serverless Application Model (SAM)** via the declaration in `infrastructure/aws-sam/template.yaml`.

The cloud stack provides:
1. **Amazon Cognito**: User Pool and User Pool Client for password and SRP-based mobile/desktop authentication.
2. **Amazon DynamoDB**: Pay-per-request tables:
   - `JarvisTasks-{Environment}`: Partitioned by `user_id` with GSI on `target_device_id`.
   - `JarvisDevices-{Environment}`: Partitioned by `user_id` and `device_id`.
   - `JarvisMemory-{Environment}`: Partitioned by `user_id` and `memory_id`.
3. **Amazon S3**: Bucket `jarvis-artifacts-store-{AccountId}` with default AES256 server-side encryption and public access blocking.
4. **Amazon Bedrock IAM Role**: Grants `bedrock:InvokeModel` permissions for foundation model reasoning.
5. **Amazon API Gateway HTTP API v2**: With JWT authorizer pointing to Cognito.

---

## 2. Environment Variables Configuration

Copy `.env.example` to `.env` in production:

```bash
# AWS Region & Environment
AWS_REGION=us-east-1
ENVIRONMENT=dev

# Amazon Cognito
COGNITO_USER_POOL_ID=us-east-1_examplePool
COGNITO_APP_CLIENT_ID=exampleAppClient12345

# DynamoDB Tables
DYNAMODB_TASKS_TABLE=JarvisTasks-dev
DYNAMODB_DEVICES_TABLE=JarvisDevices-dev
DYNAMODB_MEMORY_TABLE=JarvisMemory-dev

# S3 Artifacts
S3_ARTIFACTS_BUCKET=jarvis-artifacts-store-dev

# Amazon Bedrock Model
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

---

## 3. Deployment Steps

Ensure AWS CLI and SAM CLI are installed on the deployment machine and configured with `aws configure`.

### Step 1: Validate SAM Template
```bash
sam validate -t infrastructure/aws-sam/template.yaml
```

### Step 2: Build the Serverless Artifacts
```bash
sam build -t infrastructure/aws-sam/template.yaml
```

### Step 3: Deploy Guided Stack
```bash
sam deploy --guided \
  --stack-name jarvis-ai-backend-dev \
  --parameter-overrides Environment=dev AwsRegion=us-east-1 \
  --capabilities CAPABILITY_IAM
```

---

## 4. Teardown / Cleanup
To destroy cloud resources and avoid ongoing billing:
```bash
sam delete --stack-name jarvis-ai-backend-dev
```
