# Employee Onboarding Agent

A multi-agent AI system built with Streamlit that streamlines the employee onboarding process using Google's Generative AI.

## 🎯 Overview

The Employee Onboarding Agent is an intelligent system that automates and optimizes the employee onboarding workflow. It leverages multiple specialized AI agents to handle different aspects of onboarding:

- **HR Agent**: Manages employee records and project assignments
- **IT Agent**: Provisions technology access and resources
- **Training Agent**: Assigns and tracks training programs
- **Skill Gap Agent**: Identifies skill gaps and recommends personalized training

## ✨ Features

- 🔐 **Multi-role Authentication**: Admin, HR Lead, and IT Ops roles
- 👥 **Employee Management**: Add, edit, and manage employee information
- 📋 **Project Assignment**: Assign employees to projects with specific roles
- 🎓 **Skill Gap Analysis**: AI-powered assessment of employee skills
- 📚 **Training Recommendations**: Personalized course recommendations based on skill gaps
- 🤖 **AI-Powered Orchestration**: Intelligent task workflow management
- 📊 **Dashboard**: View and track onboarding status and metrics
- 💾 **Data Persistence**: SQLite database for storing all information

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd EmployeeOnboardingAgent

# Run setup script (Windows)
setup.bat

# OR for Mac/Linux
chmod +x setup.sh
./setup.sh
```

### 2. Configure API Key

Get your Google Generative AI API key from [Google AI Studio](https://aistudio.google.com/)

For **local development**:
```bash
# Create .streamlit/secrets.toml
GOOGLE_API_KEY = "your-api-key-here"
```

### 3. Run Locally

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser

### 4. Default Credentials

```
Username: admin      Password: admin123
Username: hrlead     Password: hrlead123
Username: itops      Password: itops123
```

## 📦 Deployment

### Deploy to Streamlit Cloud

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

**Quick Steps**:
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Create new app → Select repository & `app.py`
4. Add `GOOGLE_API_KEY` in Secrets settings
5. Done! Your app is live

## 📋 Requirements

- Python 3.9+
- Google Generative AI API key
- Modern web browser

## 📁 Project Structure

```
EmployeeOnboardingAgent/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── setup.bat/setup.sh     # Setup scripts
├── DEPLOYMENT.md          # Deployment guide
├── README.md             # This file
│
├── agents/               # AI agents for workflow
│   ├── base_agent.py
│   ├── hr_agent.py
│   ├── it_agent.py
│   ├── skill_gap_agent.py
│   └── training_agent.py
│
├── db/                   # Database layer
│   ├── database.py
│   └── seed_data.py
│
├── mcp/                  # Tool registry
│   └── registry.py
│
├── utils/                # Utilities
│   ├── gemini_client.py
│   └── logger.py
│
├── static/               # Frontend assets
│   └── styles.css
│
└── .streamlit/           # Streamlit config
    ├── config.toml
    └── secrets.toml.template
```

## 🔧 Technologies

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite (local) / PostgreSQL (production)
- **AI**: Google Generative AI (Gemini)
- **Architecture**: Multi-Agent System with MCP Protocol

## 📸 Screenshots

### Dashboard
- Overview of all employees and their onboarding status
- Recent activities and tasks

### Employee Management
- Add new employees
- View employee details and project assignments
- Track onboarding progress

### Skill Gap Analysis
- AI-powered skill assessment
- Personalized training recommendations
- Track assessment completion

## 🔐 Security Notes

- Change default credentials before production deployment
- Never commit secrets (`.streamlit/secrets.toml`) to version control
- Use environment variables for sensitive data
- Enable HTTPS for production
- Consider additional authentication layers

## 🐛 Troubleshooting

### Issue: "API key not configured"
**Solution**: Add `GOOGLE_API_KEY` to `.streamlit/secrets.toml` (local) or Secrets settings (cloud)

### Issue: Database locked errors
**Solution**: Ensure only one instance is running; SQLite has limited concurrency

### Issue: App loads slowly
**Solution**: Enable caching with `@st.cache_resource` decorator

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Detailed Streamlit Cloud setup
- [Streamlit Docs](https://docs.streamlit.io/)
- [Google AI API Docs](https://ai.google.dev/)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test locally with `streamlit run app.py`
4. Push and create a pull request

## 📝 License

[Add your license here]

## 👥 Support

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Review logs in Streamlit Cloud dashboard
- Verify all dependencies are in `requirements.txt`

## 📧 Contact

[Add contact information]

---

**Happy Onboarding! 🎉**

Start with [DEPLOYMENT.md](DEPLOYMENT.md) if you're deploying to Streamlit Cloud.
