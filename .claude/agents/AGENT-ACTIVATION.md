# Agent Activation Guide / Guide d'Activation des Agents

## Current Status / Statut Actuel
**Note**: `claude-squad` command is not yet available in this Claude Code installation. This documentation is prepared for future use when the feature becomes available.

**Note**: La commande `claude-squad` n'est pas encore disponible dans cette installation de Claude Code. Cette documentation est préparée pour une utilisation future lorsque la fonctionnalité sera disponible.

## Future Usage / Utilisation Future

### When claude-squad becomes available / Quand claude-squad sera disponible:

#### French Medical Development / Développement Médical Français
```bash
# Backend development with RGPD compliance
claude-squad backend "Ajouter audit RGPD au modèle Patient français"

# Frontend development with French-first UI
claude-squad frontend "Créer dashboard patient avec métriques chirurgicales"

# API development with trilingual docs
claude-squad api "Ajouter authentification aux endpoints analytics"

# Medical translation (French → German → English)
claude-squad medical-translator "Traduire formulaires chirurgicaux vers DE/EN"

# Code review with RGPD validation
claude-squad code-review "Vérifier conformité RGPD du système d'auth français"

# Deployment with EC2 CLI expertise
claude-squad deployment "Déployer sur staging avec health checks EC2"

# Documentation in French context
claude-squad documentation "Mettre à jour docs API pour nouveaux endpoints"
```

## Alternative Current Approach / Approche Actuelle Alternative

### Until claude-squad is available / En attendant que claude-squad soit disponible:

#### Method 1: Direct Claude with Context / Méthode 1: Claude direct avec contexte
```bash
# Backend development
claude "En tant qu'agent backend spécialisé Django pour marché médical français, ajouter audit RGPD au modèle Patient français avec conformité CNIL"

# Frontend development  
claude "En tant qu'agent frontend spécialisé React pour marché médical français, créer dashboard patient avec métriques chirurgicales en français"

# API development
claude "En tant qu'agent API spécialisé DRF+Ninja pour marché médical français, ajouter authentification aux endpoints analytics avec docs trilingues"
```

#### Method 2: Reference Agent Configuration / Méthode 2: Référencer la configuration d'agent
```bash
# Reference specific agent file
claude "Utilise la configuration de l'agent backend (.claude/agents/backend-agent.md) pour ajouter audit RGPD au modèle Patient"

# Multi-agent workflow
claude "Utilise les agents backend et medical-translator pour implémenter et traduire les formulaires patients"
```

## Agent Configuration Files / Fichiers de Configuration des Agents

All agents are fully configured in:
Tous les agents sont entièrement configurés dans:

```
.claude/agents/
├── README.md                    # Agent orchestration guide
├── backend-agent.md            # Django backend specialist (French market)
├── frontend-agent.md           # React frontend specialist (French-first)
├── api-agent.md               # API development & testing (trilingual)
├── code-review-agent.md       # Quality assurance (RGPD compliance)
├── deployment-agent.md        # DevOps with EC2 CLI expertise
├── documentation-agent.md     # Technical writing (French context)
└── medical-translator-agent.md # FR→DE/EN medical translation
```

## Migration Plan / Plan de Migration

### When claude-squad becomes available / Quand claude-squad devient disponible:

1. **Test Command Availability / Tester la Disponibilité de la Commande**:
   ```bash
   claude-squad --help
   claude-squad --list-agents
   ```

2. **Validate Agent Loading / Valider le Chargement des Agents**:
   ```bash
   claude-squad backend "Test connection"
   ```

3. **Update All Documentation / Mettre à Jour Toute la Documentation**:
   - Replace alternative methods with direct claude-squad usage
   - Update commit workflows and examples
   - Test all agent specializations

4. **Team Training / Formation de l'Équipe**:
   - Introduce claude-squad commands to development team
   - Update development workflows and CI/CD processes

## Current Workflow / Workflow Actuel

### Development Process / Processus de Développement
```bash
# 1. Reference agent configuration in prompts
claude "Acting as the backend agent for French medical SaaS (see .claude/agents/backend-agent.md), implement RGPD audit logging for the Patient model with French medical compliance"

# 2. Chain multiple agents
claude "First use backend agent config to create Patient model, then use medical-translator agent config to add French medical terminology with German/English translations"

# 3. Quality gate
claude "Using code-review agent configuration, validate the Patient model implementation for RGPD compliance and French medical standards"
```

This approach ensures all agent specializations are utilized effectively until claude-squad becomes available.

Cette approche garantit que toutes les spécialisations d'agents sont utilisées efficacement jusqu'à ce que claude-squad devienne disponible.