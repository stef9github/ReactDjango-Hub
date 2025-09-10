# Roadmap PublicHub 2025-2027
*Plan d'Exécution Réaliste avec Équipe Deux Fondateurs*

## Vue d'Ensemble

Cette roadmap reflète la réalité d'un développement avec un développeur solo assisté par IA et Nicolas Mangin gérant le développement business. Le planning priorise les fonctionnalités de démonstration pour le Salon des Maires (19-21 novembre 2025) et un MVP fonctionnel début 2026, avec levée de fonds ciblée mai-juin 2026.

## Philosophie de Développement

### Principes Fondamentaux
1. **Ship Early, Ship Often** - Déployer chaque semaine, feedback constant
2. **Demo First** - Construire pour les démonstrations avant la fonctionnalité complète
3. **Buy vs Build** - Utiliser services et librairies existants
4. **Progressive Enhancement** - Commencer simple, complexifier graduellement
5. **AI Acceleration** - Exploiter Claude Code pour gains productivité 2-3x

### Contraintes Réalistes
- **Un Développeur** - Impossible de paralléliser les tâches techniques
- **Pas d'équipe DevOps** - Utiliser services managés (Heroku/Railway)
- **Testing Limité** - Focus sur tests du chemin critique uniquement
- **Pas d'Infrastructure Custom** - Solutions prêtes à l'emploi
- **Customer Feedback Driven** - Construire uniquement ce qui est validé

## Timeline Détaillée

### Phase 1 : Foundation (Fin Septembre - Octobre 2025)
**Durée :** 5 semaines | **Objectif :** Environnement et architecture de base

#### Semaine 39 (22-28 Sept) : Setup Environnement
**Lundi-Mardi :**
- Configuration machine développement avec tous outils
- Setup Claude Code pour efficacité maximale
- Création repository GitHub et structure projet
- Configuration compte Railway/Heroku pour déploiement

**Mercredi-Jeudi :**
- Initialisation projet Django
- Setup base PostgreSQL (managée)
- Authentification basique avec django-allauth
- Configuration panel admin

**Vendredi-Dimanche :**
- Setup projet React avec Vite
- Configuration Tailwind CSS
- Sélection librairie composants (Shadcn/UI)
- Structure routing basique

**Livrables :**
- ✅ Environnement développement prêt
- ✅ Squelette Django + React déployé
- ✅ Authentification fonctionnelle
- ✅ Panel admin accessible

#### Semaine 40 (29 Sept - 5 Oct) : Modèles Core
**Lundi-Mardi :**
- Design schéma base de données (garder simple)
- Création modèles Django pour users, organisations
- Structure modèle appel d'offres basique
- Modèle document pour stockage

**Mercredi-Jeudi :**
- Personnalisation Django admin
- Endpoints API basiques avec Django REST
- Flows inscription et connexion utilisateur
- Création organisation

**Vendredi-Dimanche :**
- Composants React authentification
- Layout dashboard basique
- Structure navigation
- Premier déploiement staging

### Phase 2 : MVP Démo (Novembre 2025)
**Durée :** 3 semaines | **Objectif :** Démonstration Salon des Maires

#### Semaines 41-44 (Oct 6 - Nov 2) : Fonctionnalités Démo
**Priorités Absolues :**
1. Génération CCTP depuis templates
2. Export PDF fonctionnel
3. Interface professionnelle
4. Données de démo convaincantes
5. Flow de démonstration fluide

**Livrables Salon des Maires :**
- ✅ Application prête pour démo
- ✅ Plans de secours pour pannes
- ✅ Matériels démo préparés
- ✅ 100+ démos données
- ✅ 50+ inscriptions beta
- ✅ 20+ Lettres d'Intention

### Phase 3 : Beta MVP (Décembre 2025 - Janvier 2026)
**Durée :** 8 semaines | **Objectif :** Produit fonctionnel premiers clients

#### Décembre 2025 : Développement Beta
**Semaine 48 (24-30 Nov) :** Intégration Feedback Salon
- Priorisation feedback Salon
- Implémentation quick wins
- Corrections bugs critiques
- Améliorations onboarding

**Semaine 49 (1-7 Déc) :** Intégration BOAMP
- Recherche API BOAMP
- Setup scraping basique
- Fonctionnalité affichage appels d'offres
- Capacités recherche et filtrage

**Semaine 50 (8-14 Déc) :** Gestion Utilisateurs
- Management organisations
- Rôles et permissions utilisateurs
- Système d'invitation
- Logging activité

**Semaine 51 (15-21 Déc) :** Lancement Beta
- Déploiement production
- Onboarding utilisateurs beta
- Setup système support
- Sessions formation utilisateurs

