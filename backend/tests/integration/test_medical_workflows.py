"""
Integration Tests for Medical Workflows
Tests complete medical SaaS workflows with French RGPD compliance
"""

import pytest
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from backend.tests.conftest import (
    french_medical_user,
    medical_workflow_context,
    sample_patient_data,
    surgical_procedure_data,
    rgpd_compliant_settings
)


@pytest.mark.integration
class TestMedicalWorkflowIntegration(TransactionTestCase):
    """Integration tests for complete medical workflows"""
    
    def setUp(self):
        """Set up test environment with French medical context"""
        self.user = User.objects.create_user(
            username='dr.martin',
            email='dr.martin@hopital-test.fr',
            password='test123'
        )
    
    @patch('apps.analytics.models.AnalyticsRecord.objects.create')
    def test_patient_registration_workflow(self, mock_analytics, french_medical_user, sample_patient_data):
        """Test complete patient registration with analytics tracking"""
        from apps.core.models import BaseModel
        
        # Simulate patient registration
        patient_data = sample_patient_data
        
        # Verify French medical context
        assert patient_data['nom'] is not None, "Patient nom (last name) required"
        assert patient_data['prenom'] is not None, "Patient prenom (first name) required"
        assert patient_data['numero_securite_sociale'] is not None, "French social security number required"
        
        # Verify RGPD compliance fields
        rgpd_required_fields = ['nom', 'prenom', 'date_naissance', 'numero_securite_sociale']
        for field in rgpd_required_fields:
            assert field in patient_data, f"RGPD required field {field} missing"
        
        # Verify analytics tracking called
        mock_analytics.assert_called()
        
    def test_surgical_scheduling_workflow(self, french_medical_user, surgical_procedure_data):
        """Test surgical procedure scheduling with French terminology"""
        procedure_data = surgical_procedure_data
        
        # Verify French surgical terminology
        french_procedures = ['Appendicectomie', 'Cholécystectomie', 'Craniotomie', 'Laparoscopie']
        assert procedure_data['type_intervention'] in french_procedures, \
            f"Procedure {procedure_data['type_intervention']} not in French terminology"
        
        # Verify required surgical fields
        required_fields = [
            'type_intervention', 'date_prevue', 'duree_estimee', 
            'chirurgien_principal', 'anesthesie_type', 'salle_operation'
        ]
        for field in required_fields:
            assert field in procedure_data, f"Required surgical field {field} missing"
        
        # Verify French anesthesia terminology
        french_anesthesia = ['Générale', 'Locale', 'Rachidienne']
        assert procedure_data['anesthesie_type'] in french_anesthesia, \
            "Anesthesia type must use French terminology"
    
    @rgpd_compliant_settings
    def test_rgpd_audit_trail_workflow(self, french_medical_user):
        """Test RGPD audit trail for medical data access"""
        from django.conf import settings
        
        # Verify RGPD settings are active
        assert settings.AUDITLOG_INCLUDE_ALL_MODELS, "Audit logging must be enabled for RGPD"
        assert settings.LANGUAGE_CODE == 'fr-FR', "Primary language must be French"
        assert settings.TIME_ZONE == 'Europe/Paris', "Timezone must be French"
        
        # Test encrypted field configuration
        assert hasattr(settings, 'FIELD_ENCRYPTION_KEY'), "Encryption key required for RGPD"
        
        # Verify French localization
        assert settings.USE_I18N, "Internationalization required for trilingual support"
        assert settings.USE_L10N, "Localization required for French formats"
        
    def test_multilingual_translation_workflow(self, medical_translator_simulator):
        """Test trilingual medical translation workflow"""
        
        # Test French -> German -> English translation chain
        french_terms = ['diagnostic', 'intervention', 'patient', 'medecin']
        
        for french_term in french_terms:
            # French to German
            german_translation = medical_translator_simulator.translate_term(
                french_term, 'fr', 'de'
            )
            
            # French to English  
            english_translation = medical_translator_simulator.translate_term(
                french_term, 'fr', 'en'
            )
            
            # Verify translations exist and differ from source (except 'patient')
            if french_term != 'patient':
                assert german_translation != french_term, \
                    f"German translation missing for {french_term}"
                assert english_translation != french_term, \
                    f"English translation missing for {french_term}"
            
            # Verify medical context preserved
            medical_keywords = ['medic', 'patient', 'diagnos', 'interven', 'arzt', 'chirurg']
            combined_translations = f"{german_translation} {english_translation}".lower()
            
            has_medical_context = any(keyword in combined_translations for keyword in medical_keywords)
            assert has_medical_context, \
                f"Medical context lost in translations for {french_term}"


