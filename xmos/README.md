# XMOS - X Marketing Operating System

AI-assisted marketing and content operating system for X (Twitter) accounts focused on organic audience growth, original content creation, Saudi/Gulf trend relevance, and continuous strategy improvement.

## ⚠️ Important Separation Rule

This system is designed for **AI organic content only**. Commercial content (affiliate links, coupons, discounts, product offers, sponsored posts) must be published manually through the official X app by the user.

```
AI → Audience / Reach / Authority / Engagement
User → Affiliate / Coupons / Offers / Revenue
```

## 🏗 Architecture

```
                    ┌─────────────────────┐
                    │      X ACCOUNT      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
       AI ORGANIC SYSTEM                    USER MANUAL
              │                         COMMERCIAL POSTS
              │                                 │
              ▼                                 ▼
       Marketing Agent                     Official X App
              │
      ┌───────┼────────┬─────────┐
      ▼       ▼        ▼         ▼
   Trends  Watchlist Strategy  Analytics
      │       │        │         │
      └───────┴────┬───┴─────────┘
                   ▼
             DeepSeek V4-Pro
                   │
                   ▼
          Content / Threads / Plan
                   │
                   ▼
              Quality Gate
                   │
                   ▼
              Content Queue
                   │
                   ▼
                Scheduler
                   │
                   ▼
                X API
                   │
                   └──────────────→ X ACCOUNT
```

## 📋 Features

- **Trend Intelligence**: Saudi & Gulf region trend detection and scoring
- **Watchlist Monitoring**: Track 5-10 competitor/influencer accounts
- **Content Generation**: AI-powered posts and threads
- **Quality Gates**: Validation before publishing
- **Scheduling**: Smart content scheduling with configurable time windows
- **Analytics**: Daily summaries, weekly/monthly strategy analysis
- **Cost Guards**: Budget limits for AI and X API usage
- **Web Dashboard**: Lightweight responsive UI for management

## 🛠 Technology Stack

- Python 3.12+
- FastAPI
- SQLite + SQLAlchemy + Alembic
- APScheduler
- Jinja2 (templates)
- httpx

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- X Developer Account with API access
- DeepSeek API key

### Installation

```bash
# Clone the repository
cd xmos

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - X API credentials
# - DeepSeek API key
# - Security settings

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

Access the dashboard at `http://localhost:8000`

## 📁 Project Structure

```
xmos/
├── app/
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core configuration, security, logging
│   ├── models/                 # SQLAlchemy database models
│   ├── schemas/                # Pydantic schemas
│   ├── repositories/           # Database access layer
│   ├── services/               # Business logic services
│   │   ├── ai/                 # AI provider integration
│   │   ├── x/                  # X API client
│   │   ├── trends/             # Trend collection & scoring
│   │   ├── watchlist/          # Watchlist monitoring
│   │   ├── content/            # Content generation
│   │   ├── analytics/          # Analytics & reporting
│   │   ├── strategy/           # Strategy planning
│   │   ├── publishing/         # Publishing service
│   │   ├── scheduler/          # Job scheduling
│   │   └── costs/              # Cost tracking & guards
│   ├── agents/                 # Marketing agent orchestration
│   ├── prompts/                # AI prompt templates
│   ├── api/                    # REST API routes
│   ├── web/                    # Web dashboard templates & static
│   └── jobs/                   # Scheduled job definitions
├── migrations/                  # Alembic database migrations
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── systemd/                     # systemd service files
├── data/                        # Runtime data (SQLite, logs, backups)
├── pyproject.toml
├── .env.example
└── README.md
```

## 🔧 Configuration

See `.env.example` for all configuration options:

- Application settings (host, port, timezone)
- X API credentials
- DeepSeek API settings
- Content limits (posts/day, threads/day)
- Budget guards
- Security settings

## 📊 Implementation Phases

1. **Phase 1 — Foundation**: Project setup, database, configuration
2. **Phase 2 — X Integration**: OAuth, token management, API client
3. **Phase 3 — AI Integration**: DeepSeek provider, prompts
4. **Phase 4 — Intelligence**: Trends, watchlist
5. **Phase 5 — Content**: Generation, validation, queue
6. **Phase 6 — Publishing**: Scheduling, safe publishing
7. **Phase 7 — Analytics**: Metrics, summaries, strategy
8. **Phase 8 — Operations**: Cost guards, deployment, backup

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 📦 Deployment

### Production Server (Ubuntu VPS ~1GB RAM)

```bash
# Install system dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv nginx

# Setup application
cd /opt/xmos
python3.12 -m venv venv
source venv/bin/activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with production values

# Run migrations
alembic upgrade head

# Setup systemd service
sudo cp systemd/xmos.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xmos
sudo systemctl start xmos

# Setup Nginx reverse proxy
sudo cp systemd/xmos.nginx /etc/nginx/sites-available/xmos
sudo ln -s /etc/nginx/sites-available/xmos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Backup

```bash
# Manual backup
python scripts/backup.py

# Restore
python scripts/restore.py --file backups/xmos_YYYYMMDD.db
```

## 📝 License

MIT License

## ⚠️ Platform Compliance

This system uses official X APIs only. It does not implement:
- Automated mass replies
- Mass likes/follows
- Engagement farming
- Spam posting
- Browser automation

Focus is on content operations and analytics for organic growth.
