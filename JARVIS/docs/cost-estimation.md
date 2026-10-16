# JARVIS AI — AWS Cost Estimation & Resource Optimization

## 1. Zero-Cost Local Development Mode
JARVIS AI is specifically architected with a **dual-mode persistence engine**. In local development mode, all cloud operations (DynamoDB tables, Cognito authentication, S3 artifacts) are fully emulated via local SQLite (`data/cloud_emulation.db`) and local folders.
- **Local Dev Cost: $0.00 / month**

---

## 2. Cloud Production Architecture Monthly Cost Breakdown

The following estimates assume typical personal assistant usage (~1,000 tasks/month):

| AWS Service | Usage Metric | Unit Rate | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Amazon Bedrock (Claude 3 Sonnet)** | 1,000 requests (~500k input tokens, 200k output tokens) | Input: $0.003 / 1k<br>Output: $0.015 / 1k | **$4.50** |
| **Amazon Cognito** | 1 user (up to 50,000 MAU free tier) | Free Tier | **$0.00** |
| **AWS Lambda** | 1,000 invocations @ 512MB RAM, 1s duration | 1M free requests/month | **$0.00** |
| **Amazon API Gateway (HTTP API v2)** | 10,000 API calls | $1.00 / million calls | **$0.01** |
| **Amazon DynamoDB (Pay-Per-Request)** | 5,000 read/write units | 25GB free tier, $1.25/million writes | **$0.02** |
| **Amazon S3** | 200 MB artifacts / month | 5GB free tier | **$0.00** |
| **Total Estimated Cloud Cost** | — | — | **~$4.53 / month** |

---

## 3. Cost Control Guardrails
1. **Fallback to Local Semantic Planner**: When complex multi-step reasoning is not required, common patterns (playing music, searching YouTube, running Python assignments) execute locally without incurring Bedrock API charges.
2. **DynamoDB On-Demand (PAY_PER_REQUEST)**: Prevents idle provisioning fees associated with provisioned throughput.
3. **HTTP API v2 vs REST API**: Saves over 70% compared to traditional API Gateway REST APIs ($1.00/million vs $3.50/million).
4. **S3 Lifecycle Policies**: Auto-expire temporary task artifacts after 30 days.
