"""
Simple HR Email Automation System
Reads HR emails from hr_emails.txt file and sends automated job application emails
"""

import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re
import logging
from dotenv import load_dotenv
import google.generativeai as genai
import openai

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
    filename='simple_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimpleHRAutomation:
    """Simple system for automated HR email sending"""

    def __init__(self):
        self.hr_emails_file = 'hr_emails.txt'

    def load_hr_emails(self) -> list:
        """Load HR emails from the text file"""
        emails = []
        try:
            with open(self.hr_emails_file, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        # Clean the email
                        email = line.split('#')[0].strip()  # Remove inline comments
                        if self.validate_email(email):
                            emails.append(email)
                        else:
                            print(f"⚠️  Invalid email format: {email}")
        except FileNotFoundError:
            print(f"❌ File {self.hr_emails_file} not found. Please create it with HR emails.")
            return []
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []

        return list(set(emails))  # Remove duplicates

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
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
            else:
                print(f"⚠️  Resume file not found: {RESUME_PATH}")

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
            # Try Google Gemini first (since OpenAI has API issues)
            if genai.configure and os.getenv('GOOGLE_API_KEY'):
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                ai_content = response.text.strip()
            elif openai.api_key:
                # Fallback to OpenAI with new API format
                client = openai.OpenAI(api_key=openai.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                ai_content = response.choices[0].message.content.strip()
            else:
                raise Exception("No API keys available")

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

    def send_bulk_emails(self, use_ai: bool = True):
        """Send bulk emails to all HR contacts in the file"""
        emails = self.load_hr_emails()

        if not emails:
            print("❌ No valid HR emails found in hr_emails.txt")
            print("Please add email addresses to the file and try again.")
            return

        print(f"📧 Found {len(emails)} HR email addresses")
        print("📧 Starting bulk email campaign...")

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

    def show_email_list(self):
        """Display all emails in the file"""
        emails = self.load_hr_emails()
        print(f"\n📧 HR Emails in {self.hr_emails_file} ({len(emails)} total):")
        print("-" * 50)
        if emails:
            for i, email in enumerate(emails, 1):
                print(f"{i}. {email}")
        else:
            print("No emails found. Add emails to hr_emails.txt")

    def add_email_to_file(self, email: str):
        """Add a single email to the file"""
        if not self.validate_email(email):
            print(f"❌ Invalid email format: {email}")
            return False

        try:
            # Check if email already exists
            existing_emails = self.load_hr_emails()
            if email in existing_emails:
                print(f"⚠️  Email already exists: {email}")
                return False

            # Add to file
            with open(self.hr_emails_file, 'a', encoding='utf-8') as file:
                file.write(f"\n{email}")
            print(f"✅ Added email: {email}")
            return True

        except Exception as e:
            print(f"❌ Error adding email: {e}")
            return False

def main():
    """Main function for simple HR automation"""
    system = SimpleHRAutomation()

    print("🚀 Simple HR Email Automation System")
    print("=" * 45)
    print("Just add emails to hr_emails.txt and send!")

    while True:
        print("\n📋 Menu:")
        print("1. 📧 Send bulk emails to all HR contacts")
        print("2. ➕ Add single HR email")
        print("3. 📋 Show all HR emails")
        print("4. 🔄 Reload and send (after editing file)")
        print("5. ❌ Exit")

        choice = input("\nChoose option (1-5): ").strip()

        if choice == '1':
            use_ai = input("Use AI-generated emails? (y/n): ").lower().startswith('y')
            system.send_bulk_emails(use_ai)

        elif choice == '2':
            email = input("Enter HR email address: ").strip()
            if email:
                system.add_email_to_file(email)

        elif choice == '3':
            system.show_email_list()

        elif choice == '4':
            print("🔄 Reloading emails from file...")
            use_ai = input("Use AI-generated emails? (y/n): ").lower().startswith('y')
            system.send_bulk_emails(use_ai)

        elif choice == '5':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()
