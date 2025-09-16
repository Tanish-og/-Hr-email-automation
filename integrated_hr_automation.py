"""
Integrated HR Email Automation System
Combines manual HR email collection with automated LinkedIn job scraping
"""

import os
import time
import sqlite3
import json
from typing import List
from dotenv import load_dotenv
from linkedin_job_scraper import LinkedInJobScraper, JobPosting
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import google.generativeai as genai
import openai
import logging

# Load environment variables
load_dotenv()

# Configure APIs
openai.api_key = os.getenv('OPENAI_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Email configuration
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
RESUME_PATH = os.getenv('RESUME_PATH', 'Tanish_resume_updated (1).pdf')

# Configure logging
logging.basicConfig(
    filename='integrated_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IntegratedHRAutomation:
    """Integrated system combining manual and automated HR email collection"""

    def __init__(self):
        self.linkedin_scraper = LinkedInJobScraper()
        self.manual_db = 'emails.db'
        self.linkedin_db = 'linkedin_jobs.db'
        self.setup_databases()

    def setup_databases(self):
        """Set up both manual and LinkedIn databases"""
        # Manual emails database
        conn = sqlite3.connect(self.manual_db)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS emails (email TEXT UNIQUE)''')
        conn.commit()
        conn.close()

        # LinkedIn jobs database is already set up in the scraper

    def get_manual_emails(self) -> List[str]:
        """Get manually collected emails"""
        conn = sqlite3.connect(self.manual_db)
        c = conn.cursor()
        c.execute('SELECT email FROM emails')
        emails = [row[0] for row in c.fetchall()]
        conn.close()
        return emails

    def get_linkedin_hr_emails(self) -> List[str]:
        """Get HR emails from LinkedIn scraped jobs"""
        conn = sqlite3.connect(self.linkedin_db)
        c = conn.cursor()
        c.execute('SELECT hr_emails FROM jobs WHERE hr_emails IS NOT NULL AND hr_emails != "[]"')
        rows = c.fetchall()
        conn.close()

        all_emails = []
        for row in rows:
            try:
                emails = json.loads(row[0])
                all_emails.extend(emails)
            except:
                continue

        return list(set(all_emails))  # Remove duplicates

    def get_all_hr_emails(self) -> List[str]:
        """Get all HR emails from both sources"""
        manual_emails = self.get_manual_emails()
        linkedin_emails = self.get_linkedin_hr_emails()
        return list(set(manual_emails + linkedin_emails))

    def send_email(self, recipient: str, subject: str, body: str):
        """Send email with resume attachment"""
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Attach resume
            if os.path.exists(RESUME_PATH):
                with open(RESUME_PATH, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(RESUME_PATH)}")
                    msg.attach(part)

            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, recipient, text)
            server.quit()

            print(f"✅ Email sent to {recipient}")
            logging.info(f"Email sent successfully to {recipient}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email to {recipient}: {str(e)}")
            logging.error(f"Failed to send email to {recipient}: {str(e)}")
            return False

    def generate_ai_email(self, company_name: str, job_title: str = "AI/ML Engineer") -> tuple:
        """Generate AI-powered email content"""
        subject = f"Interest in {job_title} Position at {company_name}"

        prompt = f"""Write a professional job application email for a {job_title} position at {company_name}.
        Include a subject line and formal body. Keep it concise and mention resume attachment.
        Make it personalized for the company and role."""

        try:
            # Try OpenAI first
            if openai.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                ai_content = response.choices[0].message.content.strip()
            else:
                # Fallback to Google Gemini
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                ai_content = response.text.strip()

            # Parse subject and body
            lines = ai_content.split('\n')
            if len(lines) > 1:
                subject = lines[0].replace('Subject:', '').strip()
                body = '\n'.join(lines[1:]).strip()
            else:
                body = ai_content

        except Exception as e:
            print(f"AI generation failed: {e}. Using template.")
            body = f"""
Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company_name}. With my background in AI/ML development and passion for innovative solutions, I am excited about the opportunity to contribute to your team.

Please find my resume attached for your review. I would welcome the chance to discuss how my skills and experiences align with {company_name}'s goals.

Thank you for considering my application. I look forward to the possibility of speaking with you soon.

Best regards,
[Your Full Name]
[Your Phone Number]
[Your LinkedIn Profile]
"""

        return subject, body

    def run_linkedin_pipeline(self):
        """Run the complete LinkedIn scraping pipeline"""
        print("🚀 Starting LinkedIn AI/ML Job Scraping Pipeline...")
        jobs = self.linkedin_scraper.run_full_pipeline()
        print(f"✅ Found {len(jobs)} AI/ML jobs and extracted HR emails")
        return jobs

    def send_bulk_emails(self, email_source: str = "all", use_ai: bool = True):
        """Send bulk emails to HR contacts"""
        if email_source == "manual":
            emails = self.get_manual_emails()
            print(f"📧 Sending to {len(emails)} manually collected emails")
        elif email_source == "linkedin":
            emails = self.get_linkedin_hr_emails()
            print(f"📧 Sending to {len(emails)} LinkedIn scraped HR emails")
        else:
            emails = self.get_all_hr_emails()
            print(f"📧 Sending to {len(emails)} total HR emails")

        if not emails:
            print("❌ No emails found. Please collect emails first.")
            return

        sent_count = 0
        failed_count = 0

        for i, email in enumerate(emails, 1):
            try:
                # Extract company name from email
                company_name = email.split('@')[1].split('.')[0].capitalize()

                # Generate email content
                if use_ai:
                    subject, body = self.generate_ai_email(company_name)
                else:
                    subject = f"Application for AI/ML Engineer Position at {company_name}"
                    body = f"""
Dear Hiring Manager,

I am writing to express my interest in the AI/ML Engineer position at {company_name}. With my background in AI/ML development and passion for innovative solutions, I am excited about the opportunity to contribute to your team.

Please find my resume attached for your review. I would welcome the chance to discuss how my skills and experiences align with {company_name}'s goals.

Thank you for considering my application. I look forward to the possibility of speaking with you soon.

Best regards,
[Your Full Name]
[Your Phone Number]
[Your LinkedIn Profile]
"""

                # Send email
                success = self.send_email(email, subject, body)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

                # Rate limiting
                if i < len(emails):
                    print("⏳ Waiting 5 seconds before next email...")
                    time.sleep(5)

            except Exception as e:
                print(f"❌ Error processing {email}: {e}")
                failed_count += 1
                continue

        print("\n📊 Email Campaign Summary:")
        print(f"✅ Successfully sent: {sent_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Success rate: {(sent_count/(sent_count+failed_count)*100):.1f}%")

    def show_stats(self):
        """Show system statistics"""
        manual_emails = len(self.get_manual_emails())
        linkedin_emails = len(self.get_linkedin_hr_emails())
        total_emails = manual_emails + linkedin_emails

        # Get LinkedIn jobs count
        conn = sqlite3.connect(self.linkedin_db)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM jobs')
        linkedin_jobs = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM jobs WHERE processed = 1')
        processed_jobs = c.fetchone()[0]
        conn.close()

        print("\n📊 System Statistics:")
        print("=" * 40)
        print(f"📧 Manual HR Emails: {manual_emails}")
        print(f"🔗 LinkedIn HR Emails: {linkedin_emails}")
        print(f"📨 Total HR Emails: {total_emails}")
        print(f"💼 LinkedIn Jobs Scraped: {linkedin_jobs}")
        print(f"✅ Processed Jobs: {processed_jobs}")
        print(f"⏳ Unprocessed Jobs: {linkedin_jobs - processed_jobs}")

def main():
    """Main function for integrated HR automation"""
    system = IntegratedHRAutomation()

    print("🚀 Integrated HR Email Automation System")
    print("=" * 50)
    print("Combining manual collection + LinkedIn automation")

    while True:
        print("\n📋 Main Menu:")
        print("1. 🔍 Run LinkedIn AI/ML Job Scraper")
        print("2. ✏️  Add HR Emails Manually")
        print("3. 📧 Send Emails to Manual Contacts")
        print("4. 🤖 Send AI Emails to LinkedIn HRs")
        print("5. 📨 Send Bulk Emails (All Sources)")
        print("6. 📊 View System Statistics")
        print("7. 📋 View All Collected Emails")
        print("8. 🔧 LinkedIn Scraper Menu")
        print("9. ❌ Exit")

        choice = input("\nChoose an option (1-9): ").strip()

        if choice == '1':
            system.run_linkedin_pipeline()

        elif choice == '2':
            emails = system.get_manual_emails()
            print("Enter HR email addresses (one per line, press Enter twice to finish):")
            while True:
                email = input().strip()
                if not email:
                    break
                if '@' in email and '.' in email:
                    if email not in emails:
                        # Save to manual database
                        conn = sqlite3.connect(system.manual_db)
                        c = conn.cursor()
                        c.execute('INSERT OR IGNORE INTO emails (email) VALUES (?)', (email,))
                        conn.commit()
                        conn.close()
                        print(f"✅ Added: {email}")
                    else:
                        print(f"⚠️  Duplicate: {email}")
                else:
                    print(f"❌ Invalid email: {email}")

        elif choice == '3':
            use_ai = input("Use AI-generated emails? (y/n): ").lower().startswith('y')
            system.send_bulk_emails("manual", use_ai)

        elif choice == '4':
            use_ai = input("Use AI-generated emails? (y/n): ").lower().startswith('y')
            system.send_bulk_emails("linkedin", use_ai)

        elif choice == '5':
            use_ai = input("Use AI-generated emails? (y/n): ").lower().startswith('y')
            system.send_bulk_emails("all", use_ai)

        elif choice == '6':
            system.show_stats()

        elif choice == '7':
            print("\n📧 All Collected HR Emails:")
            print("-" * 30)
            all_emails = system.get_all_hr_emails()
            if all_emails:
                for i, email in enumerate(all_emails, 1):
                    print(f"{i}. {email}")
            else:
                print("No emails collected yet.")

        elif choice == '8':
            # Run LinkedIn scraper directly
            os.system('python linkedin_job_scraper.py')

        elif choice == '9':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please select 1-9.")

if __name__ == "__main__":
    main()
