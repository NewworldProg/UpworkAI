# 🚀 UpworkApply - AI Cover Letter Generator

**AI-powered cover letter generator for Upwork projects with multiple AI backends**

## 🚧 Current State & Future Plans

### ✅ Current Features
- **Manual Job Data Entry** - Currently requires manual input of employer/job details
- **AI Cover Letter Generation** - Working with Ollama (mistral:7b model)
- **Multiple AI Backends** - Architecture ready for OpenAI, DeepSeek, Local models
- **Project Management** - Save and manage multiple job applications
- **Monday.com Integration** - Sync job applications with Monday.com boards for team collaboration

### 🔮 Planned Features (Next Iterations)
- **🤖 Automated Job Data Extraction** - Parse Upwork job postings automatically
- **💬 AI Interview Assistant** - Generate responses to common interview questions
- **📊 Enhanced Monday.com Workflow** - Automated status updates and task creation
- **📈 Application Analytics** - Track success rates and optimize approach
- **🎯 Personalization Engine** - Learn from successful applications

## 📋 Quick Start

### Prerequisites
✅ Docker Desktop installed and running  
✅ Terminal/Command Prompt access  

### 3 Steps to Run
```bash
# 1. Navigate to project folder
cd UpworkApply

# 2. Start all services
docker-compose up -d

# 3. Open in browser
http://localhost:5173
``

---

## � Project Structure

### Backend Architecture
```
backend/
├── projects/
│   ├── services.py          # Main business logic entry point
│   ├── cover_generator.py   # AI backend orchestrator
│   ├── cover_models/        # AI client implementations
│   │   ├── openai_client.py    # OpenAI GPT integration
│   │   ├── deepseak_client.py  # DeepSeek API integration  
│   │   ├── ollama_client.py    # Local Ollama integration --> working
│   │   └── local_client.py     # Local model integration
│   ├── models.py            # Database models
│   └── views.py             # API endpoints
```
for now Ollama is working

### Service Layer Pattern
Each AI backend has its own dedicated class:

**`services.py`** - Main entry point
```python
from .cover_generator import CoverGenerator

def generate_cover_letter(description, skills, mode=None):
    generator = CoverGenerator()
    return generator.generate(description, skills, only_backend=mode)
```

**`cover_generator.py`** - Backend orchestrator
```python
class CoverGenerator:
    def generate(self, description, skills, only_backend=None):
        # Routes to appropriate AI client based on backend choice
```

**Individual AI Clients**
- `OpenAIClient` - GPT models via OpenAI API
- `DeepSeakClient` - DeepSeek models via API
- `OllamaClient` - Local models via Ollama server
- `LocalClient` - Custom fine-tuned models

---

## 🔧 Docker Services

**4 Docker Containers:**
- **PostgreSQL** (port 5432) - Database
- **Django Backend** (port 8000) - API server  
- **React Frontend** (port 5173) - Web UI
- **Ollama** (port 11434) - Local AI model server

**AI Backends Available:**
- 🤖 **Ollama** (mistral:7b) - Local AI model ⭐ Default
- 🌐 **OpenAI** - GPT models (API key required)
- 🧠 **DeepSeek** - DeepSeek API (API key required)
- 🔧 **Local** - Custom fine-tuned models

---

## 🔧 Database Inspection

```bash
# Check projects in database
docker exec -it upwork_backend python manage.py shell -c "
from projects.models import Project
print(f'Total projects: {Project.objects.count()}')
for p in Project.objects.all()[:3]:
    print(f'- {p.title[:50]}')
"
```

---

## 🔑 API Keys Configuration (Optional)

Create `.env` file in root folder:
```env
OPENAI_API_KEY=sk-your-openai-key
DEEPSEAK_API_KEY=your-deepseek-key
MONDAY_API_KEY=your-monday-api-key
MONDAY_BOARD_ID=your-board-id
DEBUG=0
```

---

## 📊 Useful Commands

```bash
# Container status
docker-compose ps

# Service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Stop services
docker-compose down

# Full restart with rebuild
docker-compose down && docker-compose up -d --build

# Access containers
docker exec -it upwork_backend bash
docker exec -it upwork_frontend sh
```

---

## 🛠️ Development Workflow

### 1. Start Development Environment
```bash
docker-compose up -d
```

### 2. Frontend Testing
- Open http://localhost:5173
- Create new project
- Test cover letter generation with different AI backends
- Check database persistence

### 3. Code Changes
- Backend: Edit files in `backend/` (hot reload enabled)
- Frontend: Edit files in `frontend/src/` (hot reload enabled)
- Database: Run migrations with `docker exec upwork_backend python manage.py migrate`

---

## 🛠️ Troubleshooting

**Problem**: `port already in use`  
**Solution**: `docker-compose down` then `docker-compose up -d`

**Problem**: Frontend doesn't load projects  
**Solution**: Wait 30-60 seconds for all services to start

**Problem**: Ollama is slow  
**Solution**: First run downloads model, wait a few minutes

**Problem**: Backend 500 errors  
**Solution**: Check logs with `docker-compose logs backend`

**Problem**: Database connection errors  
**Solution**: Ensure PostgreSQL started with `docker-compose ps`


---

## 🎯 Team Workflow

1. **Server Admin**: Copy project to server → Run `docker-compose up -d`
2. **Team Members**: Download from server → Run locally `docker-compose up -d`
3. **Access**: Everyone uses http://localhost:5173 on their machine

---

## 📈 Performance Notes

- **Ollama**: First generation takes ~30 seconds (model loading), subsequent ones ~5-10 seconds

---

**Note**: All data is stored in Docker volumes and persists across service restarts.