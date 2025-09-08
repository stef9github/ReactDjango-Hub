# Tests des Agents Claude Code

> **Framework de validation pour génération de code agents spécialisés SaaS médical**

## 🧪 Vue d'Ensemble Testing

### Objectifs Validation Agents
- **Qualité Code**: Génération respectant standards Django/React
- **Contexte Médical**: Préservation terminologie française chirurgicale
- **Conformité RGPD**: Validation chiffrement et audit automatiques
- **Performance**: Benchmarks temps génération et qualité output

### Agents Testés
- **Backend + API Agent**: Models Django, sérialiseurs DRF, endpoints Ninja
- **Frontend Agent**: Composants React trilingues, interfaces médicales
- **Medical Translator Agent**: Traduction terminologie FR→DE→EN
- **Code Review Agent**: Validation sécurité et conformité

## 🏗️ Architecture Tests

### Structure Testing
```
backend/tests/
├── agent_tests/              # Tests agents spécialisés
│   ├── test_agent_framework.py     # Framework validation
│   ├── test_backend_agent.py       # Backend + API agent
│   ├── test_frontend_agent.py      # Frontend agent
│   └── test_medical_translator.py  # Traduction médicale
├── integration/              # Tests workflows multi-agents
│   ├── test_medical_workflows.py   # Workflows médicaux complets
│   └── test_rgpd_compliance.py     # Conformité intégrée
└── performance/              # Benchmarks agents
    └── test_agent_performance.py   # Temps génération, qualité
```

### Framework Validation
```python
# backend/tests/agent_tests/test_agent_framework.py
class ClaudeCodeAgentTester:
    """Classe principale validation agents Claude Code"""
    
    def validate_code_generation(self, agent, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Valide code généré par agent"""
        generated_code = agent.generate_code(spec)
        
        return {
            'code': generated_code,
            'rgpd_compliant': self._check_rgpd_compliance(generated_code),
            'french_medical_context': self._check_french_context(generated_code),
            'quality_score': self._calculate_quality_score(generated_code),
            'security_score': self._check_security_patterns(generated_code)
        }
    
    def _check_rgpd_compliance(self, code: str) -> bool:
        """Vérifier conformité RGPD code généré"""
        rgpd_patterns = [
            'EncryptedTextField',           # Chiffrement données
            'auditlog.register',            # Audit trail
            'permissions = [',              # Contrôle accès
            'RGPD',                        # Documentation
            'Guardian',                     # Object-level permissions
        ]
        
        compliance_score = sum(1 for pattern in rgpd_patterns if pattern in code)
        return compliance_score >= len(rgpd_patterns) * 0.6  # 60% minimum
    
    def _check_french_context(self, code: str) -> bool:
        """Vérifier préservation contexte médical français"""
        french_medical_terms = [
            'diagnostic', 'intervention', 'patient', 'medecin',
            'chirurgien', 'anesthesie', 'bloc', 'salle'
        ]
        
        french_patterns = [
            "LANGUAGE_CODE = 'fr-fr'",
            "'fr':",
            "French",
            "français",
            "médical"
        ]
        
        has_terms = any(term in code.lower() for term in french_medical_terms)
        has_patterns = any(pattern in code for pattern in french_patterns)
        
        return has_terms or has_patterns
```

## 🔧 Tests Backend + API Agent

