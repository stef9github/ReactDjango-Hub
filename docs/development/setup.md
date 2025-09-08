# Configuration Environnement de Développement

> **Setup complet pour développement SaaS médical français avec Claude Code**

## 🚀 Installation Rapide

### Prérequis
```bash
# Outils requis
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Git 2.40+
- Claude Code CLI
```

### Clone & Setup Initial
```bash
# Clone repository
git clone <repository-url> ReactDjango-Hub
cd ReactDjango-Hub

# Setup environnement complet
make claude-setup
```

## 🐍 Backend Django Setup

### Environment Variables
```bash
# Copier et configurer .env
cp backend/.env.example backend/.env

# Variables principales
DATABASE_URL=postgresql://user:password@localhost:5432/medical_saas
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
FIELD_ENCRYPTION_KEY=your-encryption-key-32-bytes
```

### Installation Dependencies
```bash
cd backend

# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows

# Dependencies production
pip install -r requirements.txt

# Dependencies développement et test
pip install -r requirements-test.txt
```

### Database Setup
```bash
# Migrations initiales
python manage.py migrate

# Données de test françaises
python manage.py loaddata fixtures/french_medical_terms.json
python manage.py loaddata fixtures/surgical_procedures_fr.json

# Superuser
python manage.py createsuperuser
```

## ⚛️ Frontend React Setup

### Installation Node.js
```bash
cd frontend

# Dependencies
npm install

# Vérification types TypeScript
npm run typecheck

# Tests
npm run test
```

### Configuration Variables
```bash
# .env.local
VITE_API_URL=http://localhost:8000/api
VITE_DEFAULT_LANGUAGE=fr
VITE_SUPPORTED_LANGUAGES=fr,de,en
```

## 🔧 Claude Code Agents Setup

### Configuration Agents
```bash
# Vérifier agents disponibles
ls -la .claude/agents/

# Agents actifs:
# - backend-agent.md (Backend + API unifié)
# - frontend-agent.md (React trilingue)
# - medical-translator-agent.md
# - code-review-agent.md
# - deployment-agent.md
# - documentation-agent.md
```

### Git Worktrees Parallel
```bash
# Setup worktrees développement parallèle
git worktree add ../ReactDjango-Hub-worktrees/backend-dev feature/backend-development
git worktree add ../ReactDjango-Hub-worktrees/frontend-dev feature/frontend-development

# Vérification
git worktree list
```

### Lancement Agents
```bash
# Lancement tous agents parallèle
make claude-agents

# Ou individuellement
make claude-backend-api
make claude-frontend
```

## 💻 VS Code Configuration

### Extensions Recommandées
```json
{
  "recommendations": [
    "ms-python.python",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "ms-toolsai.jupyter",
    "ms-python.black-formatter"
  ]
}
```

### Tasks & Terminal Profiles
Les tâches Claude Code sont pré-configurées:
- `Cmd+Shift+P` → "Tasks: Run Task"
- `🔧 Start Backend + API Agent`
- `🎨 Start Frontend Agent`
- `🤖 Start Agentrooms`

## 🐳 Docker Development

### Services Infrastructure
```bash
# Base services (DB, Redis, etc.)
docker-compose up -d db redis

# Development complet
docker-compose up -d

# Vérification
docker-compose ps
```

### Configuration Docker
```yaml
# docker-compose.yml sections principales
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: medical_saas
      
  redis:
    image: redis:7-alpine
    
  backend:
    build: ./backend
    ports:
      - "8000:8000"
```

## 🧪 Tests & Qualité

### Backend Tests
```bash
cd backend

# Tests Django
python manage.py test

# Tests Pytest avec couverture  
pytest --cov=apps

# Tests agents Claude Code
pytest tests/agent_tests/ -v

# Tests intégration médicale
pytest tests/integration/ -v
```

### Frontend Tests
```bash
cd frontend

# Tests composants
npm run test

# Tests agents React
npm run test -- src/tests/component-generation/

# Coverage
npm run test:coverage
```

### Qualité Code
```bash
# Formatage automatique
make claude-format

# Sécurité
make claude-security

# Conformité RGPD
make rgpd-check

# Qualité complète
make claude-quality
```

## 🔒 Sécurité & Conformité

### Chiffrement Données Médicales
```python
# Configuration chiffrement
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')

# Utilisation models
from encrypted_model_fields.fields import EncryptedTextField

class Patient(BaseModel):
    nom = EncryptedTextField(max_length=100)
    diagnostic = EncryptedTextField()
```

### Audit Logging RGPD
```python
# Configuration audit
AUDITLOG_INCLUDE_ALL_MODELS = True

# Enregistrement models
from auditlog.registry import auditlog
auditlog.register(Patient)
```

## 📊 Monitoring & Debug

### Django Debug Toolbar
- Activé en développement
- URL: `/__debug__/`
- Profiling SQL queries

### Silk Profiling
- URL: `/silk/`
- Performance monitoring
- API response times

### Health Checks
```bash
# Vérification système
curl http://localhost:8000/health/

# Status services
docker-compose ps
```

## 🌐 Développement Trilingue

### Configuration i18n
```python
# settings.py
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'

LANGUAGES = [
    ('fr', 'Français'),      # Primaire
    ('de', 'Deutsch'),       # Secondaire  
    ('en', 'English'),       # Tertiaire
]
```

### Medical Translator Agent
```bash
# Usage traduction médicale
claude "Traduire 'intervention chirurgicale' en allemand et anglais avec contexte médical précis"
```

## 🚀 Démarrage Rapide

### Commande Unique
```bash
# Setup et lancement complet
make claude-setup && make claude-agents
```

### Vérification Installation
```bash
# Backend API
curl http://localhost:8000/api/v1/
curl http://localhost:8000/api/ninja/

# Frontend
open http://localhost:5173

# Admin Django
open http://localhost:8000/admin/
```

## 📝 Prochaines Étapes

1. **Configuration Spécifique**: Adapter .env à votre environnement
2. **Agents Claude Code**: Lancer développement parallèle
3. **Tests**: Valider setup avec `make claude-test`
4. **Documentation**: Consulter `/docs/` pour guides spécialisés

---

*Guide maintenu par les agents Claude Code - Version française pour SaaS médical*