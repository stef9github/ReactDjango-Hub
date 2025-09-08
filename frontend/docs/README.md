# Frontend Documentation

Documentation spécifique au frontend React de la plateforme médicale SaaS.

## 📁 Structure

- **`components/`** - Bibliothèque de composants React réutilisables
- **`pages/`** - Documentation des pages et routing
- **`styling/`** - Système de design Tailwind CSS et thèmes
- **`routing/`** - Navigation et protection des routes
- **`state-management/`** - Gestion d'état React (Context, Redux, etc.)
- **`testing/`** - Tests frontend, Jest, React Testing Library
- **`deployment/`** - Build et déploiement frontend

## 🎨 Frontend Agent Workflow

Cette documentation est maintenue par l'**Agent Frontend** Claude qui fonctionne dans le worktree `frontend-dev`.

### Commandes spécifiques Frontend Agent

```bash
# Dans frontend-dev worktree
git fcommit "docs: update component documentation"

# Tests frontend uniquement
npm test
npm run test:coverage

# Build et preview
npm run build
npm run preview
```

## 🇫🇷 Interface Française-Première

- **UI français natif** - Interface conçue pour utilisateurs français
- **i18n** - Traduction automatique vers DE/EN
- **Accessibilité** - WCAG 2.1 AA compliance
- **Design médical** - UX adaptée aux professionnels de santé

## 📱 Technologies

- **React 18** - Composants fonctionnels avec hooks
- **TypeScript** - Typage statique complet
- **Tailwind CSS** - Styling utility-first
- **Vite** - Build tool moderne et rapide

## 📚 Guides Rapides

- [Component Library](./components/) - Composants réutilisables
- [Styling Guide](./styling/) - Système de design et thèmes
- [State Management](./state-management/) - Patterns de gestion d'état
- [Testing Patterns](./testing/) - Tests composants et E2E