**Livrables Décembre :**
- ✅ 10+ utilisateurs beta actifs
- ✅ Intégration BOAMP fonctionnelle
- ✅ MVP déployé en production
- ✅ Premiers revenus (2-3K€ MRR)

#### Janvier 2026 : Amélioration MVP
**Semaine 2 (5-11 Jan) :** Fonctionnalités Collaboration
- Commentaires sur documents
- Historique versions basique
- Fonctionnalité partage
- Notifications email

**Semaine 3 (12-18 Jan) :** Amélioration Analytics
- Statistiques marchés publics
- Tracking coûts
- Métriques gain de temps
- Génération rapports

**Semaine 4 (19-25 Jan) :** Intégration Paiement
- Setup Stripe
- Plans abonnement
- Flows paiement
- Gestion période d'essai

**Livrables Janvier :**
- ✅ 20+ clients payants
- ✅ 5K€ MRR atteint
- ✅ Système paiement opérationnel
- ✅ Fonctionnalités core stables

### Phase 4 : Enhancement (Février - Avril 2026)
**Durée :** 12 semaines | **Objectif :** Production-ready avec clients payants

#### Février 2026 : Qualité Production
**Semaines 5-6 (1-14 Fév) :** Fonctionnalités IA
- Intégration API OpenAI
- Suggestions CCTP intelligentes
- Extraction exigences
- Vérification conformité

**Semaines 7-8 (15-28 Fév) :** Polish & Optimisation
- Améliorations performance
- Audit sécurité
- Conformité RGPD
- Systèmes backup

**Livrables Février :**
- ✅ 35+ clients payants
- ✅ 15K€ MRR atteint
- ✅ Fonctionnalités IA opérationnelles
- ✅ Stabilité grade production

#### Mars 2026 : Fonctionnalités Croissance
**Semaines 9-10 (1-14 Mars) :** Fonctionnalités Avancées
- Capacités recherche avancée
- Opérations bulk
- Développement API
- Webhooks intégration

**Semaines 11-12 (15-31 Mars) :** Expansion Marché
- Préparation support multi-langue
- Fonctionnalités entreprise
- Permissions avancées
- Capacités white-label

**Livrables Mars :**
- ✅ 50+ clients payants
- ✅ 25K€ MRR atteint
- ✅ 110% net revenue retention
- ✅ Plateforme scalable

#### Avril 2026 : Préparation Pre-Seed
**Semaines 13-14 (1-14 Avr) :** Dette Technique
- Refactoring code
- Amélioration couverture tests
- Complétion documentation
- Optimisation architecture

**Semaines 15-16 (15-30 Avr) :** Investor Ready
- Dashboard métriques
- Analytics croissance
- Documentation technique
- Preuve scalabilité

**Livrables Avril :**
- ✅ 75+ clients payants
- ✅ 40K€ MRR atteint
- ✅ Dette technique minimale
- ✅ Codebase investor-ready

### Phase 5 : Pre-Seed (Mai - Juin 2026)
**Durée :** 8 semaines | **Objectif :** Plateforme investment-ready

#### Mai 2026 : Période Levée de Fonds
- Maintenance et support
- Support clients
- Ajouts fonctionnalités mineures
- Préparations démos investisseurs
- **Cible :** 55K€ MRR

#### Juin 2026 : Planification Transition
- Préparation embauches
- Architecture pour équipe
- Documentation connaissances
- Planning handover
- **Cible :** 75K€ MRR

**Livrables Mai-Juin :**
- ✅ 100+ clients payants
- ✅ 60K€ MRR atteint
- ✅ Pre-seed fermé (500-750K€)
- ✅ Prêt pour expansion équipe

### Phase 6 : Préparation Scale (Juillet 2026+)
**Durée :** Ongoing | **Objectif :** Readiness expansion équipe

#### S2 2026 : Leader National
**T3 2026 Focus :**
- Équipe de 5-7 personnes
- Rollout fonctionnalités avancées
- Expansion régionale
- Deals entreprise (3-5 départements)
- **Cible :** 100K€ MRR en septembre

**T4 2026 Focus :**
- 200+ clients
- Présence nationale établie
- Préparation Series Seed (2-3M€)
- Maturité plateforme atteinte
- **Cible :** 150K€ MRR en décembre

## Allocation Ressources

### Co-Fondateur Technique (100% temps)
- 60% Développement (coding effectif)
- 20% Debugging/Testing (trouver et corriger issues)
- 10% DevOps/Deploy (releases et monitoring)
- 5% Documentation (docs critiques uniquement)
- 5% Planning (sprint planning)

### Nicolas Mangin - PDG (100% temps)
- 30% Ventes & BD (exploiter relations existantes)
- 25% Partenariats stratégiques (AFE, associations, réseau GE)
- 20% Leadership levée de fonds
- 15% Opérations & optimisation Six Sigma
- 10% Management advisory board

