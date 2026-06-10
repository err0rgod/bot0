# Deployment Guide: ZeroDay Daily

This document outlines the process for updating the codebase and deploying changes to the AWS Lambda environment.

## Prerequisites

- **AWS CLI**: Installed and configured with `err0rgod` credentials.
- **Docker Desktop**: Must be running and accessible.
- **Python 3.10**: For local testing.

## 1. Local Development & Testing

Before deploying, always verify your changes locally.

### Test Database Connection
```powershell
python scratch/check_db_conn.py
```

### Verify Subscriber List
You can use a scratch script to ensure the logic picks up the correct users from DynamoDB.

---

## 2. Deployment to AWS Lambda (Docker)

The `zeroday-scraper` Lambda function runs as a container image. To update it, you must build, tag, and push a new image to Amazon ECR.

### Step 1: Authenticate with ECR
Run this to allow Docker to push images to your private AWS registry.
```powershell
$password = aws ecr get-login-password --region ap-south-2
docker login --username AWS --password $password 339087217625.dkr.ecr.ap-south-2.amazonaws.com
```

### Step 2: Build the Image
Use the following command to ensure the image is compatible with Lambda (amd64 architecture and V2 manifest format).
```powershell
docker build --platform linux/amd64 --provenance=false -t zeroday-scraper .
```

### Step 3: Tag and Push
```powershell
# Tag for ECR
docker tag zeroday-scraper:latest 339087217625.dkr.ecr.ap-south-2.amazonaws.com/zeroday-scraper:latest

# Push to ECR
docker push 339087217625.dkr.ecr.ap-south-2.amazonaws.com/zeroday-scraper:latest
```

### Step 4: Update Lambda Function
Notify Lambda to pull the latest image.
```powershell
aws lambda update-function-code `
    --function-name zeroday-scraper `
    --image-uri 339087217625.dkr.ecr.ap-south-2.amazonaws.com/zeroday-scraper:latest `
    --region ap-south-2
```

---

## 3. Configuration (Environment Variables)

If you change table names or API keys, update the Lambda environment variables via the AWS Console or CLI:

- `DYNAMODB_TABLE_NAME`: `zeroday-subscribers`
- `AWS_REGION`: `ap-south-2`
- `RESEND_API_KEY`: Your Resend API token.
- `S3_BUCKET_NAME`: `zeroday-scraped-content-prod-339087217625-ap-south-2-an`

## 4. Troubleshooting

- **400 Bad Request during login**: This is usually a PowerShell pipe issue. Use the `$password` variable method shown in Step 1.
- **403 Forbidden during push**: Ensure your Docker login hasn't expired (tokens last 12 hours).
- **Unsupported Media Type**: Ensure you build with `--provenance=false` to avoid OCI index issues in Lambda.
