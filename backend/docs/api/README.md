# Backend API Documentation

Documentation complète des APIs REST de la plateforme médicale SaaS.

## 🏥 **Vue d'ensemble**

Cette API REST utilise Django REST Framework pour fournir des endpoints sécurisés et conformes RGPD pour la gestion des données médicales.

## 🔐 **Authentication**

### JWT Token Authentication

```bash
# Obtenir un token
POST /api/auth/login/
{
  "username": "doctor@example.com",
  "password": "secure_password"
}

# Utiliser le token
Authorization: Bearer <jwt_token>
```

### Endpoints Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login/` | Connexion utilisateur |
| `POST` | `/api/auth/logout/` | Déconnexion |
| `POST` | `/api/auth/refresh/` | Refresh token JWT |
| `GET` | `/api/auth/user/` | Profil utilisateur actuel |

## 👥 **Patients API**

### Modèle Patient

```python
class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)  
    birth_date = models.DateField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    # RGPD compliance fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Endpoints Patients

| Method | Endpoint | Description | Permissions |
|--------|----------|-------------|-------------|
| `GET` | `/api/patients/` | Liste paginée des patients | `view_patient` |
| `POST` | `/api/patients/` | Créer un nouveau patient | `add_patient` |
| `GET` | `/api/patients/{id}/` | Détails d'un patient | `view_patient` |
| `PUT` | `/api/patients/{id}/` | Modifier un patient | `change_patient` |
| `DELETE` | `/api/patients/{id}/` | Supprimer un patient (soft delete) | `delete_patient` |

### Exemple Réponse

```json
{
  "id": 1,
  "first_name": "Jean",
  "last_name": "Dupont",
  "birth_date": "1985-03-15",
  "phone": "+33123456789",
  "email": "jean.dupont@email.com",
  "address": "123 Rue de la Santé, 75014 Paris",
  "created_at": "2024-09-08T10:30:00Z",
  "updated_at": "2024-09-08T10:30:00Z"
}
```

## 📅 **Appointments API**

### Modèle Appointment

```python
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
```

### Endpoints Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/appointments/` | Liste des rendez-vous |
| `POST` | `/api/appointments/` | Créer un rendez-vous |
| `GET` | `/api/appointments/{id}/` | Détails d'un rendez-vous |
| `PUT` | `/api/appointments/{id}/` | Modifier un rendez-vous |

## 🔍 **Filtering & Pagination**

### Query Parameters

```bash
# Pagination
GET /api/patients/?page=2&page_size=20

# Filtering
GET /api/patients/?search=dupont
GET /api/appointments/?date_from=2024-09-01&date_to=2024-09-30

# Ordering
GET /api/patients/?ordering=-created_at
```

## 🚨 **Error Responses**

### Format Standard

```json
{
  "error": "validation_error",
  "message": "Les données fournies ne sont pas valides",
  "details": {
    "email": ["Cette adresse email est déjà utilisée"],
    "phone": ["Le numéro de téléphone doit contenir 10 chiffres"]
  }
}
```

### Codes HTTP

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (token required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## 🔒 **Sécurité & RGPD**

### Permissions par Rôle

```python
# Docteur
- view_patient, add_patient, change_patient
- view_appointment, add_appointment, change_appointment

# Secrétaire  
- view_patient, add_patient
- view_appointment, add_appointment

# Administrateur
- All permissions
```

### Audit Trail

Tous les accès aux données patients sont loggés :

```python
# models.py
class PatientAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)  # 'view', 'create', 'update'
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
```

## 🔗 **Frontend Integration**

> 💡 **Pour l'Agent Frontend**: Consultez `frontend/docs/api/README.md` pour l'intégration côté React, types TypeScript, et exemples d'utilisation.

### Schéma OpenAPI

Le schéma complet est généré automatiquement :

```bash
# Générer le schéma OpenAPI
python manage.py spectacular --file schema.yml

# Accessible via 
GET /api/schema/
GET /api/docs/  # Swagger UI
```

## 📝 **Génération de Documentation**

### Auto-génération

```bash
# Générer la doc API
python manage.py generate_api_docs

# Mise à jour des types TypeScript pour frontend
python manage.py export_typescript_types > ../frontend/src/api/types.ts
```

---

🤖 **Maintenu par Backend Agent** - Cette documentation est automatiquement mise à jour lors des commits avec `git bcommit`.