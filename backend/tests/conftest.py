"""
Test configuration for Claude Code development
Pytest fixtures for medical SaaS testing with French context
"""

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from unittest.mock import Mock, patch
import factory
from faker import Faker
from faker_medical import Provider as MedicalProvider
from typing import Dict, Any, List

# Setup French locale for medical context
faker = Faker('fr_FR')
faker.add_provider(MedicalProvider)

# ============================================================================
# Claude Code Agent Testing Fixtures
# ============================================================================

@pytest.fixture
def claude_agent_context():
    """Base context for Claude Code agent testing"""
    return {
        'medical_context': 'french_hospital',
        'language': 'fr',
        'rgpd_compliance': True,
        'terminology': 'medical_french',
        'region': 'France'
    }

@pytest.fixture
def backend_agent_simulator():
    """Mock backend agent for Django code generation"""
    class BackendAgentMock:
        def __init__(self):
            self.agent_type = "backend"
            self.specialization = "django_medical"
        
        def generate_model(self, model_spec: Dict[str, Any]) -> str:
            """Simulate Django model generation"""
            return f'''
from django.db import models
from apps.core.models import BaseModel
from auditlog.registry import auditlog
from encrypted_model_fields.fields import EncryptedTextField

class {model_spec['name']}(BaseModel):
    {model_spec.get('fields', 'nom = EncryptedTextField(max_length=100)')}
    
    class Meta:
        permissions = [
            ("view_{model_spec['name'].lower()}", "Can view {model_spec['name'].lower()}"),
        ]

auditlog.register({model_spec['name']})
            '''
        
        def generate_serializer(self, model_name: str) -> str:
            """Simulate DRF serializer generation"""
            return f'''
from rest_framework import serializers
from .models import {model_name}

class {model_name}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {model_name}
        fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {{
            'diagnostic': {{'write_only': True}}  # RGPD privacy
        }}
            '''
    
    return BackendAgentMock()

@pytest.fixture  
def frontend_agent_simulator():
    """Mock frontend agent for React component generation"""
    class FrontendAgentMock:
        def __init__(self):
            self.agent_type = "frontend"
            self.specialization = "react_medical"
        
        def generate_component(self, component_spec: Dict[str, Any]) -> str:
            """Simulate React component generation"""
            return f'''
import React from 'react';

interface {component_spec['name']}Props {{
  language: 'fr' | 'en' | 'de';
  medicalData?: any;
}}

export const {component_spec['name']}: React.FC<{component_spec['name']}Props> = ({{ language, medicalData }}) => {{
  const translations = {{
    fr: {{ title: 'Données Médicales', save: 'Enregistrer' }},
    en: {{ title: 'Medical Data', save: 'Save' }},
    de: {{ title: 'Medizinische Daten', save: 'Speichern' }}
  }};

  return (
    <div data-testid="{component_spec['name'].lower()}" className="medical-component">
      <h1>{{translations[language].title}}</h1>
      <button>{{translations[language].save}}</button>
    </div>
  );
}};
            '''
    
    return FrontendAgentMock()

@pytest.fixture
def medical_translator_simulator():
    """Mock medical translator agent"""
    class MedicalTranslatorMock:
        def __init__(self):
            self.medical_terms = {
                'fr': {
                    'patient': 'patient',
                    'diagnostic': 'diagnostic', 
                    'intervention': 'intervention chirurgicale',
                    'medecin': 'médecin'
                },
                'en': {
                    'patient': 'patient',
                    'diagnostic': 'diagnosis',
                    'intervention': 'surgical procedure', 
                    'medecin': 'physician'
                },
                'de': {
                    'patient': 'Patient',
                    'diagnostic': 'Diagnose',
                    'intervention': 'chirurgischer Eingriff',
                    'medecin': 'Arzt'
                }
            }
        
        def translate_term(self, term: str, source: str, target: str) -> str:
            """Translate medical term between languages"""
            if source == 'fr' and term in self.medical_terms['fr']:
                idx = list(self.medical_terms['fr'].keys()).index(term)
                target_terms = list(self.medical_terms[target].values())
                return target_terms[idx] if idx < len(target_terms) else term
            return term
    
    return MedicalTranslatorMock()

