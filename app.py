import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging
import re
import time
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2

# Load environment variables
load_dotenv()

# Configure Gemini API
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

def save_email(email):
    conn = sqlite3.connect(EMAIL_DB)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO emails (email) VALUES (?)', (email,))
        conn.commit()
        st.success(f"✅ Email {email} saved successfully!")
    except sqlite3.IntegrityError:
        st.warning(f"⚠️ Email {email} already exists!")
    conn.close()

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

        # Log the sent email
        logging.info(f"Email sent to {recipient} - Subject: {subject}")

        return True, f"✅ Email sent successfully to {recipient}!"
    except Exception as e:
        error_msg = f"❌ Failed to send email to {recipient}: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def generate_ai_email(company_name):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return "Default Subject", "Default email body - API key not configured"

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
        st.warning(f"AI generation failed: {str(e)}. Using default template.")
        return generate_default_email(company_name)

def generate_default_email(company_name):
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

def extract_resume_text(pdf_path):
    """Extract text content from PDF resume"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        st.error(f"Error reading resume: {str(e)}")
        return ""

def extract_personal_info_from_resume(resume_text):
    """Extract personal information from resume text"""
    info = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'location': ''
    }

    if not resume_text:
        return info

    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    if emails:
        info['email'] = emails[0]

    # Extract phone
    phone_pattern = r'\b\d{10}\b|\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, resume_text)
    if phones:
        info['phone'] = phones[0]

    # Extract LinkedIn
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    linkedin_matches = re.findall(linkedin_pattern, resume_text, re.IGNORECASE)
    if linkedin_matches:
        info['linkedin'] = 'https://' + linkedin_matches[0]

    # Extract name (first line or prominent text)
    lines = resume_text.split('\n')[:5]
    for line in lines:
        line = line.strip()
        if line and len(line.split()) >= 2 and len(line) < 30:
            if not any(x in line.lower() for x in ['email', 'phone', 'address']):
                info['name'] = line
                break

    return info

def generate_personalized_email(company_name, job_role, user_name, user_email, phone, linkedin, resume_content):
    """Generate highly personalized email using resume content and personal details"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        return generate_fallback_personalized_email(company_name, job_role, user_name, user_email, phone, linkedin)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        Write a professional job application email for a {job_role} position at {company_name}.

        APPLICANT DETAILS:
        - Name: {user_name}
        - Email: {user_email}
        - Phone: {phone}

        RESUME CONTENT (Focus on skills and projects):
        {resume_content[:2500]}

        REQUIREMENTS:
        1. Include a professional subject line
        2. Start with applicant's introduction and current background
        3. Highlight specific skills and technologies from the resume
        4. Mention relevant projects and achievements
        5. Express interest in the specific job role
        6. Connect applicant's experience to job requirements
        7. Include contact information (name, email, phone only)
        8. Mention that resume is attached
        9. End with a call to action

        Focus on technical skills, projects, and achievements from the resume. Make it specific and compelling. Keep it concise (250-350 words).
        """

        response = model.generate_content(prompt)
        ai_content = response.text.strip()

        # Parse subject and body
        lines = ai_content.split('\n')
        subject = lines[0].replace('Subject:', '').strip() if lines else f"Application for {job_role} Position at {company_name}"
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ai_content

        return subject, body
    except Exception as e:
        st.warning(f"AI generation failed: {str(e)}. Using fallback template.")
        return generate_fallback_personalized_email(company_name, job_role, user_name, user_email, phone, linkedin)

def generate_fallback_personalized_email(company_name, job_role, user_name, user_email, phone, linkedin):
    """Fallback personalized email template"""
    subject = f"Application for {job_role} Position at {company_name}"

    body = f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {job_role} position at {company_name}. My name is {user_name}, and I am excited about the opportunity to contribute my skills and experience to your team.

Based on my background and qualifications, I believe I would be a great fit for this role. I have attached my resume for your review, which details my relevant experience and achievements.

I would welcome the opportunity to discuss how my background and skills align with {company_name}'s needs and goals. I am available for an interview at your earliest convenience.

Thank you for considering my application. I look forward to the possibility of speaking with you soon.

Best regards,
{user_name}
Email: {user_email}
Phone: {phone}
LinkedIn: {linkedin}
"""
    return subject, body