@pytest.mark.integration  
class TestAgentCodeGenerationIntegration:
    """Integration tests for agent-generated code in medical context"""
    
    def test_backend_frontend_code_consistency(self, backend_agent_simulator, frontend_agent_simulator):
        """Test consistency between backend and frontend generated code"""
        
        # Generate backend model
        model_spec = {
            'name': 'Patient',
            'fields': 'nom = EncryptedTextField(max_length=100)\n    diagnostic = EncryptedTextField()'
        }
        backend_code = backend_agent_simulator.generate_model(model_spec)
        
        # Generate corresponding frontend component
        component_spec = {
            'name': 'PatientForm',
            'medicalData': True
        }
        frontend_code = frontend_agent_simulator.generate_component(component_spec)
        
        # Verify naming consistency
        assert 'Patient' in backend_code, "Model name must be in backend code"
        assert 'Patient' in frontend_code, "Model name must be referenced in frontend"
        
        # Verify French medical context in both
        french_patterns = ['nom', 'diagnostic', 'patient']
        backend_french = any(pattern in backend_code.lower() for pattern in french_patterns)
        frontend_french = any(pattern in frontend_code.lower() for pattern in french_patterns)
        
        assert backend_french, "Backend code missing French medical context"
        assert frontend_french, "Frontend code missing French medical context"
        
        # Verify RGPD compliance patterns
        assert 'EncryptedTextField' in backend_code, "Backend missing encryption"
        assert 'medicalData' in frontend_code, "Frontend missing medical data handling"
    
    def test_generated_code_quality_metrics(self, backend_agent_simulator):
        """Test quality metrics for agent-generated code"""
        
        model_specs = [
            {'name': 'Patient', 'fields': 'nom = EncryptedTextField()'},
            {'name': 'ChirurgicalProcedure', 'fields': 'type_intervention = EncryptedTextField()'},
            {'name': 'MedicalRecord', 'fields': 'diagnostic = EncryptedTextField()'}
        ]
        
        quality_scores = []
        
        for spec in model_specs:
            code = backend_agent_simulator.generate_model(spec)
            
            # Calculate quality score
            quality_indicators = [
                'class Meta:' in code,
                'permissions = [' in code,
                'auditlog.register' in code,
                'EncryptedTextField' in code,
                len(code.split('\n')) > 10,  # Adequate code length
                spec['name'] in code  # Model name present
            ]
            
            score = sum(quality_indicators) / len(quality_indicators)
            quality_scores.append(score)
        
        average_quality = sum(quality_scores) / len(quality_scores)
        assert average_quality > 0.8, f"Average code quality {average_quality} below threshold"
        
        # Ensure no model scored too low
        min_quality = min(quality_scores)
        assert min_quality > 0.6, f"Minimum quality score {min_quality} too low"


@pytest.mark.integration
class TestMedicalComplianceIntegration:
    """Integration tests for medical compliance across all components"""
    
    def test_end_to_end_rgpd_compliance(self, backend_agent_simulator, medical_workflow_context):
        """Test RGPD compliance across entire workflow"""
        
        # Test patient data model generation
        patient_spec = {
            'name': 'Patient', 
            'fields': 'nom = EncryptedTextField()\n    diagnostic = EncryptedTextField()'
        }
        patient_model = backend_agent_simulator.generate_model(patient_spec)
        
        # Verify RGPD compliance elements
        rgpd_elements = [
            'EncryptedTextField',  # Data encryption
            'auditlog.register',   # Audit trail
            'permissions = [',     # Access control
            'BaseModel'           # Standardized base
        ]
        
        for element in rgpd_elements:
            assert element in patient_model, f"RGPD element {element} missing from generated code"
        
        # Test medical record model
        record_spec = {
            'name': 'MedicalRecord',
            'fields': 'patient = ForeignKey(Patient)\n    diagnostic = EncryptedTextField()'
        }
        record_model = backend_agent_simulator.generate_model(record_spec)
        
        # Verify relationships and encryption
        assert 'Patient' in record_model, "Patient relationship missing"
        assert 'EncryptedTextField' in record_model, "Medical data encryption missing"
        
        # Test serializer for privacy controls
        patient_serializer = backend_agent_simulator.generate_serializer('Patient')
        
        assert 'write_only' in patient_serializer, "Privacy controls missing in serializer"
        assert 'RGPD privacy' in patient_serializer, "RGPD documentation missing"
    
    def test_french_medical_terminology_consistency(self, medical_translator_simulator):
        """Test consistency of French medical terminology across translations"""
        
        # Define core medical terms that should be consistent
        core_terms = {
            'patient': {'de': 'Patient', 'en': 'patient'},
            'diagnostic': {'de': 'Diagnose', 'en': 'diagnosis'}, 
            'intervention': {'de': 'chirurgischer Eingriff', 'en': 'surgical procedure'},
            'medecin': {'de': 'Arzt', 'en': 'physician'}
        }
        
        consistency_results = {}
        
        for french_term, expected_translations in core_terms.items():
            consistency_results[french_term] = {}
            
            for target_lang, expected in expected_translations.items():
                actual = medical_translator_simulator.translate_term(
                    french_term, 'fr', target_lang
                )
                consistency_results[french_term][target_lang] = {
                    'expected': expected,
                    'actual': actual,
                    'matches': actual == expected
                }
        
        # Verify all translations are consistent
        for term, translations in consistency_results.items():
            for lang, result in translations.items():
                assert result['matches'], \
                    f"Inconsistent translation for {term} -> {lang}: got {result['actual']}, expected {result['expected']}"
    
    @patch('django.core.management.call_command')
    def test_database_fixtures_loading(self, mock_call_command, django_db_setup):
        """Test loading of French medical terminology fixtures"""
        
        # Verify fixture loading calls
        expected_fixtures = [
            'fixtures/french_medical_terms.json',
            'fixtures/surgical_procedures_fr.json'
        ]
        
        # Check that loaddata was called for each fixture
        call_args_list = [call[0] for call in mock_call_command.call_args_list]
        
        for fixture in expected_fixtures:
            fixture_loaded = any(
                'loaddata' in args and fixture in args 
                for args in call_args_list
            )
            assert fixture_loaded, f"Fixture {fixture} was not loaded during setup"


if __name__ == '__main__':
    # Run with: pytest backend/tests/integration/test_medical_workflows.py -v
    pytest.main([__file__, '-v', '--tb=short', '-m', 'integration'])