### Validation Models Django
```python
class TestBackendAgent:
    """Tests génération code backend par agent"""
    
    def test_model_generation_with_rgpd(self):
        """Test génération modèle Django avec conformité RGPD"""
        tester = ClaudeCodeAgentTester()
        
        model_spec = {
            'name': 'Patient',
            'fields': {
                'nom': 'EncryptedTextField(max_length=100)',
                'diagnostic': 'EncryptedTextField()',
                'date_naissance': 'EncryptedDateField()'
            },
            'medical_context': True,
            'rgpd_compliant': True
        }
        
        result = tester.validate_code_generation(backend_agent, model_spec)
        
        # Validations
        assert result['rgpd_compliant'], "Modèle doit être RGPD compliant"
        assert result['french_medical_context'], "Contexte médical français requis"
        assert result['quality_score'] > 0.8, f"Score qualité {result['quality_score']} insuffisant"
        
        # Vérifications spécifiques
        code = result['code']
        assert 'class Patient(BaseModel):' in code
        assert 'EncryptedTextField' in code
        assert 'auditlog.register(Patient)' in code
        
    def test_serializer_generation_privacy(self):
        """Test génération sérialiseur avec contrôles confidentialité"""
        serializer_spec = {
            'model': 'Patient',
            'fields': ['nom', 'diagnostic', 'date_naissance'],
            'privacy_controls': True
        }
        
        result = tester.validate_code_generation(backend_agent, serializer_spec)
        code = result['code']
        
        # Contrôles confidentialité
        assert 'write_only=True' in code, "Champs sensibles write_only"
        assert 'SerializerMethodField' in code, "Méthodes protection données"
        assert 'has_perm' in code, "Vérification permissions"
        
    def test_api_endpoint_generation(self):
        """Test génération endpoints API avec documentation"""
        endpoint_spec = {
            'model': 'Patient',
            'operations': ['list', 'create', 'retrieve', 'update'],
            'framework': 'ninja',  # ou 'drf'
            'documentation': True
        }
        
        result = tester.validate_code_generation(backend_agent, endpoint_spec)
        code = result['code']
        
        # API Ninja
        if endpoint_spec['framework'] == 'ninja':
            assert '@api.post' in code, "Endpoint POST"
            assert '@api.get' in code, "Endpoint GET"
            assert 'response=' in code, "Schéma response"
            assert 'tags=["Patients"]' in code, "Documentation tags"
        
        # Sécurité API
        assert 'auth=' in code, "Authentication requise"
        assert 'permissions' in code, "Contrôle permissions"
```

## 🎨 Tests Frontend Agent

### Validation Composants React
```python
class TestFrontendAgent:
    """Tests génération composants React trilingues"""
    
    def test_component_trilingual_support(self):
        """Test génération composant avec support trilingue"""
        component_spec = {
            'name': 'PatientForm',
            'type': 'form',
            'medical_data': True,
            'languages': ['fr', 'de', 'en'],
            'primary_language': 'fr'
        }
        
        result = tester.validate_code_generation(frontend_agent, component_spec)
        code = result['code']
        
        # Support trilingue
        assert "'fr':" in code, "Support français"
        assert "'de':" in code, "Support allemand"  
        assert "'en':" in code, "Support anglais"
        
        # Français primaire
        fr_index = code.find("'fr':")
        en_index = code.find("'en':")
        de_index = code.find("'de':")
        
        assert fr_index < en_index, "Français doit être premier"
        assert fr_index < de_index, "Français doit être premier"
        
        # Attributs test
        assert 'data-testid' in code, "Attributs test requis"
        assert 'PatientForm' in code, "Nom composant correct"
        
    def test_medical_terminology_component(self):
        """Test composant avec terminologie médicale française"""
        component_spec = {
            'name': 'DiagnosticDisplay', 
            'medical_domain': 'surgery',
            'terminology': 'french_primary'
        }
        
        result = tester.validate_code_generation(frontend_agent, component_spec)
        code = result['code']
        
        # Terminologie médicale française
        medical_terms = ['diagnostic', 'intervention', 'chirurgien', 'anesthésie']
        found_terms = [term for term in medical_terms if term in code.lower()]
        
        assert len(found_terms) >= 2, f"Terminologie médicale insuffisante: {found_terms}"
        
        # Interface médicale
        assert 'medical-' in code, "Classes CSS médicales"
        assert 'form' in code or 'button' in code, "Éléments interactifs"
```

## 🌐 Tests Medical Translator Agent

### Validation Traduction Contextuelle
```python
class TestMedicalTranslatorAgent:
    """Tests traduction terminologie médicale spécialisée"""
    
    def test_surgical_terminology_accuracy(self):
        """Test précision traduction terminologie chirurgicale"""
        test_cases = [
            # (terme_fr, langue_cible, traduction_attendue)
            ('intervention chirurgicale', 'de', 'chirurgischer Eingriff'),
            ('anesthésie générale', 'de', 'Vollnarkose'),
            ('diagnostic préopératoire', 'en', 'preoperative diagnosis'),
            ('bloc opératoire', 'en', 'operating room'),
            ('salle de réveil', 'de', 'Aufwachraum'),
        ]
        
        for terme_fr, langue_cible, traduction_attendue in test_cases:
            result = medical_translator.translate_term(
                terme_fr, 
                source='fr', 
                target=langue_cible,
                domain='surgery'
            )
            
            assert result.lower() == traduction_attendue.lower(), \
                f"Traduction incorrecte: {terme_fr} -> {result} != {traduction_attendue}"
    
    def test_medical_context_preservation(self):
        """Test préservation contexte médical lors traduction"""
        french_sentence = "Le patient présente une appendicite aiguë nécessitant une intervention en urgence."
        
        # Traduction allemand
        german_result = medical_translator.translate_text(
            french_sentence, 
            source='fr', 
            target='de',
            preserve_medical_context=True
        )
        
        # Vérifications contexte médical
        assert 'patient' in german_result.lower(), "Terme 'patient' préservé"
        assert 'appendizitis' in german_result.lower(), "Diagnostic médical traduit"
        
        # Traduction anglais  
        english_result = medical_translator.translate_text(
            french_sentence,
            source='fr', 
            target='en',
            preserve_medical_context=True
        )
        
        assert 'appendicitis' in english_result.lower(), "Terminologie médicale précise"
        assert 'emergency' in english_result.lower(), "Contexte urgence préservé"
```

