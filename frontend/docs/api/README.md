# API Integration Guide

Guide pour l'intégration des APIs backend dans le frontend React.

## 🔗 **Références API Backend**

L'agent frontend doit consulter la documentation API backend située dans :

```
../../backend/docs/api/     # Documentation complète des endpoints
../../docs/api/             # Schémas API globaux et contrats
```

## 📡 **Endpoints Principaux**

### Base URL
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

### Endpoints par Domaine

**Authentication** - `/api/auth/`
- `POST /api/auth/login/` - Connexion utilisateur
- `POST /api/auth/logout/` - Déconnexion
- `POST /api/auth/refresh/` - Refresh token JWT
- `GET /api/auth/user/` - Profil utilisateur actuel

**Patients** - `/api/patients/`
- `GET /api/patients/` - Liste des patients
- `POST /api/patients/` - Créer un patient
- `GET /api/patients/{id}/` - Détails d'un patient
- `PUT /api/patients/{id}/` - Modifier un patient

**Appointments** - `/api/appointments/`
- `GET /api/appointments/` - Liste des rendez-vous
- `POST /api/appointments/` - Créer un rendez-vous
- `PUT /api/appointments/{id}/` - Modifier un rendez-vous

> 📚 **Documentation détaillée :** Voir `backend/docs/api/` pour les schémas complets, validations et exemples de réponses.

## 🛠 **Client API TypeScript**

### Structure Recommandée

```typescript
// src/api/client.ts
export class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  // Methods pour chaque endpoint...
}

// src/api/types.ts - Types TypeScript générés depuis backend
export interface Patient {
  id: number
  first_name: string
  last_name: string
  birth_date: string
  // ... autres champs selon backend/docs/api/patients.md
}
```

## 🔄 **Synchronisation avec Backend**

### Contrat API Partagé

Le frontend et backend partagent un contrat API défini dans :
- `docs/api/schema.json` - Schéma OpenAPI/Swagger
- `docs/api/types.ts` - Types TypeScript partagés

### Workflow de Synchronisation

1. **Backend Agent** génère la documentation API
2. **Frontend Agent** consulte cette documentation  
3. **Types partagés** sont mis à jour automatiquement

```bash
# Générer les types depuis le schema backend
npm run api:generate-types
```

## 🧪 **Testing API Integration**

### Mock API pour Tests

```typescript
// src/api/__mocks__/client.ts
export const mockApiClient = {
  getPatients: jest.fn().mockResolvedValue([
    { id: 1, first_name: 'Jean', last_name: 'Dupont' }
  ]),
  // ... autres mocks
}
```

### Tests d'Intégration

```typescript
// src/api/__tests__/integration.test.ts
describe('API Integration', () => {
  it('should fetch patients list', async () => {
    const patients = await apiClient.getPatients()
    expect(patients).toHaveLength(2)
  })
})
```

## 🚨 **Gestion d'Erreurs**

### Codes d'Erreur Standards

- `400` - Validation error (données invalides)
- `401` - Authentication required
- `403` - Permission denied  
- `404` - Resource not found
- `500` - Server error

### Error Handling Pattern

```typescript
try {
  const patient = await apiClient.getPatient(id)
} catch (error) {
  if (error.status === 404) {
    showNotification('Patient introuvable', 'error')
  } else if (error.status === 403) {
    redirectToLogin()
  }
}
```

## 📋 **Checklist Frontend-Backend Sync**

- [ ] Types TypeScript à jour avec modèles Django
- [ ] Endpoints documentés dans `backend/docs/api/`
- [ ] Tests API côté frontend
- [ ] Gestion d'erreurs implémentée
- [ ] Validation des données côté frontend
- [ ] Performance (cache, pagination) optimisée

---

💡 **Tip**: Utilise `git bcommit` dans backend-dev pour mettre à jour la doc API, puis `git fcommit` dans frontend-dev pour synchroniser l'intégration.