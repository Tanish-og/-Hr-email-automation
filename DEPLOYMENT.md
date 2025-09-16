# 🚀 Deployment Guide for HR Email Automation System

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Recommended - Free & Easy)

#### Step 1: Prepare Your Repository
```bash
# Your repository is already prepared with:
# ✅ app.py (main application)
# ✅ packages.txt (dependencies)
# ✅ .gitignore (excludes sensitive files)
# ✅ README.md (documentation)
```

#### Step 2: Deploy to Streamlit Cloud
1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository: `Tanish-og/-Hr-email-automation`
5. Set main file path: `app.py`
6. Click "Deploy"

#### Step 3: Configure Secrets
In Streamlit Cloud dashboard:
1. Go to your app settings
2. Add secrets for API keys:
```
GOOGLE_API_KEY = "your_google_gemini_api_key"
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
```

#### Step 4: Access Your Live App
- Your app will be available at: `https://[your-app-name].streamlit.app`
- Share this URL with anyone you want to use your system!

---

### Option 2: Heroku Deployment

#### Step 1: Create Required Files
```bash
# Create Procfile
echo "web: sh setup.sh && streamlit run app.py" > Procfile

# Create setup.sh
cat > setup.sh << EOF
mkdir -p ~/.streamlit/
echo "[global]
developmentMode = false
[logger]
level = "WARNING"
[client]
showSidebarNavigation = true
" > ~/.streamlit/config.toml
EOF

# Create runtime.txt
echo "python-3.9.12" > runtime.txt
```

#### Step 2: Deploy to Heroku
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-hr-automation-app

# Set environment variables
heroku config:set GOOGLE_API_KEY="your_key"
heroku config:set SENDER_EMAIL="your_email"
heroku config:set SENDER_PASSWORD="your_password"

# Deploy
git push heroku master
```

---

### Option 3: Railway Deployment

#### Step 1: Connect Repository
1. Go to [https://railway.app/](https://railway.app/)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Streamlit app

#### Step 2: Configure Environment Variables
In Railway dashboard:
- Go to Variables section
- Add your API keys and email credentials

#### Step 3: Deploy
- Railway will automatically build and deploy
- Your app will be available at a Railway domain

---

### Option 4: Render Deployment

#### Step 1: Create render.yaml
```yaml
services:
  - type: web
    name: hr-email-automation
    runtime: python3
    buildCommand: "pip install -r requirements.txt"
    startCommand: "streamlit run app.py --server.port $PORT --server.headless true"
```

#### Step 2: Deploy on Render
1. Go to [https://render.com/](https://render.com/)
2. Connect your GitHub repository
3. Render will detect the configuration
4. Set environment variables in dashboard
5. Deploy

---

## 🔧 Environment Variables Setup

### For All Deployment Platforms:

```bash
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_api_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password

# Optional (with defaults)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
RESUME_PATH=Tanish_resume_updated (1).pdf
```

### Getting API Keys:

#### Google Gemini API Key:
1. Visit: https://aistudio.google.com/
2. Sign in with Google account
3. Click "Get API key"
4. Create new API key
5. Copy the key

#### Gmail App Password:
1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App passwords
4. Generate password for "Mail"
5. Use this password (not your regular password)

---

## 📱 Mobile Access

Once deployed, your app works perfectly on mobile devices:
- 📱 Responsive design
- 👆 Touch-friendly interface
- 📧 Easy email management
- 📊 Real-time statistics

---

## 🔒 Security Considerations

### For Production Deployment:
- ✅ Never commit `.env` files
- ✅ Use environment variables for secrets
- ✅ Enable HTTPS (automatic on most platforms)
- ✅ Regular security updates
- ✅ Monitor API usage

### Data Privacy:
- 📄 Resume files are processed locally
- 🗄️ Email data stored securely
- 🔐 API keys encrypted
- 📊 No personal data logging

---

## 🚀 Quick Deployment Checklist

- [x] Code committed to GitHub
- [x] Dependencies listed in packages.txt
- [x] Sensitive files in .gitignore
- [x] Environment variables configured
- [ ] Deployment platform selected
- [ ] API keys obtained
- [ ] App deployed and tested

---

## 🎯 Recommended Deployment: Streamlit Cloud

**Why Streamlit Cloud?**
- 🚀 **Free** tier available
- ⚡ **Fast** deployment (2-3 minutes)
- 🔄 **Auto-updates** when you push to GitHub
- 📊 **Built-in** analytics
- 🌐 **Custom domains** supported
- 📱 **Mobile-friendly**

**Deployment Time:** ~5 minutes
**Cost:** Free for basic usage

---

## 🆘 Troubleshooting Deployment

### Common Issues:

#### "Module not found" errors:
```bash
# Make sure all dependencies are in packages.txt
streamlit
PyPDF2
google-generativeai
python-dotenv
requests
beautifulsoup4
```

#### Environment variables not working:
- Check variable names match exactly
- Ensure no extra spaces
- Restart deployment after adding variables

#### App not loading:
- Check build logs for errors
- Verify main file path is correct
- Ensure all required files are committed

---

## 📈 Scaling Your Deployment

### For Higher Usage:
- **Upgrade to paid plans** on deployment platforms
- **Add database persistence** (PostgreSQL)
- **Implement caching** for better performance
- **Add monitoring** and analytics
- **Set up CI/CD** pipelines

---

## 🎉 Post-Deployment

Once deployed, your HR Email Automation System will be:
- 🌐 **Accessible worldwide** 24/7
- 📱 **Mobile-optimized** for on-the-go use
- 🔄 **Auto-updating** with GitHub integration
- 📊 **Analytics-ready** for tracking usage
- 🤝 **Shareable** with colleagues/students

**Your professional job application automation tool is now live and ready to revolutionize your career search!** 🚀
