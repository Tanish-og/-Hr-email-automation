# HR Email Automation System

An intelligent agentic AI system for automated job application emails. This system collects HR email addresses from various sources and sends personalized, formal job application emails with resume attachments.

## 🌟 Features

### Core Functionality
- **HR Email Collection**: Manual entry and web scraping capabilities
- **Email Validation**: Automatic email format validation
- **Personalized Email Generation**: AI-powered emails using your resume content
- **Resume Content Extraction**: Automatic PDF text extraction for personalization
- **Resume Attachment**: Automatic attachment of your resume
- **SMTP Integration**: Secure email sending via Gmail/Outlook
- **Database Storage**: SQLite database for email management
- **Comprehensive Logging**: Detailed logs for tracking and debugging

### AI-Powered Features
- **Resume-Based Personalization**: Emails generated from your actual resume content
- **Smart Email Templates**: Generate professional emails using Google Gemini
- **Personal Information Integration**: Includes your name, email, phone, LinkedIn
- **Job Role Targeting**: Specify desired position for tailored content
- **Company-Specific Content**: Tailored emails based on company information
- **Fallback Templates**: Default professional templates when AI is unavailable

## 📋 Requirements

### Python Dependencies
```bash
pip install -r requirements.txt
```

### API Keys Required (Choose at least one)
- **OpenAI API Key**: For GPT-powered email generation
- **Google Gemini API Key**: For Gemini-powered email generation (FREE)

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Edit the `.env` file with your actual API keys and email credentials:

```env
# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Resume Path
RESUME_PATH=Tanish_resume_updated (1).pdf

# API Keys (Required - Choose one)
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### Step 3: Set Up Gmail App Password (Important!)
For Gmail users, you need to create an App Password:

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App passwords
4. Generate a password for "Mail"
5. Use this password in the `.env` file instead of your regular password

### Step 4: Run the Application

#### Option A: Web Interface (Recommended)
```bash
streamlit run app.py
```
This opens a beautiful web interface at `http://localhost:8501`

#### Option B: Command Line Interface
```bash
python main.py
```

## 📧 Usage Guide

### Main Menu Options

1. **Collect HR Emails Manually**
   - Enter email addresses one by one
   - Automatic duplicate detection
   - Email format validation

2. **Scrape HR Emails from Website**
   - Input company career page URLs
   - Automatic email extraction
   - ⚠️ Use responsibly - check website terms of service

3. **View Collected Emails**
   - Display all stored HR emails
   - Shows total count

4. **Send Automated Emails**
   - Generates personalized emails for each HR
   - Attaches your resume automatically
   - Includes 5-second delays between emails

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SENDER_EMAIL` | Your email address | Required |
| `SENDER_PASSWORD` | Your email password/app password | Required |
| `SMTP_SERVER` | SMTP server | smtp.gmail.com |
| `SMTP_PORT` | SMTP port | 587 |
| `RESUME_PATH` | Path to your resume PDF | Tanish_resume_updated (1).pdf |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `GOOGLE_API_KEY` | Google Gemini API key | Optional |

### API Key Setup

#### OpenAI API Key
1. Visit [https://platform.openai.com/](https://platform.openai.com/)
2. Sign up/Login to your account
3. Navigate to API Keys section
4. Create a new secret key
5. Copy and paste into `.env` file

#### Google Gemini API Key (FREE)
1. Visit [https://aistudio.google.com/](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API key"
4. Create a new API key
5. Copy and paste into `.env` file

## 📊 Email Templates

### AI-Generated Emails
The system uses AI to generate personalized emails based on:
- Company name extraction from email domain
- Professional tone and structure
- Resume attachment mention
- Call-to-action for interview

### Fallback Template
If AI is unavailable, the system uses a professional default template:

```
Subject: Application for Software Engineering Position at [Company]

Dear Hiring Manager,

I am writing to express my interest in the Software Engineering position at [Company]. With my background in software development and passion for innovative solutions, I am excited about the opportunity to contribute to your team.

Please find my resume attached for your review. I would welcome the chance to discuss how my skills and experiences align with [Company]'s goals.

Thank you for considering my application. I look forward to the possibility of speaking with you soon.

