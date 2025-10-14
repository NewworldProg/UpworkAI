# UpworkAI - Intelligent Upwork Automation Platform

🤖 AI-powered platform for automating Upwork job applications, message management, and client communication.

## 🌟 Features

### 🔍 Job Monitoring & Applications
- **Automated Job Scraping**: Monitors new Upwork job postings in real-time
- **AI-Powered Cover Letters**: Generates tailored cover letters using AI models
- **Smart Job Matching**: Matches jobs based on your skills and preferences
- **Application Tracking**: Tracks application status and responses

### 💬 Message Management
- **Chat Extraction**: Extracts messages from Upwork conversations
- **AI Chat Analysis**: Analyzes conversations for insights and suggestions
- **Smart Replies**: Generates AI-powered response suggestions
- **Real-time Notifications**: Get notified of new messages and opportunities

### 🎯 AI Integration
- **Multiple AI Models**: Support for Ollama, OpenAI, and other AI services
- **Context-Aware Responses**: AI understands conversation context
- **Professional Templates**: Pre-built templates for common scenarios
- **Custom Training**: Fine-tune models for your specific use cases

## 🏗️ Architecture

### Backend (Django REST API)
```
backend/
├── projects/              # Job management and applications
├── ai_cover_letters/      # AI-powered cover letter generation
├── upwork_messages/       # Message extraction and AI chat
├── notification_push/     # Job monitoring and notifications
└── zephyr/               # Additional utilities
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── components/        # React components
│   ├── scraper/          # Browser automation scripts
│   └── utils/            # Utility functions
├── package.json
└── vite.config.js
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome browser (for automation)
- Virtual environment

### 1. Clone Repository
```bash
git clone https://github.com/NewworldProg/UpworkAI.git
cd UpworkAI
```

### 2. Backend Setup
```bash
# Activate virtual environment (if exists)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Django server
python manage.py runserver
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Chrome Setup for Automation
```bash
# Start Chrome with debugging enabled
chrome.exe --remote-debugging-port=9222 --user-data-dir="chrome-debug"
```

## 📊 Database Models

### Jobs & Monitoring
- **Job**: Upwork job postings with metadata
- **ScrapingSession**: Tracking of scraping activities
- **Notification**: System alerts and notifications
- **ChromeSession**: Browser session management

### Messages & Chat
- **Chat**: Upwork conversations/threads
- **Message**: Individual messages with AI analysis
- **MessageExtractionLog**: Extraction session logs

## 🔧 API Endpoints

### Job Management
```
GET  /api/notification-push/jobs/          # List jobs
POST /api/notification-push/start/         # Start monitoring
POST /api/notification-push/stop/          # Stop monitoring
```

### Message Management
```
GET  /api/messages/chats/                  # List chats
GET  /api/messages/chats/{id}/messages/    # Chat messages
POST /api/messages/extract/                # Extract messages
POST /api/messages/ai/analyze-active-chat/ # AI analysis
```

### AI Services
```
POST /api/ai/generate-cover-letter/        # Generate cover letter
POST /api/messages/ai/suggest-replies/     # Suggest replies
POST /api/messages/ai/generate-response/   # Generate response
```

## 🤖 AI Models Supported

- **Ollama** (Local AI models)
- **OpenAI GPT** (API-based)
- **Custom Models** (Configurable endpoints)

## 🔒 Security & Privacy

- All data stored locally by default
- Optional cloud backup with encryption
- No sensitive data shared with external services
- Configurable data retention policies

## 📈 Performance

- **Background Processing**: Long-running tasks handled asynchronously
- **Retry Logic**: Robust error handling and retry mechanisms
- **Caching**: Intelligent caching for improved performance
- **Database Optimization**: Efficient queries and indexing

## 🛠️ Development

### Project Structure
```
UpworkAI/
├── backend/              # Django REST API
├── frontend/             # React SPA
├── venv/                # Python virtual environment
├── start_services.ps1   # Windows service starter
├── start_services.py    # Cross-platform service starter
└── README.md
```

### Key Technologies
- **Backend**: Django, Django REST Framework, SQLite/PostgreSQL
- **Frontend**: React, Vite, Modern ES6+
- **Automation**: Puppeteer, Chrome DevTools Protocol
- **AI**: Ollama, OpenAI API, Custom models
- **Database**: SQLite (development), PostgreSQL (production)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Made with ❤️ for the Upwork freelancing community**