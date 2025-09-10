"""
Integration Tests for Business Workflows
Tests complete enterprise SaaS workflows with GDPR compliance
"""

import pytest
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from backend.tests.conftest import (
    enterprise_user,
    business_workflow_context,
    sample_client_data,
    business_process_data,
    gdpr_compliant_settings
)


@pytest.mark.integration
class TestBusinessWorkflowIntegration(TransactionTestCase):
    """Integration tests for complete business workflows"""
    
    def setUp(self):
        """Set up test environment with enterprise business context"""
        self.user = User.objects.create_user(
            username='manager.martin',
            email='manager.martin@enterprise-test.com',
            password='test123'
        )
    
    @patch('apps.analytics.models.AnalyticsRecord.objects.create')
    def test_client_registration_workflow(self, mock_analytics, enterprise_user, sample_client_data):
        """Test complete client registration with analytics tracking"""
        from apps.core.models import BaseModel
        
        # Simulate client registration
        client_data = sample_client_data
        
        # Verify business client context
        assert client_data['name'] is not None, "Client name required"
        assert client_data['email'] is not None, "Client email required"
        assert client_data['company'] is not None, "Client company required"
        
        # Verify GDPR compliance fields
        gdpr_required_fields = ['name', 'email', 'company', 'phone']
        for field in gdpr_required_fields:
            assert field in client_data, f"GDPR required field {field} missing"
        
        # Verify analytics tracking called
        mock_analytics.assert_called()
        
    def test_business_process_scheduling_workflow(self, enterprise_user, business_process_data):
        """Test business process scheduling with enterprise terminology"""
        process_data = business_process_data
        
        # Verify business process terminology
        business_processes = ['Project Planning', 'Client Onboarding', 'Product Launch', 'Strategic Review']
        assert process_data['process_type'] in business_processes, \
            f"Process {process_data['process_type']} not in business terminology"
        
        # Verify required business process fields
        required_fields = [
            'process_type', 'scheduled_date', 'estimated_duration', 
            'assigned_manager', 'priority_level', 'department'
        ]
        for field in required_fields:
            assert field in process_data, f"Required business field {field} missing"
        
        # Verify business priority levels
        priority_levels = ['High', 'Medium', 'Low']
        assert process_data['priority_level'] in priority_levels, \
            "Priority level must use standard business terminology"
    
    @gdpr_compliant_settings
    def test_gdpr_audit_trail_workflow(self, enterprise_user):
        """Test GDPR audit trail for business data access"""
        from django.conf import settings
        
        # Verify GDPR settings are active
        assert settings.AUDITLOG_INCLUDE_ALL_MODELS, "Audit logging must be enabled for GDPR"
        assert settings.LANGUAGE_CODE == 'fr-fr', "Primary language configured"
        assert settings.TIME_ZONE == 'Europe/Paris', "Timezone must be European"
        
        # Test encrypted field configuration
        assert hasattr(settings, 'FIELD_ENCRYPTION_KEY'), "Encryption key required for GDPR"
        
        # Verify internationalization
        assert settings.USE_I18N, "Internationalization required for multilingual support"
        assert settings.USE_L10N, "Localization required for regional formats"
        
    def test_multilingual_translation_workflow(self, business_translator_simulator):
        """Test trilingual business translation workflow"""
        
        # Test French -> German -> English translation chain
        business_terms = ['client', 'process', 'manager', 'enterprise']
        
        for business_term in business_terms:
            # French to German
            german_translation = business_translator_simulator.translate_term(
                business_term, 'fr', 'de'
            )
            
            # French to English  
            english_translation = business_translator_simulator.translate_term(
                business_term, 'fr', 'en'
            )
            
            # Verify translations exist and differ from source (except 'client')
            if business_term != 'client':
                assert german_translation != business_term, \
                    f"German translation missing for {business_term}"
                assert english_translation != business_term, \
                    f"English translation missing for {business_term}"
            
            # Verify business context preserved
            business_keywords = ['client', 'process', 'manager', 'enterprise', 'unternehmen', 'geschäft']
            combined_translations = f"{german_translation} {english_translation}".lower()
            
            has_business_context = any(keyword in combined_translations for keyword in business_keywords)
            assert has_business_context, \
                f"Business context lost in translations for {business_term}"


@pytest.mark.integration  
class TestAgentCodeGenerationIntegration:
    """Integration tests for agent-generated code in business context"""
    
    def test_backend_frontend_code_consistency(self, backend_agent_simulator, frontend_agent_simulator):
        """Test consistency between backend and frontend generated code"""
        
        # Generate backend model
        model_spec = {
            'name': 'Client',
            'fields': 'name = EncryptedTextField(max_length=100)\n    company = EncryptedTextField()'
        }
        backend_code = backend_agent_simulator.generate_model(model_spec)
        
        # Generate corresponding frontend component
        component_spec = {
            'name': 'ClientForm',
            'businessData': True
        }
        frontend_code = frontend_agent_simulator.generate_component(component_spec)
        
        # Verify naming consistency
        assert 'Client' in backend_code, "Model name must be in backend code"
        assert 'Client' in frontend_code, "Model name must be referenced in frontend"
        
        # Verify business context in both
        business_patterns = ['name', 'company', 'client']
        backend_business = any(pattern in backend_code.lower() for pattern in business_patterns)
        frontend_business = any(pattern in frontend_code.lower() for pattern in business_patterns)
        
        assert backend_business, "Backend code missing business context"
        assert frontend_business, "Frontend code missing business context"
        
        # Verify GDPR compliance patterns
        assert 'EncryptedTextField' in backend_code, "Backend missing encryption"
        assert 'businessData' in frontend_code, "Frontend missing business data handling"
    
    def test_generated_code_quality_metrics(self, backend_agent_simulator):
        """Test quality metrics for agent-generated code"""
        
        model_specs = [
            {'name': 'Client', 'fields': 'name = EncryptedTextField()'},
            {'name': 'BusinessProcess', 'fields': 'process_type = EncryptedTextField()'},
            {'name': 'BusinessRecord', 'fields': 'description = EncryptedTextField()'}
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