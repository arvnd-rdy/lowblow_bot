import requests
import time
import json
import os
import boto3
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS S3 client for storing cache
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'loblaw-job-monitor-cache')
CACHE_FILE_KEY = 'loblaw_windsor_jobs.json'

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# The webpage to monitor
URL = "https://careers.loblaw.ca/jobs?location_name=Windsor%2C%20ON%2C%20Canada&location_type=2&filter%5Bemployment_type%5D%5B0%5D=Part%20Time"

def send_telegram_message(message):
    """Send notification to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Telegram notification sent!")
        else:
            print(f"❌ Failed to send notification: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def extract_jobs_from_page(url):
    """Extract all job listings from the page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all job cards
        job_cards = soup.find_all('li', {'class': 'results-list__item', 'data-testid': 'jobs-list-only_jobs-list_item'})
        
        jobs = {}
        
        for card in job_cards:
            try:
                # Extract job title and link
                title_elem = card.find('a', class_='results-list__item-title--link')
                if not title_elem:
                    continue
                
                job_title = title_elem.text.strip()
                job_link = title_elem.get('href', '')
                if job_link and not job_link.startswith('http'):
                    job_link = f"https://careers.loblaw.ca{job_link}"
                
                # Extract location
                location_elem = card.find('span', class_='results-list__item-street--label')
                location = location_elem.text.strip() if location_elem else "Windsor, ON"
                
                # Extract store/brand
                brand_elem = card.find('span', class_='results-list__item-brand--label')
                brand = brand_elem.text.strip() if brand_elem else "Loblaw"
                
                # Extract distance if available
                distance_elem = card.find('span', class_='results-list__item-distance--label')
                distance = distance_elem.text.strip() if distance_elem else "N/A"
                
                # Create unique job ID
                job_id = f"{job_title}_{location}".replace(' ', '_').replace(',', '')
                
                jobs[job_id] = {
                    'title': job_title,
                    'location': location,
                    'brand': brand,
                    'distance': distance,
                    'link': job_link,
                    'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None

def load_cached_jobs():
    """Load previously saved jobs from S3"""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=CACHE_FILE_KEY)
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f"No cached jobs found or error loading: {e}")
        return {}

def save_jobs(jobs):
    """Save current jobs to S3"""
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=CACHE_FILE_KEY,
            Body=json.dumps(jobs, indent=2),
            ContentType='application/json'
        )
        print("✅ Jobs saved to S3")
    except Exception as e:
        print(f"❌ Error saving to S3: {e}")

def compare_jobs(old_jobs, new_jobs):
    """Find new and removed jobs"""
    new_job_ids = set(new_jobs.keys())
    old_job_ids = set(old_jobs.keys())
    
    added_ids = new_job_ids - old_job_ids
    removed_ids = old_job_ids - new_job_ids
    
    added_jobs = [new_jobs[job_id] for job_id in added_ids]
    removed_jobs = [old_jobs[job_id] for job_id in removed_ids]
    
    return added_jobs, removed_jobs

def format_job_details(job):
    """Format a single job for display"""
    text = f"<b>{job['title']}</b>\n"
    text += f"📍 {job['location']}\n"
    text += f"🏪 {job['brand']}\n"
    if job['distance'] != "N/A":
        text += f"📏 Distance: {job['distance']}\n"
    text += f"🔗 <a href='{job['link']}'>Apply Now</a>\n"
    return text

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    print(f"🔍 Checking at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check configuration
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return {
            'statusCode': 400,
            'body': 'Telegram bot not configured!'
        }
    
    # Get current jobs
    current_jobs = extract_jobs_from_page(URL)
    
    if current_jobs is None:
        return {
            'statusCode': 500,
            'body': 'Failed to fetch jobs'
        }
    
    print(f"📊 Found {len(current_jobs)} jobs on the page")
    
    # Load previous jobs
    previous_jobs = load_cached_jobs()
    
    # First run
    if not previous_jobs:
        print("📝 First run - saving initial job listings")
        save_jobs(current_jobs)
        
        message = "🚀 <b>Loblaw Job Monitor Started!</b>\n\n"
        message += "📍 Location: Windsor, ON\n"
        message += "💼 Type: Part-Time Jobs\n"
        message += f"📊 Currently tracking: {len(current_jobs)} jobs\n\n"
        
        # Show first 3 jobs as examples
        if current_jobs:
            message += "Current jobs include:\n\n"
            for i, (job_id, job) in enumerate(list(current_jobs.items())[:3]):
                message += f"{i+1}. <b>{job['title']}</b> at {job['brand']}\n"
        
        message += f"\n⏰ Checking every 5 minutes for changes\n"
        message += f"🔗 <a href='{URL}'>View All Jobs</a>"
        
        send_telegram_message(message)
        return {
            'statusCode': 200,
            'body': 'Monitor started successfully'
        }
    
    # Compare jobs
    added_jobs, removed_jobs = compare_jobs(previous_jobs, current_jobs)
    
    if added_jobs or removed_jobs:
        print(f"🚨 Changes detected! +{len(added_jobs)} -{len(removed_jobs)}")
        
        message = "🚨 <b>Job Listings Updated!</b>\n\n"
        message += f"📍 Windsor, ON - Part Time\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # New jobs
        if added_jobs:
            message += f"✨ <b>NEW JOBS ({len(added_jobs)}):</b>\n\n"
            for job in added_jobs[:5]:  # Show max 5 new jobs
                message += format_job_details(job)
                message += "\n"
            
            if len(added_jobs) > 5:
                message += f"... and {len(added_jobs) - 5} more new jobs!\n\n"
        
        # Removed jobs
        if removed_jobs:
            message += f"❌ <b>REMOVED ({len(removed_jobs)}):</b>\n"
            for job in removed_jobs[:3]:
                message += f"• {job['title']} at {job['brand']}\n"
            if len(removed_jobs) > 3:
                message += f"... and {len(removed_jobs) - 3} more\n"
        
        message += f"\n📊 Total jobs now: {len(current_jobs)}\n"
        message += f"🔗 <a href='{URL}'>View All Jobs</a>"
        
        send_telegram_message(message)
        save_jobs(current_jobs)
        
        return {
            'statusCode': 200,
            'body': f'Changes detected: +{len(added_jobs)} -{len(removed_jobs)}'
        }
    else:
        print("✅ No changes detected")
        return {
            'statusCode': 200,
            'body': 'No changes detected'
        } 