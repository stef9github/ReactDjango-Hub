# Configuration Marché Français - Medical SaaS Platform
# French Market Configuration - Medical SaaS Platform

## 🇫🇷 Configuration Française Principale

### Localisation
- **Langue Principale**: Français (fr-fr)
- **Langues Supportées**: Français → Allemand → Anglais
- **Fuseau Horaire**: Europe/Paris
- **Localisation**: USE_I18N=True, USE_L10N=True

### Conformité RGPD
- **Conformité**: RGPD (Règlement Général sur la Protection des Données)
- **Autorité**: CNIL (Commission Nationale de l'Informatique et des Libertés)
- **Code Médical**: Code de la santé publique français
- **Article 9 RGPD**: Protection spéciale des données de santé

## 🏥 Contexte Médical Français

### Réglementation
- **Ordre des médecins**: Normes du conseil médical français
- **CNIL**: Directives de l'autorité française de protection des données
- **Code de la santé publique**: Conformité au code de la santé français
- **RGPD Article 9**: Protection spéciale pour les données de santé

### Terminologie Chirurgicale
```yaml
Procédures Principales:
  - Appendicectomie (Appendectomy / Blinddarmoperation)
  - Cholécystectomie (Cholecystectomy / Gallenblasenentfernung)
  - Arthroplastie (Arthroplasty / Gelenkersatz)
  - Craniotomie (Craniotomy / Kraniotomie)
  - Laparoscopie (Laparoscopy / Laparoskopie)
  - Endoscopie (Endoscopy / Endoskopie)
```

## ⚙️ Configuration Technique

### Django Settings
```python
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
LANGUAGES = [
    ('fr', 'Français'),      # Langue principale - Marché français
    ('de', 'Deutsch'),       # Support allemand
    ('en', 'English'),       # Traduction anglaise
]
```

### Agents Claude Code Configurés

| **Agent** | **Focus Français** | **Spécialisation** |
|-----------|-------------------|-------------------|
| 🔧 **Backend Agent** | Django + RGPD | Conformité française, audit logging CNIL |
| 🎨 **Frontend Agent** | Interface française | UI français-première avec traductions |
| 🔌 **API Agent** | APIs conformes RGPD | Documentation trilingue, sécurité française |
| 🔍 **Code Review Agent** | Contrôle RGPD | Validation conformité française |
| 🚀 **Deployment Agent** | Infrastructure EU | Déploiement conforme RGPD en Europe |
| 📚 **Documentation Agent** | Docs françaises | Documentation médicale française |
| 🌍 **Medical Translator** | FR → DE/EN | Traduction médicale française primaire |

## 📋 Droits RGPD Implémentés

### Droits des Personnes
- **Droit à l'information** (Articles 13-14 RGPD)
- **Droit d'accès** (Article 15 RGPD)
- **Droit de rectification** (Article 16 RGPD)
- **Droit à l'effacement** (Article 17 RGPD)
- **Droit à la limitation** (Article 18 RGPD)
- **Droit à la portabilité** (Article 20 RGPD)
- **Droit d'opposition** (Article 21 RGPD)

### Conservation des Données
- **Dossiers patients**: 20 ans (Code de la santé publique R.1112-7)
- **Imagerie médicale**: 20 ans (Code de la santé publique R.1112-7)
- **Données d'usage**: 3 ans (CNIL)
- **Logs d'accès**: 1 an (CNIL)

## 🔄 Workflow de Développement

### 1. Développement Français-Première
```bash
# Interface utilisateur créée en français
claude-squad frontend "Créer dashboard patient avec métriques chirurgicales"

# Backend développé avec terminologie française
claude-squad backend "Ajouter audit RGPD au modèle Patient français"
```

### 2. Traduction Automatique
```bash
# Traduction vers allemand et anglais
claude-squad medical-translator "Traduire formulaires chirurgicaux vers DE/EN"
```

### 3. Conformité RGPD
```bash
# Validation conformité française
claude-squad code-review "Vérifier conformité RGPD du système d'auth français"
```

## 🎯 Commandes Utiles

### Gestion des Traductions
```bash
# Générer fichiers de traduction
python manage.py makemessages -l fr -l de -l en

# Compiler traductions
python manage.py compilemessages

# Vérifier langue actuelle
python manage.py shell -c "from django.utils.translation import get_language; print(get_language())"
```

### Tests RGPD
```bash
# Tests conformité RGPD
python manage.py test apps.core.tests.test_rgpd_compliance

# Validation données personnelles
python manage.py check_personal_data_handling
```

## 📞 Support

### Contact RGPD
- **DPO**: Délégué à la Protection des Données
- **CNIL**: Commission Nationale de l'Informatique et des Libertés
- **Référence**: Code de la santé publique français

---

**Configuration pour le marché médical français avec support RGPD complet et traduction automatique vers l'allemand et l'anglais.** 🇫🇷🏥