## 📊 Tests Performance Agents

### Benchmarks Génération
```python
class TestAgentPerformance:
    """Tests performance et benchmarks agents"""
    
    def test_code_generation_speed(self):
        """Test vitesse génération code par agents"""
        benchmarks = {
            'backend_agent': {
                'model_generation': 10.0,      # secondes max
                'serializer_generation': 8.0,
                'api_endpoint_generation': 12.0
            },
            'frontend_agent': {
                'component_generation': 15.0,
                'form_generation': 12.0,
                'page_generation': 20.0
            }
        }
        
        for agent_type, operations in benchmarks.items():
            agent = get_agent(agent_type)
            
            for operation, max_time in operations.items():
                start_time = time.time()
                
                # Génération code test
                spec = get_test_spec(operation)
                result = agent.generate_code(spec)
                
                generation_time = time.time() - start_time
                
                assert generation_time < max_time, \
                    f"{agent_type}.{operation} trop lent: {generation_time}s > {max_time}s"
                assert result is not None, "Génération doit retourner code"
    
    def test_concurrent_agent_operations(self):
        """Test agents travaillant en parallèle"""
        import concurrent.futures
        
        def generate_backend_code():
            return backend_agent.generate_model({'name': 'TestModel'})
        
        def generate_frontend_code():
            return frontend_agent.generate_component({'name': 'TestComponent'})
        
        # Exécution parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            backend_future = executor.submit(generate_backend_code)
            frontend_future = executor.submit(generate_frontend_code)
            
            backend_result = backend_future.result(timeout=30)
            frontend_result = frontend_future.result(timeout=30)
        
        # Validations
        assert backend_result is not None, "Backend agent génération échouée"
        assert frontend_result is not None, "Frontend agent génération échouée"
        
        # Pas d'interférences entre agents
        assert 'TestModel' in backend_result, "Code backend cohérent"
        assert 'TestComponent' in frontend_result, "Code frontend cohérent"
```

## 🚀 Exécution Tests

### Commandes Testing
```bash
# Tests complets agents
make claude-test

# Tests spécifiques
pytest backend/tests/agent_tests/ -v
pytest backend/tests/agent_tests/test_backend_agent.py::TestBackendAgent::test_model_generation_with_rgpd -v

# Tests performance avec benchmarks
pytest backend/tests/performance/ -v --benchmark-only

# Tests intégration multi-agents  
pytest backend/tests/integration/test_medical_workflows.py -v
```

### Configuration CI/CD
```yaml
# .github/workflows/claude-optimized.yml
agent-testing:
  name: 🤖 Agent Code Generation Testing
  runs-on: ubuntu-latest
  steps:
    - name: 🧪 Test Backend + API Agent
      run: pytest backend/tests/agent_tests/test_backend_agent.py -v
      
    - name: 🎨 Test Frontend Agent  
      run: pytest backend/tests/agent_tests/test_frontend_agent.py -v
      
    - name: 🌐 Test Medical Translator
      run: pytest backend/tests/agent_tests/test_medical_translator.py -v
      
    - name: 📊 Performance Benchmarks
      run: pytest backend/tests/performance/ --benchmark-json=benchmarks.json
      
    - name: ⚖️ RGPD Compliance Validation
      run: pytest backend/tests/integration/test_rgpd_compliance.py -v
```

### Métriques Qualité
- **Couverture Tests**: 85%+ validation agents
- **Performance**: Génération < 15s par composant
- **Conformité RGPD**: 100% validation automatique
- **Contexte Médical**: Préservation terminologie française
- **Qualité Code**: Score > 0.8 pour tous agents

---

*Framework testing maintenu par Code Review Agent avec focus conformité médicale française*