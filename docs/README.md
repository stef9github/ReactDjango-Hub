# ReactDjango Hub - Documentation

> **Plateforme SaaS Médicale Française** - Documentation complète pour le développement avec Claude Code

## 📋 Table des Matières

### 🏥 [Marché Français](./french-market/)
Documentation spécifique au marché médical français
- **[Spécifications SaaS Chirurgien](./french-market/specifications-chirurgien.md)** - Cahier des charges complet
- **[Conformité RGPD](./compliance/rgpd-compliance.md)** - Conformité données médicales françaises
- **[Terminologie Médicale](./french-market/medical-terminology.md)** - Glossaire FR/DE/EN

### 🏗️ [Architecture](./architecture/)
Structure technique et conception système
- **[Vue d'ensemble](./architecture/overview.md)** - Architecture globale du système
- **[Base de données](./architecture/database.md)** - Modèles Django et PostgreSQL
- **[APIs](./architecture/api-design.md)** - DRF + Django Ninja endpoints
- **[Sécurité](./architecture/security.md)** - Chiffrement et permissions

### 🤖 [Agents Claude Code](./agents/)
Système d'agents spécialisés pour le développement
- **[Vue d'ensemble](./agents/overview.md)** - Système d'agents et responsabilités
- **[Backend + API Agent](./agents/backend-api-agent.md)** - Développement Django complet
- **[Frontend Agent](./agents/frontend-agent.md)** - Composants React trilingues
- **[Flux de travail](./agents/workflow.md)** - Coordination et commits

### 💻 [Développement](./development/)
Guide de développement et bonnes pratiques
- **[Configuration](./development/setup.md)** - Environment de développement
- **[Standards Code](./development/coding-standards.md)** - Conventions et qualité
- **[Git Worktrees](./development/git-worktrees.md)** - Développement parallèle
- **[VS Code](./development/vscode-integration.md)** - Intégration IDE
- **[Communication Inter-Agents](./development/inter-agent-communication.md)** - Protocoles Claude Code
- **[Optimisation Agents](./development/agent-optimization-guide.md)** - Performance et efficacité

### 🔌 [API](./api/)
Documentation des APIs REST
- **[Endpoints DRF](./api/drf-endpoints.md)** - APIs Django REST Framework
- **[Endpoints Ninja](./api/ninja-endpoints.md)** - APIs FastAPI-style
- **[Authentification](./api/authentication.md)** - Sécurité et permissions
- **[Documentation OpenAPI](./api/openapi-spec.md)** - Spécifications Swagger

### 🧪 [Tests](./testing/)
Stratégie et framework de tests
- **[Tests Agents](./testing/agent-testing.md)** - Validation génération de code
- **[Tests API](./testing/api-testing.md)** - Tests endpoints et intégration
- **[Tests Médical](./testing/medical-testing.md)** - Contexte médical français
- **[Performance](./testing/performance.md)** - Benchmarks et optimisation

### ⚖️ [Conformité](./compliance/)
Conformité légale et médicale française
- **[RGPD Article 9](./compliance/rgpd-article-9.md)** - Données sensibles médicales
- **[CNIL](./compliance/cnil-guidelines.md)** - Recommandations autorité française
- **[Code Santé Publique](./compliance/code-sante-publique.md)** - Réglementation médicale
- **[Audit Trail](./compliance/audit-logging.md)** - Traçabilité des données

### 🚀 [Déploiement](./deployment/)
Infrastructure et mise en production
- **[AWS Infrastructure](./deployment/aws-setup.md)** - Configuration cloud
- **[Docker](./deployment/docker.md)** - Containerisation
- **[Monitoring](./deployment/monitoring.md)** - Surveillance système
- **[CI/CD](./deployment/cicd.md)** - Pipelines automatisées

## 🎯 Navigation Rapide

### Pour Commencer
1. 📖 [Spécifications Métier](./french-market/specifications-chirurgien.md)
2. 🏗️ [Architecture Overview](./architecture/overview.md)
3. 🤖 [Configuration Agents](./agents/overview.md)
4. 💻 [Setup Développement](./development/setup.md)

### Développeurs
- 🔧 [Backend + API Guide](./agents/backend-api-agent.md)
- 🎨 [Frontend Guide](./agents/frontend-agent.md)
- 🧪 [Testing Framework](./testing/agent-testing.md)
- ⚖️ [RGPD Compliance](./compliance/rgpd-compliance.md)

### DevOps
- 🚀 [Deployment Guide](./deployment/aws-setup.md)
- 🐳 [Docker Setup](./deployment/docker.md)
- 📊 [Monitoring](./deployment/monitoring.md)

---

## 📝 Convention de Documentation

- **Langue Principale**: Français (marché cible)
- **Langues Secondaires**: Allemand et Anglais pour référence
- **Format**: Markdown avec support Mermaid pour diagrammes
- **Maintenance**: Agents Claude Code maintiennent la documentation

## 🆘 Support

Pour questions spécifiques au développement avec Claude Code:
- **Issues**: [GitHub Issues](https://github.com/anthropics/claude-code/issues)  
- **Agents**: Utiliser les agents spécialisés dans `.claude/agents/`
- **Documentation**: Ce répertoire `/docs/`

---
*Documentation maintenue par Claude Code Agents - Version française pour SaaS médical*