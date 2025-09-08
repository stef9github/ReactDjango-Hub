# Backend Documentation

Documentation spécifique au backend Django de la plateforme médicale SaaS.

## 📁 Structure

- **`api/`** - Documentation des endpoints API REST
- **`models/`** - Schémas des modèles Django et relations
- **`database/`** - Migrations, schémas et optimisations base de données
- **`authentication/`** - Système d'authentification et autorisations RBAC
- **`testing/`** - Tests backend, fixtures et mocking
- **`deployment/`** - Configuration et déploiement backend

## 🔧 Backend Agent Workflow

Cette documentation est maintenue par l'**Agent Backend** Claude qui fonctionne dans le worktree `backend-dev`.

### Commandes spécifiques Backend Agent

```bash
# Dans backend-dev worktree
git bcommit "docs: update API documentation"

# Tests backend uniquement  
python manage.py test
pytest apps/ --cov

# Linting backend
black apps/ --line-length=88
flake8 apps/
```

## 🏥 Conformité Médicale

- **RGPD** - Protection des données patients
- **HIPAA** - Conformité médicale US (si applicable)
- **Audit trails** - Traçabilité complète des accès données

## 📚 Guides Rapides

- [API Endpoints](./api/) - Tous les endpoints REST disponibles
- [Models Guide](./models/) - Relations et validations des modèles
- [Authentication](./authentication/) - JWT, permissions, rôles
- [Testing Strategy](./testing/) - Tests unitaires et d'intégration