def get_sent_emails_log():
    """Get sent emails log with structured data"""
    if not os.path.exists('email_log.txt'):
        return []

    sent_emails = []
    try:
        with open('email_log.txt', 'r') as f:
            for line in f:
                if 'Email sent to' in line:
                    # Parse log line: "2025-09-17 12:50:15,123 - INFO - Email sent to hr@company.com - Subject: Application for Software Engineer Position"
                    parts = line.strip().split(' - ')
                    if len(parts) >= 4:
                        timestamp = f"{parts[0]} {parts[1]}"
                        email_part = parts[3]

                        # Extract email and subject
                        if ' - Subject: ' in email_part:
                            email_subject = email_part.split(' - Subject: ')
                            recipient = email_subject[0].replace('Email sent to ', '')
                            subject = email_subject[1]

                            # Extract job role from subject
                            job_role = "Unknown"
                            if "Application for " in subject and " Position" in subject:
                                job_role = subject.replace("Application for ", "").replace(" Position", "")

                            sent_emails.append({
                                'timestamp': timestamp,
                                'recipient': recipient,
                                'job_role': job_role,
                                'subject': subject
                            })
    except Exception as e:
        st.warning(f"Error reading email log: {e}")

    return sent_emails

# Auto-extract user information from resume on startup
@st.cache_data
def get_user_info():
    """Auto-extract user information from resume"""
    if not os.path.exists(RESUME_PATH):
        return {
            'name': 'Your Name',
            'email': 'your.email@example.com',
            'phone': 'Your Phone',
            'skills': 'Your Skills',
            'projects': 'Your Projects'
        }

    resume_text = extract_resume_text(RESUME_PATH)
    if not resume_text:
        return {
            'name': 'Your Name',
            'email': 'your.email@example.com',
            'phone': 'Your Phone',
            'skills': 'Your Skills',
            'projects': 'Your Projects'
        }

    # Extract name
    name = 'Your Name'
    lines = resume_text.split('\n')[:3]
    for line in lines:
        line = line.strip()
        if line and len(line.split()) >= 2 and len(line) < 30:
            if not any(x in line.lower() for x in ['email', 'phone', 'address', 'linkedin']):
                name = line
                break

    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    email = emails[0] if emails else 'your.email@example.com'

    # Extract phone
    phone_pattern = r'\b\d{10}\b|\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, resume_text)
    phone = phones[0] if phones else 'Your Phone'

    # Extract skills section
    skills_text = ""
    resume_lower = resume_text.lower()
    if 'skills' in resume_lower:
        # Find skills section
        lines = resume_text.split('\n')
        skills_start = -1
        for i, line in enumerate(lines):
            if 'skills' in line.lower():
                skills_start = i
                break

        if skills_start != -1:
            # Get next 10 lines for skills
            skills_lines = lines[skills_start:skills_start+10]
            skills_text = '\n'.join(skills_lines)

    # Extract projects section
    projects_text = ""
    if 'projects' in resume_lower or 'project' in resume_lower:
        lines = resume_text.split('\n')
        project_start = -1
        for i, line in enumerate(lines):
            if 'project' in line.lower():
                project_start = i
                break

        if project_start != -1:
            # Get next 15 lines for projects
            project_lines = lines[project_start:project_start+15]
            projects_text = '\n'.join(project_lines)

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills_text or 'Your technical skills and expertise',
        'projects': projects_text or 'Your key projects and achievements'
    }

