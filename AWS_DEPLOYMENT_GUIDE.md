# AWS Lambda Deployment Guide

Deploy your Loblaw Careers Job Monitor to AWS Lambda for free, using the AWS Free Tier. This guide walks you through every step.

## Prerequisites
- AWS account (free tier eligible)
- Telegram bot and chat ID (for notifications)
- AWS CLI (optional, for advanced users)

## Step 1: Create an S3 Bucket
1. Go to the AWS S3 Console
2. Click "Create bucket"
3. Choose a unique name (e.g., `loblaw-job-monitor-cache-xyz`)
4. Select your region
5. Click "Create bucket"

## Step 2: Prepare Lambda Deployment Package
1. Clone this repository
2. Open a terminal and navigate to the project directory
3. Create a new folder for packaging:
   ```
   mkdir lambda-package
   cd lambda-package
   ```
4. Copy the Lambda function and requirements file:
   ```
   cp ../lambda_function.py .
   cp ../requirements-lambda.txt .
   ```
5. Install dependencies into this folder:
   ```
   pip install -r requirements-lambda.txt -t .
   ```
6. Zip the contents (not the folder itself):
   - On Linux/macOS:
     ```
     zip -r ../lambda-deployment.zip .
     ```
   - On Windows PowerShell:
     ```
     Compress-Archive -Path * -DestinationPath ..\lambda-deployment.zip
     ```

## Step 3: Create the Lambda Function
1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Name your function (e.g., `loblaw-job-monitor`)
5. Runtime: Python 3.12 (or latest supported)
6. Click "Create function"
7. Upload your `lambda-deployment.zip` in the Code section

## Step 4: Set Environment Variables
In the Lambda configuration, add these environment variables:
- `TELEGRAM_BOT_TOKEN` — your Telegram bot token
- `TELEGRAM_CHAT_ID` — your Telegram chat ID
- `S3_BUCKET_NAME` — your S3 bucket name

## Step 5: Set Up IAM Permissions
1. Go to the Lambda function's Permissions tab
2. Click the execution role name
3. Add an inline policy with this JSON (replace the bucket name):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::loblaw-job-monitor-cache-xyz",
           "arn:aws:s3:::loblaw-job-monitor-cache-xyz/*"
         ]
       }
     ]
   }
   ```
4. Save the policy

## Step 6: Add EventBridge Trigger
1. In the Lambda console, go to the Triggers section
2. Click "Add trigger"
3. Select "EventBridge (CloudWatch Events)"
4. Choose "Create a new rule"
5. Rule type: Schedule expression
6. Schedule expression: `rate(5 minutes)`
7. Click "Add"

## Step 7: Test and Monitor
- Use the "Test" button in Lambda to run manually
- Check CloudWatch Logs for output
- Monitor your Telegram for notifications
- The function will now run automatically every 5 minutes

## Cost
- AWS Free Tier covers all resources for this use case
- Estimated monthly cost: $0 (within free tier limits)

## Troubleshooting
- **S3 Access Denied:** Check IAM policy and bucket name
- **No Telegram messages:** Double-check bot token and chat ID
- **Timeouts:** Increase Lambda timeout if needed

---

Enjoy hands-free job monitoring in the cloud! 