# ============================================================================
# Medical Context Fixtures
# ============================================================================

@pytest.fixture
def french_medical_context():
    """French medical context for testing"""
    return {
        'language': 'fr-FR',
        'timezone': 'Europe/Paris',
        'medical_system': 'french_hospital',
        'rgpd_compliance': True,
        'cnil_guidelines': True,
        'medical_terminology': 'french',
        'surgical_procedures': [
            'Appendicectomie',
            'Cholécystectomie', 
            'Craniotomie',
            'Laparoscopie'
        ]
    }

@pytest.fixture
def sample_patient_data():
    """Sample French patient data for testing"""
    return {
        'nom': faker.last_name(),
        'prenom': faker.first_name(),
        'date_naissance': faker.date_of_birth(),
        'numero_securite_sociale': faker.ssn(),
        'adresse': faker.address(),
        'telephone': faker.phone_number(),
        'email': faker.email(),
        'medecin_traitant': f"Dr. {faker.name()}",
        'groupe_sanguin': faker.random_element(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
    }

@pytest.fixture
def surgical_procedure_data(french_medical_context):
    """Sample surgical procedure data"""
    return {
        'type_intervention': faker.random_element(french_medical_context['surgical_procedures']),
        'date_prevue': faker.future_datetime(),
        'duree_estimee': faker.random_int(min=30, max=300),  # minutes
        'chirurgien_principal': f"Dr. {faker.name()}",
        'anesthesie_type': faker.random_element(['Générale', 'Locale', 'Rachidienne']),
        'salle_operation': f"Bloc {faker.random_int(min=1, max=8)}",
        'materiel_special': faker.random_element(['Standard', 'Robotique', 'Microscope'])
    }

# ============================================================================
# Database and Authentication Fixtures  
# ============================================================================

@pytest.fixture
def french_medical_user():
    """Create a French medical professional user"""
    user = User.objects.create_user(
        username=f"dr.{faker.last_name().lower()}",
        email=faker.email(),
        password='test123',
        first_name=faker.first_name(),
        last_name=faker.last_name()
    )
    
    # Add French medical professional metadata
    user.profile = {
        'specialization': faker.random_element([
            'Chirurgie générale',
            'Cardiologie', 
            'Neurologie',
            'Orthopédie',
            'Gynécologie'
        ]),
        'hospital': faker.company(),
        'rpps_number': faker.random_number(digits=11),  # French medical ID
        'language_preference': 'fr'
    }
    
    return user

@pytest.fixture
def rgpd_compliant_settings():
    """Django settings for RGPD compliance testing"""
    return override_settings(
        # RGPD compliance settings
        DATA_UPLOAD_MAX_MEMORY_SIZE=2621440,  # 2.5 MB
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        
        # French localization
        LANGUAGE_CODE='fr-FR',
        TIME_ZONE='Europe/Paris',
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=True,
        
        # Medical data encryption
        FIELD_ENCRYPTION_KEY=b'test-key-for-testing-only-not-production',
        
        # Audit logging
        AUDITLOG_INCLUDE_ALL_MODELS=True,
    )

# ============================================================================
# Agent Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def agent_performance_benchmarks():
    """Performance benchmarks for Claude Code agents"""
    return {
        'backend_agent': {
            'model_generation_max_time': 10.0,  # seconds
            'serializer_generation_max_time': 5.0,
            'view_generation_max_time': 8.0
        },
        'frontend_agent': {
            'component_generation_max_time': 12.0,
            'form_generation_max_time': 8.0,
            'dashboard_generation_max_time': 15.0
        },
        'medical_translator': {
            'term_translation_max_time': 2.0,
            'form_translation_max_time': 5.0,
            'ui_translation_max_time': 7.0
        }
    }

@pytest.fixture
def mock_claude_api():
    """Mock Claude API responses for testing"""
    with patch('claude_api.generate_response') as mock:
        mock.return_value = {
            'status': 'success',
            'generated_code': 'class TestModel(BaseModel): pass',
            'confidence_score': 0.95,
            'medical_context_preserved': True,
            'rgpd_compliant': True
        }
        yield mock

# ============================================================================
# Integration Testing Fixtures
# ============================================================================

@pytest.fixture
def medical_workflow_context():
    """Complete medical workflow context for integration testing"""
    return {
        'patient_registration': True,
        'surgical_scheduling': True, 
        'medical_records': True,
        'analytics_tracking': True,
        'rgpd_audit_trail': True,
        'multilingual_support': ['fr', 'en', 'de'],
        'medical_devices_integration': False,  # Future feature
        'telemedicine_support': False  # Future feature
    }

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database with French medical data"""
    with django_db_blocker.unblock():
        # Load French medical terminology fixtures
        from django.core.management import call_command
        call_command('loaddata', 'fixtures/french_medical_terms.json', verbosity=0)
        call_command('loaddata', 'fixtures/surgical_procedures_fr.json', verbosity=0)

# ============================================================================
# Factory Classes for Test Data Generation
# ============================================================================

class PatientFactory(factory.django.DjangoModelFactory):
    """Factory for creating test patients with French context"""
    
    class Meta:
        model = 'clinical.Patient'  # Replace with your actual model
        
    nom = factory.Faker('last_name', locale='fr_FR')
    prenom = factory.Faker('first_name', locale='fr_FR')
    date_naissance = factory.Faker('date_of_birth')
    email = factory.Faker('email', locale='fr_FR')
    telephone = factory.Faker('phone_number', locale='fr_FR')
    
    # Medical-specific fields
    numero_securite_sociale = factory.Faker('ssn', locale='fr_FR')
    groupe_sanguin = factory.Faker('random_element', elements=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])

class SurgicalProcedureFactory(factory.django.DjangoModelFactory):
    """Factory for surgical procedures with French medical context"""
    
    class Meta:
        model = 'clinical.SurgicalProcedure'  # Replace with your actual model
    
    patient = factory.SubFactory(PatientFactory)
    type_intervention = factory.Faker('random_element', elements=[
        'Appendicectomie',
        'Cholécystectomie', 
        'Craniotomie',
        'Arthroplastie',
        'Laparoscopie'
    ])
    date_prevue = factory.Faker('future_datetime')
    duree_estimee = factory.Faker('random_int', min=30, max=360)  # minutes
    chirurgien_principal = factory.Faker('name', locale='fr_FR')

# ============================================================================
# Test Utilities
# ============================================================================

def assert_rgpd_compliant_code(code: str) -> None:
    """Assert that generated code is RGPD compliant"""
    rgpd_patterns = [
        'EncryptedTextField',
        'EncryptedCharField', 
        'auditlog.register',
        'permissions = [',
        'BaseModel'
    ]
    
    found_patterns = [pattern for pattern in rgpd_patterns if pattern in code]
    assert len(found_patterns) >= 3, f"Code missing RGPD compliance patterns. Found: {found_patterns}"

def assert_french_medical_context(code: str) -> None:
    """Assert that French medical context is preserved"""
    french_patterns = [
        r'nom\s*=',
        r'prenom\s*=', 
        r'diagnostic\s*=',
        r'patient',
        r'medical|médical'
    ]
    
    import re
    found_patterns = [pattern for pattern in french_patterns 
                     if re.search(pattern, code, re.IGNORECASE)]
    
    assert len(found_patterns) >= 2, f"Code missing French medical context. Found: {found_patterns}"