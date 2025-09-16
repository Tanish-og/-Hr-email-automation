# Agentic AI for HR Email Collection and Automated Job Application Emails
# This script collects HR email IDs, stores them in a file, and sends formal emails with resume attachment

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json
import os
import logging
import re
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure API keys
openai.api_key = os.getenv('OPENAI_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Configure logging
logging.basicConfig(filename='email_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
EMAIL_DB = 'emails.db'
RESUME_PATH = os.getenv('RESUME_PATH', 'Tanish_resume_updated (1).pdf')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def load_emails():
    conn = sqlite3.connect(EMAIL_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails (email TEXT UNIQUE)''')
    c.execute('SELECT email FROM emails')
    emails = [row[0] for row in c.fetchall()]
    conn.close()
    return emails

def save_emails(emails):
    conn = sqlite3.connect(EMAIL_DB)
    c = conn.cursor()
    c.execute('DELETE FROM emails')
    c.executemany('INSERT INTO emails (email) VALUES (?)', [(email,) for email in emails])
    conn.commit()
    conn.close()

def scrape_hr_emails(url):
    print("WARNING: Web scraping may violate website terms of service. Use responsibly and ensure you have permission.")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find emails in text
        text = soup.get_text()
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        found_emails = re.findall(email_pattern, text)
        
        # Also check mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'mailto:'))
        for link in mailto_links:
            email = link['href'].replace('mailto:', '')
            if validate_email(email):
                found_emails.append(email)
        
        # Remove duplicates
        found_emails = list(set(found_emails))
        
        if found_emails:
            emails = load_emails()
            added = 0
            for email in found_emails:
                if email not in emails:
                    emails.append(email)
                    added += 1
            save_emails(emails)
            print(f"Scraped and added {added} new emails from {url}")
        else:
            print("No emails found on the page.")
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")

def collect_hr_emails():
    emails = load_emails()
    print("Enter HR email IDs (one per line, press Enter twice to finish):")
    while True:
        email = input().strip()
        if not email:
            break
        if validate_email(email):
            if email not in emails:
                emails.append(email)
                print(f"Added: {email}")
            else:
                print(f"Duplicate: {email}")
        else:
            print(f"Invalid email format: {email}")
    save_emails(emails)
    print(f"Collected {len(emails)} HR emails.")

def send_email(recipient, subject, body, attachment_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient, text)
        server.quit()
        print(f"Email sent to {recipient}")
        logging.info(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email to {recipient}: {str(e)}")
        logging.error(f"Failed to send email to {recipient}: {str(e)}")

def generate_formal_email(company_name):
    subject = f"Application for Software Engineering Position at {company_name}"
    body = f"""
Dear Hiring Manager,

I am writing to express my interest in the Software Engineering position at {company_name}. With my background in software development and passion for innovative solutions, I am excited about the opportunity to contribute to your team.

Please find my resume attached for your review. I would welcome the chance to discuss how my skills and experiences align with {company_name}'s goals.

Thank you for considering my application. I look forward to the possibility of speaking with you soon.

Best regards,
[Your Full Name]
[Your Phone Number]
[Your LinkedIn/Profile]
"""
    return subject, body

def generate_ai_email(company_name):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Google API key not set. Using default template.")
        return generate_formal_email(company_name)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Write a professional job application email for a Software Engineering position at {company_name}. Include a subject line and formal body. Keep it concise and mention that resume is attached."
        response = model.generate_content(prompt)
        ai_content = response.text.strip()

        # Parse subject and body
        lines = ai_content.split('\n')
        subject = lines[0].replace('Subject:', '').strip() if lines else f"Application for Software Engineering at {company_name}"
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ai_content
        return subject, body
    except Exception as e:
        print(f"AI generation failed: {str(e)}. Using default template.")
        return generate_formal_email(company_name)

def generate_summary_report():
    summary_file = 'summary_report.txt'
    with open(summary_file, 'w') as f:
        f.write("=== HR EMAIL AUTOMATION SUMMARY REPORT ===\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Emails collected
        emails = load_emails()
        f.write(f"Total HR Emails Collected: {len(emails)}\n")
        f.write("Emails:\n")
        for email in emails:
            f.write(f"  - {email}\n")
        f.write("\n")

        # Email logs
        if os.path.exists('email_log.txt'):
            f.write("=== EMAIL SENDING LOGS ===\n")
            with open('email_log.txt', 'r') as log_file:
                f.write(log_file.read())
        else:
            f.write("No email logs found.\n")

        f.write("\n=== CONFIGURATION ===\n")
        f.write(f"Sender Email: {SENDER_EMAIL}\n")
        f.write(f"Resume Path: {RESUME_PATH}\n")
        f.write(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}\n")
        f.write(f"AI Integration: Gemini (Google)\n")

    print(f"Summary report generated: {summary_file}")

def automate_emails():
    emails = load_emails()
    if not emails:
        print("No HR emails found. Please collect emails first.")
        return

    for i, email in enumerate(emails):
        company_name = email.split('@')[1].split('.')[0].capitalize()  # Simple extraction
        subject, body = generate_ai_email(company_name)
        send_email(email, subject, body, RESUME_PATH)
        if i < len(emails) - 1:  # Don't sleep after last email
            print("Waiting 5 seconds before next email...")
            time.sleep(5)

if __name__ == "__main__":
    while True:
        print("\nOptions:")
        print("1. Collect HR Emails Manually")
        print("2. Scrape HR Emails from Website")
        print("3. View Collected Emails")
        print("4. Send Automated Emails")
        print("5. Generate Summary Report")
        print("6. Exit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            collect_hr_emails()
        elif choice == '2':
            url = input("Enter website URL to scrape for emails: ").strip()
            if url:
                scrape_hr_emails(url)
        elif choice == '3':
            emails = load_emails()
            print("Collected Emails:")
            for email in emails:
                print(email)
        elif choice == '4':
            automate_emails()
        elif choice == '5':
            generate_summary_report()
        elif choice == '6':
            break
        else:
            print("Invalid choice.")