# Streamlit UI
def main():
    st.set_page_config(page_title="HR Email Sender", page_icon="📧", layout="wide")

    st.title("🚀 HR Email Automation System")
    st.markdown("**Professional job application emails with AI-powered personalization**")

    # Job Role Selection
    st.header("🎯 Job Application Settings")

    job_role = st.selectbox(
        "Select the job position you're applying for:",
        [
            "Software Engineer",
            "Senior Software Engineer",
            "Full Stack Developer",
            "Frontend Developer",
            "Backend Developer",
            "DevOps Engineer",
            "Data Scientist",
            "Machine Learning Engineer",
            "AI Engineer",
            "Product Manager",
            "UI/UX Designer",
            "System Administrator",
            "Cloud Architect",
            "Mobile App Developer",
            "Python Developer",
            "Java Developer",
            "JavaScript Developer",
            "React Developer",
            "Node.js Developer",
            "Database Administrator",
            "Security Engineer",
            "QA Engineer",
            "Technical Lead",
            "Engineering Manager",
            "Other"
        ],
        index=0,
        help="Select the specific job role you're applying for. This will be used to personalize your email content."
    )

    if job_role == "Other":
        job_role = st.text_input("Please specify the job role:", placeholder="e.g., Technical Architect")

    st.success(f"📋 Applying for: **{job_role}** position")

    # Auto-extract user info
    with st.spinner("Loading your information from resume..."):
        user_info = get_user_info()

    # Display user info
    st.header("👤 Your Information (Auto-extracted from Resume)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👤 Name", user_info['name'])
    with col2:
        st.metric("📧 Email", user_info['email'])
    with col3:
        st.metric("📞 Phone", user_info['phone'])

    # Show extracted skills and projects
    with st.expander("📋 Your Skills & Projects (Auto-extracted)", expanded=False):
        col_skills, col_projects = st.columns(2)
        with col_skills:
            st.subheader("🛠️ Skills")
            st.text_area("", value=user_info['skills'][:500], height=150, disabled=True)
        with col_projects:
            st.subheader("💼 Projects")
            st.text_area("", value=user_info['projects'][:500], height=150, disabled=True)

    # HR Emails Table
    st.header("📧 HR Email Management")

    # Add new HR email
    col_add, col_space = st.columns([1, 3])
    with col_add:
        new_email = st.text_input("Add HR Email:", placeholder="hr@company.com", key="new_email")
        if st.button("➕ Add Email", use_container_width=True):
            if new_email and validate_email(new_email):
                save_email(new_email)
                st.rerun()
            else:
                st.error("Please enter a valid email address")

    # Load and display HR emails in a table
    emails = load_emails()

    if emails:
        st.subheader(f"📋 HR Emails ({len(emails)})")

        # Create table data
        table_data = []
        for email in emails:
            company = email.split('@')[1].split('.')[0].capitalize()

            # Generate email content for this company
            resume_content = extract_resume_text(RESUME_PATH) if os.path.exists(RESUME_PATH) else ""

            # Use the user's preferred email template with dynamic job role replacement
            subject = f"Application for {job_role} Position"

            body = f"""
Tanish Gupta
guptatanish50@gmail.com
 | +91 9170908456
LinkedIn
 | GitHub
 | Portfolio

[Date]

Dear Hiring Manager,

I am excited to apply for the {job_role} position. I am a Computer Science undergraduate at IIIT Tiruchirappalli with strong skills in AI and Machine Learning, backed by hands-on project experience.

I developed JobNet, an AI-powered recruitment platform using NLP for skill extraction and AI match scoring, along with CrewAI, an automation framework for streamlining business workflows. Additionally, I built a Movie Recommender System leveraging TF-IDF and cosine similarity to boost user engagement.

My technical expertise includes Python, PyTorch, TensorFlow, Hugging Face, LangChain, FastAPI, OpenCV, and AI automation tools like CrewAI and n8n. I have also completed courses in Generative AI and Machine Learning, reinforcing my practical knowledge.

I am eager to apply my skills to develop innovative AI solutions and contribute to meaningful projects. Thank you for your time and consideration.

Sincerely,
Tanish Gupta
"""

            table_data.append({
                'Company': company,
                'HR Email': email,
                'Email Content': f"**Subject:** {subject}\n\n**Body:**\n{body[:300]}...",
                'Send': False
            })

        # Display as table with send buttons
        for i, row in enumerate(table_data):
            col1, col2, col3, col4 = st.columns([1, 2, 4, 1])

            with col1:
                st.write(f"**{row['Company']}**")

            with col2:
                st.write(row['HR Email'])

            with col3:
                with st.expander(f"📄 View Email Content", expanded=False):
                    st.text_area("", value=row['Email Content'], height=150, disabled=True, key=f"content_{i}")

            with col4:
                if st.button("🚀 Send", key=f"send_{i}", use_container_width=True):
                    # Parse the email content
                    content_lines = row['Email Content'].split('\n')
                    subject = content_lines[0].replace('**Subject:** ', '')
                    body = '\n'.join(content_lines[2:]).replace('**Body:**\n', '')

                    with st.spinner(f"Sending email to {row['HR Email']}..."):
                        success, message = send_email(row['HR Email'], subject, body, RESUME_PATH)

                    if success:
                        st.success(f"✅ Email sent to {row['Company']}!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed: {message}")

            st.divider()

    else:
        st.info("No HR emails added yet. Add some emails above to get started!")

    # Past Sent Emails Section
    st.header("📤 Past Sent Emails")

    sent_emails = get_sent_emails_log()
    if sent_emails:
        st.subheader(f"📋 Recently Sent Emails ({len(sent_emails)})")

        # Display as a clean table
        for i, email_data in enumerate(sent_emails[-10:], 1):  # Show last 10 emails
            col_time, col_recipient, col_role, col_action = st.columns([2, 3, 2, 1])

            with col_time:
                # Format timestamp nicely
                timestamp = email_data['timestamp']
                if ',' in timestamp:
                    date_time = timestamp.split(',')
                    st.write(f"📅 {date_time[0]}")
                    st.write(f"🕐 {date_time[1][:5]}")
                else:
                    st.write(f"📅 {timestamp}")

            with col_recipient:
                company = email_data['recipient'].split('@')[1].split('.')[0].capitalize()
                st.write(f"🏢 **{company}**")
                st.write(f"📧 {email_data['recipient']}")

            with col_role:
                st.write(f"💼 {email_data['job_role']}")

            with col_action:
                # Allow re-sending to the same email
                if st.button("🔄 Resend", key=f"resend_{i}", help=f"Resend to {email_data['recipient']}"):
                    # Use current job role for resending
                    subject = f"Application for {job_role} Position"
                    body = f"""
Tanish Gupta
guptatanish50@gmail.com
 | +91 9170908456
LinkedIn
 | GitHub
 | Portfolio

[Date]

Dear Hiring Manager,

I am excited to apply for the {job_role} position. I am a Computer Science undergraduate at IIIT Tiruchirappalli with strong skills in AI and Machine Learning, backed by hands-on project experience.

I developed JobNet, an AI-powered recruitment platform using NLP for skill extraction and AI match scoring, along with CrewAI, an automation framework for streamlining business workflows. Additionally, I built a Movie Recommender System leveraging TF-IDF and cosine similarity to boost user engagement.

My technical expertise includes Python, PyTorch, TensorFlow, Hugging Face, LangChain, FastAPI, OpenCV, and AI automation tools like CrewAI and n8n. I have also completed courses in Generative AI and Machine Learning, reinforcing my practical knowledge.

I am eager to apply my skills to develop innovative AI solutions and contribute to meaningful projects. Thank you for your time and consideration.

Sincerely,
Tanish Gupta
"""

                    with st.spinner(f"Resending to {email_data['recipient']}..."):
                        success, message = send_email(email_data['recipient'], subject, body, RESUME_PATH)

                    if success:
                        st.success(f"✅ Resent to {company}!")
                        st.balloons()
                    else:
                        st.error(f"❌ Failed: {message}")

            st.divider()
    else:
        st.info("📭 No emails sent yet. Send some emails to see them here!")

    # Quick stats
    st.markdown("---")
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("📧 Total HR Emails", len(emails))
    with col_stats2:
        st.metric("📤 Total Emails Sent", len(sent_emails))
    with col_stats3:
        # Calculate success rate (assuming all logged emails were successful)
        success_rate = 100.0 if len(sent_emails) > 0 else 0.0
        st.metric("✅ Success Rate", f"{success_rate:.1f}%")

if __name__ == "__main__":
    main()
