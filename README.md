# Multi-Agent Networking Tool

An intelligent networking assistant powered by multiple AI agents that help you research prospects, craft personalized messages, and track outreach effectiveness.

## Features

### 🔍 Research Agents
- **LinkedIn Agent**: Extracts professional information, work history, education
- **Google Agent**: Finds additional context, projects, publications
- **Social Media Agent**: Discovers interests, activities, personality traits

### 🧩 Agglomeration Agent
- Synthesizes data from all research agents
- Builds comprehensive persona profiles
- Identifies personality traits and communication preferences

### ✉️ Message Generation Agent
- Creates personalized outreach messages
- Adapts tone based on context (channel, familiarity, age)
- Supports multiple outreach channels (LinkedIn, Email, Twitter)

### 📊 Analytics Agent
- Tracks outreach performance
- A/B testing for different messaging styles
- Automated follow-up reminders
- Success rate analysis

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Research Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ LinkedIn │  │  Google  │  │  Social  │      │
│  │  Agent   │  │  Agent   │  │   Media  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         Agglomeration Agent                      │
│           (Persona Builder)                      │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────┐           ┌──────────────┐
│   Message    │           │  Analytics   │
│    Agent     │           │    Agent     │
└──────────────┘           └──────────────┘
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy
- **AI**: Anthropic Claude API
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **Scheduling**: APScheduler

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Networking-Tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Run the application**
   ```bash
   python backend/main.py
   ```

5. **Open in browser**
   ```
   http://localhost:8000
   ```

## Usage

### 1. Create a New Prospect
- Navigate to the web interface
- Enter prospect information manually (name, company, education, interests)
- Or paste data from LinkedIn, Google, etc.

### 2. Generate Persona
- Click "Analyze Prospect" to run the agglomeration agent
- Review the generated persona and insights

### 3. Craft Message
- Select outreach channel (LinkedIn, Email, Twitter)
- Set parameters (degree of connection, familiarity, tone)
- Generate personalized message

### 4. Track Outreach
- Log when messages are sent
- Record responses
- View analytics and insights

## Project Structure

```
networking-tool/
├── backend/
│   ├── agents/              # AI agent implementations
│   ├── models/              # Database models
│   ├── api/                 # API routes
│   ├── config.py           # Configuration
│   └── main.py             # Application entry point
├── frontend/
│   ├── index.html          # Main UI
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
├── data/                    # SQLite database
└── requirements.txt        # Python dependencies
```

## API Endpoints

- `POST /api/prospects` - Create new prospect
- `GET /api/prospects` - List all prospects
- `GET /api/prospects/{id}` - Get prospect details
- `POST /api/prospects/{id}/analyze` - Generate persona
- `POST /api/prospects/{id}/message` - Generate message
- `POST /api/outreach` - Log outreach attempt
- `GET /api/analytics` - Get analytics data

## License

MIT