Best regards,
[Your Full Name]
[Your Phone Number]
[Your LinkedIn/Profile]
```

## 🗄️ Database Management

### SQLite Database: `emails.db`
- Stores all collected HR email addresses
- Automatic duplicate prevention
- Persistent storage across sessions

### Log Files
- `email_log.txt`: Records all email sending activities
- Includes timestamps, success/failure status
- Useful for debugging and tracking

## ⚠️ Important Notes

### Email Best Practices
- **Rate Limiting**: 5-second delays between emails to avoid spam filters
- **Personalization**: AI-generated emails are tailored per company
- **Professional Tone**: All emails maintain formal, professional language

### Legal & Ethical Considerations
- **Web Scraping**: Only scrape websites you have permission to access
- **Terms of Service**: Check company websites for scraping policies
- **Data Privacy**: Ensure compliance with data protection regulations
- **Spam Laws**: Use responsibly and avoid spamming

### Security
- **App Passwords**: Use Gmail app passwords, not regular passwords
- **API Keys**: Keep API keys secure and never commit to version control
- **Environment Variables**: Store sensitive data in `.env` file

## 🔍 Troubleshooting

### Common Issues

#### "Authentication failed"
- Check if you're using an app password for Gmail
- Verify email credentials in `.env` file

#### "AI generation failed"
- Ensure you have a valid API key
- Check API key limits and billing status
- The system will automatically use fallback templates

#### "Resume file not found"
- Verify the resume file exists in the project directory
- Check the `RESUME_PATH` in `.env` file
- Ensure correct file extension (.pdf)

#### "Connection timeout"
- Check your internet connection
- Verify SMTP server settings
- Try different SMTP ports if needed

### Log Analysis
Check `email_log.txt` for detailed error messages and debugging information.

## 📈 Future Enhancements

### Planned Features
- **Company Research Integration**: Automatically research companies before sending emails
- **LinkedIn Integration**: Scrape HR contacts from LinkedIn
- **Email Tracking**: Track email opens and responses
- **A/B Testing**: Test different email templates
- **CRM Integration**: Connect with CRM systems for follow-up management

### Advanced AI Features
- **Sentiment Analysis**: Analyze company culture from job postings
- **Personalization Engine**: Use company data for highly personalized emails
- **Response Prediction**: AI-powered prediction of response likelihood

## 🚀 Deployment

### Streamlit Cloud Deployment (Recommended)

1. **Create GitHub Repository:**
   ```bash
   # If you haven't already connected to GitHub:
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin master
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file path to: `app.py`
   - Add secrets in Streamlit Cloud:
     ```
     SENDER_EMAIL = "your_email@gmail.com"
     SENDER_PASSWORD = "your_gmail_app_password"
     GOOGLE_API_KEY = "your_gemini_api_key"
     RESUME_PATH = "Tanish_resume_updated (1).pdf"
     ```

3. **Access Your Deployed App:**
   - **Live App URL:** [Your Streamlit Cloud URL will appear here after deployment]
   - Your app will be live 24/7
   - Example: `https://hr-email-automation-username.streamlit.app`

### Local Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

## 🔧 Configuration for Deployment

### Required Environment Variables:
```env
# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# API Keys
GOOGLE_API_KEY=your_gemini_api_key

# Resume Path
RESUME_PATH=Tanish_resume_updated (1).pdf
```

### Gmail App Password Setup:
1. Enable 2-Factor Authentication on Gmail
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password (without spaces)

## 📊 Features Overview

### ✅ Core Features:
- **Professional Email Templates** with dynamic job role replacement
- **Resume Auto-Attachment** from PDF file
- **Job Role Selection** with 25+ professional positions
- **One-Click Email Sending** with Gmail integration
- **Re-sending Capability** for follow-ups
- **Past Emails Tracking** with detailed history
- **Auto-Resume Parsing** for skills and projects extraction

### ✅ Advanced Features:
- **SQLite Database** for email management
- **Comprehensive Logging** for all activities
- **Error Handling** with user-friendly messages
- **Responsive UI** with modern design
- **Mobile-Friendly** interface

## 🤝 Contributing

This is a personal project for job application automation. Feel free to fork and modify for your own use.

## 📄 License

This project is for personal use only. Please ensure compliance with all applicable laws and regulations regarding email automation and web scraping.

---

**⚠️ Disclaimer**: Use this tool responsibly. Automated email sending should comply with anti-spam laws and website terms of service. The author is not responsible for misuse of this tool.
