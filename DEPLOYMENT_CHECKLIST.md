# Pre-Deployment Checklist

Use this checklist to ensure your Employee Onboarding Agent is ready for deployment to Streamlit Cloud.

## ✅ Setup & Configuration

- [ ] Clone repository to your machine
- [ ] Run `setup.bat` (Windows) or `setup.sh` (Mac/Linux)
- [ ] Virtual environment created successfully
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `.streamlit/secrets.toml` file created with Google API key
- [ ] `.env.example` file available in repository root

## ✅ Local Testing

- [ ] Run `streamlit run app.py` locally
- [ ] Test login with default credentials:
  - admin / admin123
  - hrlead / hrlead123
  - itops / itops123
- [ ] Dashboard loads without errors
- [ ] Database initializes and seeds properly
- [ ] Can add new employees
- [ ] Can create projects
- [ ] Can assign employees to projects
- [ ] Skill gap assessment works
- [ ] AI recommendations generate successfully

## ✅ Code Quality

- [ ] No Python syntax errors: `python -m py_compile app.py agents/*.py db/*.py utils/*.py mcp/*.py`
- [ ] No hardcoded secrets in code
- [ ] All imports are used
- [ ] Comments are clear and up-to-date
- [ ] No TODO or FIXME left unaddressed

## ✅ Repository Setup (Git)

- [ ] Repository initialized: `git init`
- [ ] `.gitignore` file exists and includes:
  - [ ] `__pycache__/`
  - [ ] `.env` and `.streamlit/secrets.toml`
  - [ ] `*.db` (database files)
  - [ ] `venv/`
- [ ] All code committed: `git add .` and `git commit -m "Initial commit"`
- [ ] Remote added: `git remote add origin <github-url>`
- [ ] Code pushed to GitHub: `git push -u origin main`
- [ ] Repository is public (or you have access to authorize Streamlit Cloud)

## ✅ Secrets Management

- [ ] Never commit `.streamlit/secrets.toml` to Git
- [ ] Never commit `.env` file
- [ ] `.streamlit/secrets.toml.template` is in repository (without actual key)
- [ ] `.env.example` is in repository (without actual values)

## ✅ Requirements.txt

- [ ] All dependencies listed: `pip freeze > requirements.txt`
- [ ] No local file paths in requirements.txt
- [ ] Python version compatibility verified (3.9+)
- [ ] Google generativeai package version specified

## ✅ Files to Include in Repo

- [ ] `app.py` - Main Streamlit application
- [ ] `requirements.txt` - Python dependencies
- [ ] `README.md` - Project documentation
- [ ] `DEPLOYMENT.md` - Deployment instructions
- [ ] `.streamlit/config.toml` - Streamlit configuration
- [ ] `.streamlit/secrets.toml.template` - Secrets template (NO ACTUAL KEY!)
- [ ] `.env.example` - Environment variables template
- [ ] `.gitignore` - Git ignore rules
- [ ] `agents/` directory with all agent files
- [ ] `db/` directory with database files
- [ ] `utils/` directory with utility files
- [ ] `mcp/` directory with registry files
- [ ] `static/` directory with CSS files
- [ ] `setup.bat` and `setup.sh` - Setup scripts
- [ ] `.github/workflows/` - CI/CD workflows (optional)

## ✅ Streamlit Cloud Deployment

### Create Streamlit Cloud Account

- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
- [ ] Sign up / Log in with GitHub account
- [ ] Grant permissions to access GitHub repositories

### Create New App

- [ ] Click "New app" button
- [ ] Select your GitHub repository
- [ ] Select branch: `main` (or default)
- [ ] Configure main file path: `app.py`
- [ ] Click "Deploy"

### Configure Secrets

- [ ] Wait for initial deployment (2-5 minutes)
- [ ] Click Settings gear icon (⚙️) top-right
- [ ] Click "Secrets" in sidebar
- [ ] Add your secrets:
  ```toml
  GOOGLE_API_KEY = "your-actual-google-api-key"
  GEMINI_MODEL = "gemini-1.5-flash"
  ```
- [ ] Click "Save"
- [ ] App will reboot with secrets loaded

## ✅ Post-Deployment

- [ ] Visit your app URL (provided by Streamlit Cloud)
- [ ] Login with test credentials
- [ ] Test all major features:
  - [ ] Dashboard displays correctly
  - [ ] Can add employees
  - [ ] Can create projects
  - [ ] Can run assessments
  - [ ] AI recommendations work
- [ ] Check app logs for errors: Streamlit Cloud > Manage App > Logs
- [ ] Share app URL with team
- [ ] Monitor app health daily for first week

## ⚠️ Important Notes

- The free tier of Streamlit Cloud includes limited resources
- SQLite database will reset on app restart (consider upgrading for persistence)
- Keep your API key secure - never share it
- Monitor API usage to avoid hitting quota limits
- Regularly update dependencies for security patches

## 🆘 If Deployment Fails

1. Check logs in Streamlit Cloud dashboard
2. Verify all files are in the GitHub repository
3. Ensure `.streamlit/secrets.toml` is NOT in repository (check `.gitignore`)
4. Verify `requirements.txt` has all dependencies
5. Test locally again: `streamlit run app.py`
6. Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting

## 🔐 Security Reminders

- [ ] Default credentials changed before production
- [ ] Never log sensitive information
- [ ] API keys stored only in Streamlit Secrets (cloud) or `.streamlit/secrets.toml` (local)
- [ ] Regular security audits performed
- [ ] Dependency vulnerabilities checked: `pip list --outdated`

## 📞 Support

- Streamlit Cloud Issues: https://discuss.streamlit.io/
- Streamlit Docs: https://docs.streamlit.io/
- Google AI Forum: https://ai.google.dev/
- Project Issues: Check repository issues tab

---

**Last Updated**: 2024
**Status**: Ready for deployment ✅

Mark each item as complete before deployment!
