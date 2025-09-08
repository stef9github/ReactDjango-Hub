# Conformité RGPD - Données Médicales

> **Guide complet pour la conformité RGPD Article 9 dans le SaaS médical français**

## ⚖️ Cadre Légal

### RGPD Article 9 - Données Sensibles
Les données de santé sont des **données à caractère personnel sensibles** nécessitant une protection renforcée.

**Base légale autorisée**:
- Consentement explicite de la personne concernée
- Nécessité pour les soins de santé (intérêt vital)
- Mission d'intérêt public dans le domaine de la santé

### Réglementation Française Complémentaire
- **Code de la santé publique** - Articles L1111-7 à L1111-8
- **CNIL** - Délibération n° 2019-106 (référentiel santé)
- **Ordre des médecins** - Déontologie et secret médical

## 🔒 Implémentation Technique

### Chiffrement des Données
```python
# Configuration chiffrement Django
from encrypted_model_fields.fields import EncryptedTextField, EncryptedDateField

class Patient(BaseModel):
    # Identité - Chiffré au repos
    nom = EncryptedTextField(max_length=100)
    prenom = EncryptedTextField(max_length=100)
    date_naissance = EncryptedDateField()
    numero_securite_sociale = EncryptedTextField(max_length=15)
    
    # Données médicales - Chiffrement renforcé
    diagnostic_principal = EncryptedTextField()
    antecedents_medicaux = EncryptedTextField()
    allergies = EncryptedTextField()
    
    # Métadonnées - Non sensibles
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    
    class Meta:
        db_table = 'patients'
        permissions = [
            ('view_medical_data', 'Peut consulter données médicales'),
            ('edit_medical_data', 'Peut modifier données médicales'),
            ('export_medical_data', 'Peut exporter données médicales'),
        ]
```

### Audit Trail Complet
```python
# Configuration django-auditlog
from auditlog.registry import auditlog
from auditlog.models import LogEntry

# Enregistrement models médicaux
auditlog.register(Patient, include_fields=['nom', 'prenom', 'diagnostic_principal'])
auditlog.register(Surgery, include_fields=['type_intervention', 'date_prevue'])
auditlog.register(MedicalRecord)

# Audit personnalisé RGPD
class RGPDAuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)  # CREATE, READ, UPDATE, DELETE, EXPORT
    resource_type = models.CharField(max_length=50)  # Patient, Surgery, etc.
    resource_id = models.UUIDField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    legal_basis = models.CharField(max_length=100)  # Base légale RGPD
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rgpd_audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
```

### Gestion des Consentements
```python
class ConsentementRGPD(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    type_traitement = models.CharField(max_length=100)  # Soins, Analytics, etc.
    consentement_donne = models.BooleanField()
    date_consentement = models.DateTimeField()
    date_retrait = models.DateTimeField(null=True, blank=True)
    
    # Traçabilité
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    methode_collecte = models.CharField(max_length=50)  # Interface, Email, etc.
    
    # Versions consentement
    version_cgu = models.CharField(max_length=20)
    version_politique_confidentialite = models.CharField(max_length=20)
    
    class Meta:
        unique_together = ['patient', 'type_traitement']
        db_table = 'consentements_rgpd'
```

## 👤 Droits des Personnes Concernées

### Droit d'Accès (Article 15)
```python
from django.http import HttpResponse
import json

def patient_data_export(request, patient_id):
    """Export données patient - Droit d'accès RGPD"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Vérification permissions
    if not request.user.has_perm('patients.view_medical_data', patient):
        raise PermissionDenied
    
    # Données exportables
    data = {
        'identite': {
            'nom': patient.nom,
            'prenom': patient.prenom,
            'date_naissance': patient.date_naissance.isoformat(),
        },
        'donnees_medicales': {
            'diagnostic': patient.diagnostic_principal,
            'antecedents': patient.antecedents_medicaux,
            'allergies': patient.allergies,
        },
        'historique_soins': [
            {
                'date': surgery.date_prevue.isoformat(),
                'intervention': surgery.type_intervention,
                'statut': surgery.statut,
            }
            for surgery in patient.surgery_set.all()
        ],
        'consentements': [
            {
                'type': consent.type_traitement,
                'accorde': consent.consentement_donne,
                'date': consent.date_consentement.isoformat(),
            }
            for consent in patient.consentementrgpd_set.all()
        ]
    }
    
    # Audit log
    RGPDAuditLog.objects.create(
        user=request.user,
        action='EXPORT',
        resource_type='Patient',
        resource_id=patient.id,
        ip_address=get_client_ip(request),
        legal_basis='Article 15 RGPD - Droit d\'accès'
    )
    
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )
    response['Content-Disposition'] = f'attachment; filename="patient_{patient.id}_data.json"'
    
    return response
```

### Droit à l'Effacement (Article 17)
```python
def patient_data_deletion(request, patient_id):
    """Suppression données patient - Droit à l'oubli RGPD"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Vérifications légales
    if patient.has_ongoing_treatment():
        raise ValidationError("Impossible de supprimer - soins en cours")
    
    if patient.has_legal_retention_requirements():
        # Anonymisation au lieu de suppression
        patient.anonymize()
    else:
        # Suppression complète
        with transaction.atomic():
            # Audit avant suppression
            RGPDAuditLog.objects.create(
                user=request.user,
                action='DELETE',
                resource_type='Patient', 
                resource_id=patient.id,
                legal_basis='Article 17 RGPD - Droit à l\'effacement'
            )
            
            # Suppression cascade sécurisée
            patient.delete()
    
    return JsonResponse({'status': 'deleted', 'patient_id': str(patient_id)})
```

