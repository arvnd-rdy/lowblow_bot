# Loblaw Careers Job Monitor

## 🚀 What is this?
A serverless bot that monitors the Loblaw careers website for new part-time job postings in a specific location and sends instant Telegram notifications when new jobs appear.

## 🧐 Why did I build this?
Searching for part-time jobs on the Loblaw careers site is tedious—you can't stay glued to the website 24/7, refreshing for new postings. I wanted a bot that checks the site every 5 minutes and notifies me on Telegram as soon as a new job is posted.

But running a script on my laptop 24/7 isn't practical. So, I deployed it to the cloud using AWS Lambda and S3, which are (practically) free for this use case, since the resource usage is minimal.

## ✨ Features
- Monitors Loblaw careers for new part-time jobs in a chosen location
- Sends Telegram notifications instantly when new jobs are posted
- Runs automatically every 5 minutes (no manual refresh needed)
- Serverless: no need to keep your computer running
- Uses AWS Lambda (compute) and S3 (cache storage)

## 🛠️ How it works
- Scrapes the Loblaw careers site for job postings
- Compares with previous results (stored in S3)
- Sends a Telegram message if new jobs are found
- Runs every 5 minutes via AWS EventBridge trigger

## ☁️ Cloud Deployment
This project is designed to run on AWS Lambda + S3 for reliability and zero maintenance. All deployment steps are in the [AWS_DEPLOYMENT_GUIDE.md](./AWS_DEPLOYMENT_GUIDE.md).

## 📦 Project Structure
- `lambda_function.py` — Lambda-compatible Python script
- `requirements-lambda.txt` — Dependencies for Lambda
- `AWS_DEPLOYMENT_GUIDE.md` — Step-by-step AWS deployment guide

## 🚀 Quick Start
1. Clone this repo
2. Follow the instructions in [AWS_DEPLOYMENT_GUIDE.md](./AWS_DEPLOYMENT_GUIDE.md)
3. Set your Telegram bot token, chat ID, and S3 bucket as Lambda environment variables
4. Enjoy hands-free job monitoring!

## 📝 License
MIT 