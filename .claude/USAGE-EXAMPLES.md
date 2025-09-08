# Claude Code Agent Usage Examples

## Current Status
**Note**: `claude-squad` command is not yet available. Use alternative methods below.

## Example Workflows - When claude-squad becomes available

### French Medical Development Scenarios

#### 1. Adding RGPD Audit Logging to Patient Model
```bash
# Backend agent implements RGPD-compliant audit logging
claude-squad backend "Ajouter l'audit logging RGPD au modèle Patient français avec conformité CNIL"

# Code review agent validates compliance
claude-squad code-review "Vérifier la conformité RGPD de l'audit logging Patient"

# Documentation agent updates compliance docs
claude-squad documentation "Mettre à jour la documentation RGPD pour l'audit Patient"
```

#### 2. Creating Surgical Dashboard with Trilingual Support
```bash
# Frontend agent creates French-first UI
claude-squad frontend "Créer dashboard chirurgical avec métriques en français"

# Medical translator adds German and English
claude-squad medical-translator "Traduire interface dashboard vers allemand et anglais"

# API agent provides data endpoints
claude-squad api "Ajouter endpoints analytics pour métriques chirurgicales"
```

#### 3. Full Feature Development Workflow
```bash
# 1. Backend: Create surgical procedure tracking
claude-squad backend "Implémenter suivi procédures chirurgicales avec modèles Django français"

# 2. API: Add endpoints with trilingual documentation  
claude-squad api "Créer endpoints REST pour procédures avec docs FR/DE/EN"

# 3. Frontend: Build surgical procedure interface
claude-squad frontend "Créer interface gestion procédures chirurgicales français"

# 4. Translation: Localize medical terminology
claude-squad medical-translator "Traduire terminologie chirurgicale vers DE/EN"

# 5. Review: Validate RGPD compliance
claude-squad code-review "Valider conformité RGPD système procédures chirurgicales"

# 6. Deploy: Release to staging with health checks
claude-squad deployment "Déployer procédures chirurgicales sur staging avec tests EC2"

# 7. Document: Update API and user documentation
claude-squad documentation "Documenter nouvelles fonctionnalités procédures chirurgicales"
```

## Alternative Current Approaches (Until claude-squad available)

### Method 1: Direct Context References
```bash
# Reference specific agent configuration
claude "Acting as the backend agent (see .claude/agents/backend-agent.md), implement RGPD audit logging for the Patient model with French medical compliance and CNIL guidelines"

# Chain multiple agent contexts
claude "Using the frontend agent configuration (.claude/agents/frontend-agent.md), create a surgical dashboard in French, then use medical translator config to add German/English support"
```

### Method 2: Step-by-Step Agent Emulation
```bash
# Step 1: Backend development with French context
claude "En tant qu'agent backend Django spécialisé médical français, créer modèle Patient avec audit RGPD selon directives CNIL"

# Step 2: Frontend development with trilingual support  
claude "En tant qu'agent frontend React pour marché médical français, créer dashboard patient avec traductions automatiques DE/EN"

# Step 3: Quality validation
claude "En tant qu'agent code review, valider conformité RGPD et sécurité système Patient français"
```

## Medical Context Examples

### RGPD Compliance Features
```bash
# When claude-squad available:
claude-squad backend "Implémenter droits RGPD (accès, rectification, oubli) pour données Patient"
claude-squad code-review "Auditer implémentation droits RGPD selon Article 15-21"
claude-squad documentation "Documenter procédures exercice droits RGPD patients"

# Current alternative:
claude "Using backend agent expertise, implement RGPD patient rights (access, rectification, erasure) according to French CNIL guidelines and Code de la santé publique"
```

### Surgical Terminology Translation  
```bash
# When claude-squad available:
claude-squad medical-translator "Créer dictionnaire terminologie chirurgicale FR→DE→EN pour spécialités orthopédie, cardiologie, neurochirurgie"

# Current alternative:
claude "Acting as medical translator specialist, create comprehensive surgical terminology dictionary French→German→English for orthopedics, cardiology, neurosurgery with medical accuracy"
```

### EC2 Deployment with Health Checks
```bash
# When claude-squad available:
claude-squad deployment "Déployer application médicale sur EC2 avec auto-scaling et health checks conformité RGPD"

# Current alternative:  
claude "Using deployment agent EC2 CLI expertise, deploy French medical SaaS with auto-scaling, health monitoring, and RGPD-compliant infrastructure in EU region"
```

## Integration Patterns

### Cross-Agent Workflows
```bash
# Full stack feature (when claude-squad available):
claude-squad backend "Créer modèle AnalyseMedicale" && \
claude-squad api "Ajouter endpoints analyse avec auth" && \
claude-squad frontend "Interface analyse médicale français" && \
claude-squad medical-translator "Traduire interface analyse DE/EN" && \
claude-squad code-review "Valider sécurité analyse médicale" && \
claude-squad deployment "Déployer analyse sur production EC2"
```

### Emergency Hotfix Workflow
```bash
# Critical RGPD compliance fix (when claude-squad available):
claude-squad backend "Fix critique: fuite données Patient dans logs système"
claude-squad code-review "Audit urgence: vérifier étanchéité données Patient"  
claude-squad deployment "Déploiement hotfix RGPD immédiat avec rollback plan"
```

## Migration Checklist

### When claude-squad becomes available:
1. **Test Command**: `claude-squad --help && claude-squad --list-agents`
2. **Validate Agents**: Test each agent responds correctly
3. **Update Scripts**: Replace alternative methods with claude-squad
4. **Team Training**: Introduce new commands to development team
5. **CI/CD Integration**: Update automated workflows

### Current Development Process:
1. **Reference Agent Files**: Always specify which agent configuration to use
2. **French-First Context**: Specify French medical market requirements  
3. **RGPD Compliance**: Always mention CNIL guidelines and French regulations
4. **Trilingual Support**: Request French primary with German/English translations
5. **Medical Context**: Include surgical/medical terminology requirements

## Quick Reference

| **Task Type** | **Agent** | **Current Command Pattern** |
|--------------|-----------|----------------------------|
| Django Models/APIs | Backend | `claude "As backend agent (see .claude/agents/backend-agent.md), [task] with RGPD compliance"` |
| React Components | Frontend | `claude "As frontend agent, create [component] in French with automatic DE/EN translation"` |
| API Endpoints | API | `claude "As API agent, implement [endpoint] with trilingual documentation"` |
| Medical Translation | Medical Translator | `claude "As medical translator, translate [content] from French to German/English"` |
| RGPD Review | Code Review | `claude "As code review agent, validate RGPD compliance of [feature]"` |
| EC2 Deployment | Deployment | `claude "As deployment agent with EC2 CLI expertise, deploy [feature]"` |
| Documentation | Documentation | `claude "As documentation agent, create French medical docs for [feature]"` |

This ensures comprehensive development workflow automation while maintaining French medical market focus and RGPD compliance! 🇫🇷🏥