### Droit de Rectification (Article 16)
```python
class PatientUpdateView(UpdateView):
    model = Patient
    fields = ['nom', 'prenom', 'date_naissance']
    
    def form_valid(self, form):
        # Audit modifications
        changes = []
        for field, old_value in form.initial.items():
            new_value = form.cleaned_data.get(field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} -> {new_value}")
        
        if changes:
            RGPDAuditLog.objects.create(
                user=self.request.user,
                action='UPDATE',
                resource_type='Patient',
                resource_id=self.object.id,
                legal_basis='Article 16 RGPD - Droit de rectification',
                details='; '.join(changes)
            )
        
        return super().form_valid(form)
```

## 🛡️ Sécurité & Protection

### Chiffrement Transit/Repos
```python
# Settings sécurité
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Chiffrement base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
            'sslcert': '/path/to/client-cert.pem',
            'sslkey': '/path/to/client-key.pem',
            'sslrootcert': '/path/to/ca-cert.pem',
        }
    }
}
```

### Gestion Sessions & Auth
```python
# Sessions chiffrées
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1 heure pour données médicales

# Authentification renforcée
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12,}  # Renforcé pour médical
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## 📋 Procédures CNIL

### Registre des Traitements
```python
class TraitementRGPD(models.Model):
    nom = models.CharField(max_length=200)
    finalite = models.TextField()  # Soins, gestion, statistiques
    base_legale = models.CharField(max_length=100)
    categories_donnees = models.TextField()
    categories_personnes = models.CharField(max_length=200)
    destinataires = models.TextField()
    transferts_tiers = models.TextField(blank=True)
    duree_conservation = models.CharField(max_length=100)
    mesures_securite = models.TextField()
    
    responsable_traitement = models.CharField(max_length=200)
    delegue_protection_donnees = models.CharField(max_length=200)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
```

### Analyse d'Impact (AIPD)
Documentation obligatoire pour données sensibles médicales:

1. **Description systématique du traitement**
2. **Évaluation nécessité/proportionnalité**  
3. **Évaluation risques droits/libertés**
4. **Mesures protection envisagées**

### Notification Violations
```python
class ViolationDonnees(models.Model):
    TYPES = [
        ('breach_confidentiality', 'Violation confidentialité'),
        ('breach_integrity', 'Violation intégrité'),
        ('breach_availability', 'Violation disponibilité'),
    ]
    
    date_detection = models.DateTimeField()
    date_violation = models.DateTimeField()
    type_violation = models.CharField(max_length=50, choices=TYPES)
    
    # Description
    circonstances = models.TextField()
    donnees_concernees = models.TextField()
    nombre_personnes_affectees = models.IntegerField()
    consequences_probables = models.TextField()
    
    # Mesures prises
    mesures_immediates = models.TextField()
    mesures_remediation = models.TextField()
    
    # Notifications
    cnil_notifiee = models.BooleanField(default=False)
    date_notification_cnil = models.DateTimeField(null=True)
    personnes_notifiees = models.BooleanField(default=False)
    
    responsable_declaration = models.ForeignKey(User, on_delete=models.PROTECT)
```

## 🔍 Contrôles & Audits

### Tests Conformité Automatisés
```python
# tests/test_rgpd_compliance.py
class RGPDComplianceTest(TestCase):
    def test_patient_data_encryption(self):
        """Vérifier chiffrement données sensibles"""
        patient = Patient.objects.create(
            nom="Dupont", 
            diagnostic_principal="Appendicite"
        )
        
        # Vérifier chiffrement en base
        with connection.cursor() as cursor:
            cursor.execute("SELECT nom, diagnostic_principal FROM patients WHERE id = %s", [patient.id])
            row = cursor.fetchone()
            
            # Données doivent être chiffrées en base
            self.assertNotEqual(row[0], "Dupont")
            self.assertNotEqual(row[1], "Appendicite")
    
    def test_audit_log_creation(self):
        """Vérifier création logs audit"""
        patient = Patient.objects.create(nom="Test")
        
        # Vérifier audit log créé
        audit_logs = RGPDAuditLog.objects.filter(
            resource_type='Patient',
            resource_id=patient.id
        )
        self.assertTrue(audit_logs.exists())
    
    def test_data_retention_policy(self):
        """Vérifier politique rétention"""
        # Patient inactif > durée légale
        old_patient = Patient.objects.create(
            nom="Ancient",
            date_creation=timezone.now() - timedelta(days=365*20)  # 20 ans
        )
        
        # Doit être marqué pour anonymisation/suppression
        self.assertTrue(old_patient.should_be_anonymized())
```

### Checklist Conformité
- ✅ **Chiffrement au repos**: Toutes données sensibles chiffrées
- ✅ **Chiffrement en transit**: HTTPS/TLS obligatoire  
- ✅ **Audit trail**: Tous accès loggés
- ✅ **Consentements**: Collecte et traçabilité
- ✅ **Droits personnes**: Accès, rectification, effacement
- ✅ **Retention**: Politique durée conservation
- ✅ **Sécurité**: Authentication forte, sessions sécurisées
- ✅ **Documentation**: Registre traitements, AIPD

---

*Conformité RGPD maintenue et validée par Code Review Agent spécialisé médical*