### Budget Pré-Financement
- Runway personnel : 0€ (autofinancé)
- Outils & Infrastructure : 500€/mois
- Marketing & Événements : 1 000€/mois
- Légal & Comptabilité : 500€/mois
- **Burn Total :** 2 000€/mois

### Budget Post Pre-seed (500-750K€)
- Runway : 18 mois
- Équipe : 2 co-fondateurs + 3-4 embauches
- Marketing : 3K€/mois
- Infrastructure : 1.5K€/mois
- **Burn Total :** 35K€/mois

## Stack Technologique (Optimisé Solo Dev)

### Backend
- **Framework :** Django 5.0 LTS + Django REST Framework
- **Database :** PostgreSQL (managé par Railway/Heroku)
- **Authentication :** django-allauth (social login ready)
- **Admin :** Django Admin (personnalisation extensive)
- **File Storage :** Cloudinary ou AWS S3
- **Background Jobs :** Django-RQ (simple Redis queue)
- **PDF Generation :** WeasyPrint
- **API Docs :** drf-spectacular (auto-généré)

### Frontend
- **Framework :** React 18 + Vite (fast refresh)
- **UI Library :** Shadcn/UI (composants pré-construits)
- **Styling :** Tailwind CSS (utility-first)
- **State :** Zustand (plus simple que Redux)
- **Forms :** React Hook Form + Zod
- **Tables :** TanStack Table
- **HTTP :** Axios avec interceptors
- **Icons :** Lucide React

### Infrastructure
- **Hosting :** Railway ou Heroku (zero DevOps)
- **CDN :** Cloudflare (tier gratuit)
- **Monitoring :** Sentry (error tracking)
- **Analytics :** Plausible (privacy-focused)
- **Email :** SendGrid ou Postmark
- **Payments :** Stripe (subscriptions)
- **AI :** OpenAI API (GPT-4)

## Priorisation Fonctionnalités

### Must-Have pour Démo (Novembre 2025)
1. Authentification et inscription utilisateur
2. Création et gestion organisation
3. Sélection template CCTP basique
4. Génération CCTP basée sur formulaire
5. Fonctionnalité export PDF
6. Upload et stockage documents
7. Dashboard basique
8. Apparence UI professionnelle

### Must-Have pour Beta (Janvier 2026)
1. Affichage appels d'offres BOAMP (caché)
2. Bibliothèque templates documents
3. Collaboration basique (commentaires)
4. Notifications email
5. Fonctionnalité recherche
6. Historique activité
7. Intégration paiement
8. Analytics basiques

### Must-Have pour Production (Mars 2026)
1. Suggestions propulsées par IA
2. Recherche et filtres avancés
3. Opérations bulk
4. API pour intégrations
5. Optimisation performance
6. Hardening sécurité
7. Conformité RGPD
8. Analytics compréhensifs

### Explicitement Différé (Post-Financement)
1. Applications mobiles
2. Automation workflow complexe
3. Collaboration temps réel
4. Analyse IA avancée
5. Architecture multi-tenant
6. Split microservices
7. Intégrations custom
8. Internationalisation
9. Capacités offline
10. Reporting avancé

## Métriques de Succès & Jalons

### T4 2025 (Sept-Déc)
- ✅ Démo montrée au Salon des Maires
- ✅ 10+ clients beta
- ✅ 2-3K€ MRR
- ✅ Signaux product-market fit

### T1 2026 (Jan-Mars)
- ✅ 50+ clients
- ✅ 25K€ MRR
- ✅ Toujours 2 co-fondateurs (pas d'embauches encore)
- ✅ 2-3 partenariats en formation

### T2 2026 (Avr-Juin)
- ✅ 100+ clients
- ✅ 75K€ MRR
- ✅ Pre-seed fermé (500-750K€)
- ✅ Équipe de 5 personnes

### S2 2026 (Juil-Déc)
- ✅ 200+ clients
- ✅ 150K€ MRR
- ✅ Position marché forte
- ✅ Préparation Series Seed (2-3M€)

## Facteurs Critiques de Succès

1. **Vitesse d'Exécution** - Avantage first-mover dans marchés publics propulsés IA
2. **Obsession Client** - Compréhension profonde besoins secteur public
3. **Excellence Produit** - 10x meilleur que solutions existantes
4. **Partenariats Stratégiques** - Exploiter associations et canaux
5. **Efficacité Capital** - Accomplir plus avec moins, étendre runway
6. **Qualité Équipe** - Embaucher A-players qui comprennent la mission
7. **Effets Réseau** - Construire valeur plateforme qui se compose

---

*"Construire pour la démo, puis pour le client, puis pour le scale - dans cet ordre."*