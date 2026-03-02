# Employee Onboarding Agent - Streamlit Deployment Guide

This is a Streamlit-based Employee Onboarding Agent application that can be deployed to Streamlit Cloud.

## Features

- **Employee Management**: Add and manage employee information
- **Project Assignment**: Assign employees to projects
- **Skill Gap Analysis**: Assess and identify skill gaps using AI
- **Training Recommendations**: Get personalized training recommendations
- **Authentication**: Multi-role authentication (Admin, HR Lead, IT Ops)
- **Task Orchestration**: Automated onboarding workflow with multiple agents

## Prerequisites

- Python 3.9+
- Google Generative AI API key (get it from [Google AI Studio](https://aistudio.google.com/))
- Git account (for Streamlit Cloud deployment)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd EmployeeOnboardingAgent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Local Environment

Create `.streamlit/secrets.toml` file with your API key:

```toml
GOOGLE_API_KEY = "your-actual-google-api-key"
GEMINI_MODEL = "gemini-1.5-flash"
```

### 5. Run the App Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deployment to Streamlit Cloud

### Step 1: Push to GitHub

1. Ensure all files are committed and pushed to GitHub
2. The repository should include:
   - `app.py` (main application)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (Streamlit configuration)
   - `.gitignore` (to exclude secrets and unnecessary files)

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app" and sign in with your GitHub account
3. Select your repository and branch:
   - **Repository**: Your GitHub repo
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`

### Step 3: Add Secrets

After creating the app:

1. Click the "Settings" gear icon (⚙️) in the top-right corner
2. Select "Secrets" from the sidebar
3. Add your API key:

```toml
GOOGLE_API_KEY = "your-actual-google-api-key"
GEMINI_MODEL = "gemini-1.5-flash"
```

4. Click "Save"

### Step 4: Monitor Deployment

- The app will automatically redeploy when you push new commits
- View logs in the "Manage app" section
- Access your live app at the public URL provided by Streamlit

## Default Login Credentials (Development)

```
Username        Password
admin           admin123
hrlead          hrlead123
itops           itops123
```

**Note**: In production, change these credentials immediately!

## Database

- Local: SQLite database at `onboarding.db`
- Cloud: Data persists in Streamlit Cloud's filesystem (limited in free tier)

For production use, consider:
- PostgreSQL on AWS RDS
- Google Cloud SQL
- Firebase Firestore

## API Keys & Secrets

### Google Generative AI

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API key"
3. Create a new API key
4. Add to Streamlit Secrets as `GOOGLE_API_KEY`

## Troubleshooting

### App Won't Load

- Check secrets are configured correctly
- View app logs in Streamlit Cloud dashboard
- Ensure all dependencies are in `requirements.txt`

### Google API Errors

- Verify API key is valid and enabled
- Check API quota/usage limits
- Ensure `GOOGLE_API_KEY` is set in secrets

### Database Issues

- SQLite data persists locally but resets on Streamlit Cloud free tier restarts
- For persistent data, use cloud database service

### Performance

- Cache heavy computations with `@st.cache_resource` or `@st.cache_data`
- Optimize database queries
- Reduce image sizes in static assets

## Development Tips

1. **Testing Locally**: Always test locally with `streamlit run app.py` before pushing
2. **Dependencies**: Update `requirements.txt` when adding new packages
3. **Secrets**: Never commit `.streamlit/secrets.toml` to version control
4. **Logging**: Check app logs to debug issues
5. **Caching**: Use Streamlit's caching decorators for performance

## Project Structure

```
EmployeeOnboardingAgent/
├── app.py                      # Main Streamlit app
├── requirements.txt            # Python dependencies
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml.template  # Secrets template
├── agents/                     # AI agents for orchestration
│   ├── base_agent.py
│   ├── hr_agent.py
│   ├── it_agent.py
│   ├── skill_gap_agent.py
│   └── training_agent.py
├── db/                        # Database layer
│   ├── database.py
│   └── seed_data.py
├── mcp/                       # MCP registry for tool management
│   └── registry.py
├── utils/                     # Utility modules
│   ├── gemini_client.py
│   └── logger.py
└── static/                    # CSS and assets
    └── styles.css
```

## Support & Documentation

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
- [Google Generative AI API Docs](https://ai.google.dev/)

## License

[Add your license here]

## Contact

[Add contact information if needed]
